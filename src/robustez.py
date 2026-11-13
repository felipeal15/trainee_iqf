"""
robustez.py — Análise de robustez da Aula 3 ("Antes de dizer que funciona"), plano da P20.

A estratégia está CONGELADA: nada aqui muda o padrão nem serve para escolher parâmetros.
Cada variação troca um parâmetro só durante a própria rodada (ver `parametros`) e volta ao
valor padrão em seguida.

    1. Tearsheets do QuantStats (carteira e blocos x Ibovespa)
    2. Excesso de retorno sobre o CDI, por ano
    3. Subperíodos
    4. Grades: janela dos fatores de preço x rebalanceamento de cada bloco
    5. Fatias ±10 p.p., uma de cada vez
    6. Piso de volume no agressivo (teste, não candidato)
    7. Anos de dado necessários para confiar no Sharpe

Uso (a partir da raiz do projeto):
    python src/robustez.py      # grava tabelas, gráficos, tearsheets e resumo.md em
                                # resultados/robustez/ (leva alguns minutos)
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from types import ModuleType

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

import estrategia
import fatores
from backtest import datas_rebalanceamento, rodar_backtest
from dados import PROCESSED, RAIZ, Dados, carregar_dados
from diagnostico import md, num, pct
from estrategia import (CUSTO_OPERACAO, PESO_AGRESSIVO, PESO_DEFENSIVO, ResultadoEstrategia,
                        escolher_agressivo, juntar_blocos, rodar_estrategia)
from graficos import _eixo_datas, _titulo, aplicar_estilo
from metricas import cagr, drawdown, resumo
from universo import universo_liquido, universo_por_piso

SAIDA = RAIZ / "resultados" / "robustez"
ARQ_IPCA = PROCESSED / "ipca_mensal.parquet"

CART, DEF, AGR = "Estratégia 65/35", "Bloco defensivo", "Bloco agressivo"
SUBPERIODOS = {"2011-14": ("2011", "2014"), "2015-16 (recessão)": ("2015", "2016"),
               "2017-19": ("2017", "2019"), "2020 (Covid)": ("2020", "2020"),
               "2021-22 (alta de juros)": ("2021", "2022"), "2023-26": ("2023", "2026")}

# Grades (P20). Janela em meses -> pregões (21 por mês)
JANELAS = {6: 126, 9: 189, 12: 252}
FREQ_NOME = {"M": "mensal", "Q": "trimestral", "S": "semestral"}
FATIAS = {"FATIA_QUALITY_LOWVOL": (0.20, 0.40), "FATIA_VALUE": (0.40, 0.60),
          "FATIA_SIZE_MOMENTUM": (0.20, 0.40)}
FATIA_NOME = {"FATIA_QUALITY_LOWVOL": "Quality + Low Vol (defensivo)",
              "FATIA_VALUE": "Value (defensivo)", "FATIA_SIZE_MOMENTUM": "Size + Momentum (agressivo)"}

# Piso de volume (P20): R$ 1 milhão/dia em reais de out/2026, deflacionado pelo IPCA
PISO_REAIS_HOJE_MIL = 1_000.0
SERIE_IPCA = 433  # SGS/BCB: IPCA, variação % no mês

Z_95 = 1.96  # anos de dado: t ≈ Sharpe x raiz(anos) >= 1,96


# ---------------------------------------------------------------------------
# Rodadas com um parâmetro trocado
# ---------------------------------------------------------------------------
@contextmanager
def parametros(*trocas: tuple[ModuleType, str, object]):
    """Troca constantes de módulo (ex.: (fatores, "JANELA_FATORES_PRECO", 126)) só dentro do
    bloco `with` e devolve os valores padrão na saída, mesmo se der erro."""
    originais = [(mod, nome, getattr(mod, nome)) for mod, nome, _ in trocas]
    try:
        for mod, nome, valor in trocas:
            setattr(mod, nome, valor)
        yield
    finally:
        for mod, nome, valor in originais:
            setattr(mod, nome, valor)


def metricas_carteira(res: ResultadoEstrategia, dados: Dados) -> dict[str, float]:
    r = pd.DataFrame({"c": res.carteira, "Ibovespa": dados.ibov.reindex(res.carteira.index)})
    m = resumo(r, dados.cdi, benchmark="Ibovespa")["c"]
    return {"Sharpe": m["Sharpe (CDI)"], "CAGR": m["CAGR"], "Max DD": m["Max drawdown"],
            "Vol": m["Volatilidade (anual)"]}


# ---------------------------------------------------------------------------
# 1. QuantStats
# ---------------------------------------------------------------------------
def tearsheets(series: pd.DataFrame, ibov: pd.Series, cdi: pd.Series) -> pd.DataFrame | None:
    """Um tearsheet HTML por série. O HTML do QuantStats só aceita rf fixo (com a série diária
    do CDI ele quebra), então rf = CDI médio do período, taxa anual composta. A tabela devolvida
    compara o Sharpe do QuantStats com o nosso (CDI diário)."""
    try:
        import quantstats as qs
    except ImportError:
        print("quantstats não instalado: tearsheets pulados (as métricas estão nas tabelas)")
        return None
    rf = (1 + cdi).prod() ** (252 / len(cdi)) - 1
    linhas = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for nome, r in series.items():
            arquivo = f"1_tearsheet_{nome.split()[-1].replace('/', '-').lower()}.html"
            qs.reports.html(r, benchmark=ibov, rf=rf, output=str(SAIDA / arquivo),
                            title=f"{nome} x Ibovespa (rf = CDI médio {rf:.2%} a.a.)")
            linhas[nome] = {"arquivo": arquivo, "Sharpe QuantStats (rf fixo)": num(qs.stats.sharpe(r, rf=rf)),
                            "Sharpe nosso (CDI diário)": num(resumo(
                                pd.DataFrame({"x": r, "Ibovespa": ibov}), cdi, "Ibovespa").at["Sharpe (CDI)", "x"])}
    tab = pd.DataFrame(linhas).T.rename_axis("série")
    tab.attrs["rf"] = rf
    return tab


# ---------------------------------------------------------------------------
# 2 e 3. CDI e subperíodos
# ---------------------------------------------------------------------------
def excesso_cdi(series: pd.DataFrame, cdi: pd.Series) -> pd.DataFrame:
    anual = (1 + series).groupby(series.index.year).prod() - 1
    cdi_anual = (1 + cdi).groupby(cdi.index.year).prod() - 1
    excesso = anual.sub(cdi_anual, axis=0)
    total = pd.Series({c: cagr(series[c]) - cagr(cdi) for c in series.columns}, name="CAGR − CDI (período todo)")
    vitorias = pd.Series({c: f"{(excesso[c] > 0).sum()} de {len(excesso)}" for c in series.columns},
                         name="anos acima do CDI")
    tab = excesso.map(pct).rename(index=str)
    return pd.concat([tab, total.map(lambda v: pct(v, 2)).to_frame().T, vitorias.to_frame().T]).rename_axis("ano")


def subperiodos(series: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for nome, (a, b) in SUBPERIODOS.items():
        trecho = series.loc[a:b]
        for c in series.columns:
            r = trecho[c]
            linhas.append({"subperíodo": nome, "série": c, "CAGR": pct(cagr(r)),
                           "Vol": pct(r.std() * np.sqrt(252)), "Max DD": pct(drawdown(r).min())})
    return pd.DataFrame(linhas).pivot(index="subperíodo", columns="série").reindex(SUBPERIODOS)


# ---------------------------------------------------------------------------
# 4 e 5. Grades e fatias
# ---------------------------------------------------------------------------
def grade(dados: Dados, nome_freq: str, freqs: list[str]) -> pd.DataFrame:
    """Sharpe, CAGR e max DD da carteira para cada janela x frequência de um bloco."""
    linhas = []
    for meses, pregoes in JANELAS.items():
        for f in freqs:
            print(f"   janela {meses} meses, {nome_freq} {FREQ_NOME[f]}")
            with parametros((fatores, "JANELA_FATORES_PRECO", pregoes), (estrategia, nome_freq, f)):
                m = metricas_carteira(rodar_estrategia(dados), dados)
                # Parâmetros efetivos da rodada: identificam a combinação (para tirar duplicatas)
                efetivos = {"freq. agressivo": FREQ_NOME[estrategia.FREQ_AGRESSIVO],
                            "freq. defensivo": FREQ_NOME[estrategia.FREQ_DEFENSIVO]}
            linhas.append({"janela (meses)": meses, "rebalanceamento": FREQ_NOME[f], **efetivos, **m})
    return pd.DataFrame(linhas)


def newey_west(y: pd.Series, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, int]:
    """Coeficientes da regressão y = X b (MQO) e o t de cada um com erro-padrão de Newey-West
    (pesos de Bartlett), que corrige autocorrelação e heterocedasticidade dos retornos diários.
    Defasagens pela regra usual, fixada antes de olhar o resultado: piso(4 (n/100)^(2/9))."""
    y, X = np.asarray(y, float), np.asarray(X, float)
    n = len(y)
    lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    Xu = X * (y - X @ b)[:, None]
    S = Xu.T @ Xu
    for lag in range(1, lags + 1):
        G = Xu[lag:].T @ Xu[:-lag]
        S += (1 - lag / (lags + 1)) * (G + G.T)
    inv = np.linalg.inv(X.T @ X)
    return b, b / np.sqrt(np.diag(inv @ S @ inv)), lags


def significancia(series: pd.DataFrame, ibov: pd.Series, cdi: pd.Series, anos: float,
                  m: pd.DataFrame) -> pd.DataFrame:
    """Intervalo de 95% do Sharpe, t do alpha (Newey-West) e t do excesso sobre o Ibovespa."""
    linhas = {}
    for c in series.columns:
        sr = m.at["Sharpe (CDI)", c]
        ep = np.sqrt((1 + sr ** 2 / 2) / anos)  # erro-padrão aproximado do Sharpe anual
        excesso = series[c] - cdi
        b, t, lags = newey_west(excesso, pd.DataFrame({"alpha": 1.0, "beta": ibov - cdi}))
        b2, t2, _ = newey_west(series[c] - ibov, pd.DataFrame({"const": np.ones(len(ibov))}))
        linhas[c] = {"Sharpe (CDI)": num(sr), "intervalo de 95% do Sharpe": f"{num(sr - Z_95 * ep)} a {num(sr + Z_95 * ep)}",
                     "alpha anual": pct(b[0] * 252, 2), "t do alpha (Newey-West)": num(t[0]),
                     "excesso médio sobre o Ibovespa (a.a.)": pct(b2[0] * 252, 2),
                     "t do excesso sobre o Ibovespa": num(t2[0]), "defasagens (NW)": f"{lags}"}
    return pd.DataFrame(linhas).T.rename_axis("série")


def sem_anos(series: pd.DataFrame, anos_fora: list[int], anos_total: float) -> pd.Series:
    """CAGR de cada série tirando os anos civis de `anos_fora` (que são anos completos)."""
    fica = series[~series.index.year.isin(anos_fora)]
    return (1 + fica).prod() ** (1 / (anos_total - len(anos_fora))) - 1


def grafico_grades(grades: dict[str, pd.DataFrame], padrao: dict[str, tuple[int, str]]) -> plt.Figure:
    fig, eixos = plt.subplots(1, len(grades), figsize=(11, 3.6))
    vmin = min(g["Sharpe"].min() for g in grades.values())
    vmax = max(g["Sharpe"].max() for g in grades.values())
    for ax, (titulo, g) in zip(eixos, grades.items()):
        tab = g.pivot(index="janela (meses)", columns="rebalanceamento", values="Sharpe")
        ax.imshow(tab.values, cmap="Blues", vmin=vmin - 0.05, vmax=vmax + 0.05, aspect="auto")
        for i, janela in enumerate(tab.index):
            for j, freq in enumerate(tab.columns):
                destaque = (janela, freq) == padrao[titulo]
                ax.text(j, i, num(tab.iat[i, j]) + ("\n(padrão)" if destaque else ""), ha="center", va="center",
                        fontweight="semibold" if destaque else "normal")
        ax.set_xticks(range(len(tab.columns)), tab.columns)
        ax.set_yticks(range(len(tab.index)), [f"{m} meses" for m in tab.index])
        ax.grid(False)
        ax.set_title(titulo, fontsize=10, loc="left")
    fig.suptitle("Sharpe (CDI) da carteira: janela dos fatores de preço × rebalanceamento",
                 x=0.01, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    return fig


def fatias(dados: Dados, base: dict[str, float]) -> pd.DataFrame:
    linhas = [{"fatia": "padrão", "valor": "—", **base}]
    for nome, valores in FATIAS.items():
        padrao = getattr(estrategia, nome)
        for v in valores:
            print(f"   {nome} = {v:.0%}")
            with parametros((estrategia, nome, v)):
                linhas.append({"fatia": FATIA_NOME[nome], "valor": f"{padrao:.0%} → {v:.0%}",
                               **metricas_carteira(rodar_estrategia(dados), dados)})
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# 6. Piso de volume no agressivo
# ---------------------------------------------------------------------------
def ipca_indice() -> pd.Series:
    """Índice do IPCA (base 1 no primeiro mês), por fim de mês. Guardado em data/processed."""
    if ARQ_IPCA.exists():
        s = pd.read_parquet(ARQ_IPCA)["ipca"]
    else:
        resp = requests.get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE_IPCA}/dados",
                            params={"formato": "json", "dataInicial": "01/01/2009",
                                    "dataFinal": "31/12/2026"}, timeout=60)
        resp.raise_for_status()
        bruto = pd.DataFrame(resp.json())
        s = pd.Series(bruto["valor"].astype(float).values / 100,
                      index=pd.to_datetime(bruto["data"], format="%d/%m/%Y") + pd.offsets.MonthEnd(0),
                      name="ipca")
        s.to_frame().to_parquet(ARQ_IPCA)
    return (1 + s).cumprod()


def piso_nominal(indice: pd.Series) -> callable:
    """Piso em R$ mil/dia NOMINAIS na data t: R$ 1 mi de out/2026 trazido para t pelo IPCA do
    mês ANTERIOR a t (o IPCA do próprio mês só sai depois)."""
    ref = indice.iloc[-1]

    def piso(t: pd.Timestamp) -> float:
        return PISO_REAIS_HOJE_MIL * indice.loc[: t - pd.offsets.MonthEnd(1)].iloc[-1] / ref
    return piso


def rodar_piso(dados: Dados, base: ResultadoEstrategia) -> tuple[ResultadoEstrategia, pd.DataFrame]:
    indice = ipca_indice()
    piso = piso_nominal(indice)
    datas_agr = datas_rebalanceamento(dados.calendario, estrategia.FREQ_AGRESSIVO)
    datas_def = datas_rebalanceamento(dados.calendario, estrategia.FREQ_DEFENSIVO)
    tamanho_univ = {}

    def selecionar(janela, t):
        univ = universo_por_piso(janela, t, piso(t))
        tamanho_univ[t] = {"piso (R$ mil/dia nominais)": piso(t), "universo com piso": len(univ),
                           "universo top 90": len(universo_liquido(janela, t))}
        return escolher_agressivo(janela, univ)

    agressivo = rodar_backtest(dados, datas_agr, selecionar, custo_operacao=CUSTO_OPERACAO)
    blocos = pd.DataFrame({"defensivo": base.defensivo.retornos, "agressivo": agressivo.retornos})
    pesos = pd.Series({"defensivo": PESO_DEFENSIVO, "agressivo": PESO_AGRESSIVO})
    carteira, giro = juntar_blocos(blocos, pesos, datas_def, CUSTO_OPERACAO)
    res = ResultadoEstrategia(carteira, base.defensivo, agressivo, giro, giro * CUSTO_OPERACAO)
    return res, pd.DataFrame(tamanho_univ).T


def volume_mediano_escolhidas(dados: Dados, carteiras: dict) -> pd.Series:
    """Volume médio de 3 meses (R$ mi/dia) mediano das ações escolhidas em cada data."""
    vol = dados.volume.fillna(0).rolling(63, min_periods=1).mean()
    return pd.Series({t: vol.loc[t, tk].median() / 1e3 for t, tk in carteiras.items()})


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------
def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    aplicar_estilo()
    print("Carregando dados e rodando o padrão...")
    dados = carregar_dados()
    base = rodar_estrategia(dados)
    idx = base.carteira.index
    ibov, cdi = dados.ibov.reindex(idx), dados.cdi.reindex(idx)
    series = pd.DataFrame({CART: base.carteira, DEF: base.defensivo.retornos, AGR: base.agressivo.retornos})
    anos = (idx[-1] - idx[0]).days / 365.25
    rel = [f"# Robustez (Aula 3)\n\nGerado por `python src/robustez.py`. Período {idx[0]:%d/%m/%Y} a "
           f"{idx[-1]:%d/%m/%Y} ({num(anos, 1)} anos); custo de {pct(CUSTO_OPERACAO)} por operação. "
           "Estratégia congelada (P20): nada aqui muda o padrão nem escolhe parâmetros.\n"]

    # 1 ---------------------------------------------------------------------------------------
    print("1. Tearsheets...")
    qs_tab = tearsheets(series, ibov, cdi)
    if qs_tab is not None:
        rel += ["## 1. Tearsheets do QuantStats\n",
                f"rf fixo = CDI médio do período ({pct(qs_tab.attrs['rf'], 2)} a.a.), porque o HTML do "
                "QuantStats não aceita a série diária. O Sharpe oficial é o nosso, com CDI diário.\n",
                md(qs_tab), "\n"]

    # 2 ---------------------------------------------------------------------------------------
    t2 = excesso_cdi(series.assign(Ibovespa=ibov), cdi)
    t2.to_csv(SAIDA / "2_excesso_cdi.csv")
    anual = (1 + series[[CART]].assign(Ibovespa=ibov, CDI=cdi)).groupby(idx.year).prod() - 1
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(anual))
    ax.bar(x, anual[CART] - anual["CDI"], color=np.where(anual[CART] > anual["CDI"], "#2a78d6", "#e34948"), zorder=3)
    ax.axhline(0, color="#c3c2b7")
    ax.set_xticks(x, anual.index.astype(str))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: pct(v, 0)))
    _titulo(ax, "Carteira 65/35: retorno acima do CDI, por ano",
            f"Azul = ganhou do CDI. {t2.at['anos acima do CDI', CART]} anos; 2026 até outubro")
    fig.savefig(SAIDA / "2_excesso_cdi.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    rel += ["## 2. Ganhou do CDI?\n", md(t2), "\n![](2_excesso_cdi.png)\n"]

    # 3 ---------------------------------------------------------------------------------------
    t3 = subperiodos(series.assign(Ibovespa=ibov, CDI=cdi))
    t3.to_csv(SAIDA / "3_subperiodos.csv")
    for medida in ["CAGR", "Vol", "Max DD"]:
        rel += [f"## 3. Subperíodos: {medida}\n" if medida == "CAGR" else f"### {medida}\n",
                md(t3[medida][[CART, DEF, AGR, "Ibovespa", "CDI"]]), "\n"]
    # "Bate" só com diferença de pelo menos 0,1 p.p.; menos que isso é empate
    sub_cagr = pd.DataFrame({k: {c: cagr(s.loc[a:b]) for c, s in series.assign(Ibovespa=ibov, CDI=cdi).items()}
                             for k, (a, b) in SUBPERIODOS.items()}).T
    placar = {}
    for ref in ["Ibovespa", "CDI"]:
        dif = sub_cagr[CART] - sub_cagr[ref]
        placar[f"carteira x {ref}"] = (f"bate em {(dif >= 0.001).sum()}, empata em {(dif.abs() < 0.001).sum()}, "
                                       f"perde em {(dif <= -0.001).sum()} de {len(dif)}")
    rel += [md(pd.Series(placar, name="subperíodos (empate = diferença < 0,1 p.p.)").rename_axis("comparação").to_frame()), "\n"]

    # 4 ---------------------------------------------------------------------------------------
    print("4. Grades...")
    g_agr = grade(dados, "FREQ_AGRESSIVO", ["M", "Q"])
    g_def = grade(dados, "FREQ_DEFENSIVO", ["Q", "S"])
    for nome, g in [("4_grade_agressivo", g_agr), ("4_grade_defensivo", g_def)]:
        g.to_csv(SAIDA / f"{nome}.csv", index=False)
    grades = {"Rebalanceamento do agressivo": g_agr, "Rebalanceamento do defensivo": g_def}
    fig = grafico_grades(grades, {"Rebalanceamento do agressivo": (12, "mensal"),
                                  "Rebalanceamento do defensivo": (12, "trimestral")})
    fig.savefig(SAIDA / "4_grades.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    # As linhas com a frequência padrão aparecem nas duas grades: duplicata pela combinação
    # de parâmetros efetivos, não pelos rótulos
    todas = pd.concat([g_agr, g_def]).drop_duplicates(["janela (meses)", "freq. agressivo", "freq. defensivo"])
    base_m = metricas_carteira(base, dados)
    resumo_grade = pd.Series({
        "combinações distintas": f"{len(todas)} (as {len(g_agr) + len(g_def) - len(todas)} do rebalanceamento padrão aparecem nas duas grades)",
        "Sharpe do padrão": num(base_m["Sharpe"]),
        "Sharpe mínimo / mediano / máximo": f"{num(todas.Sharpe.min())} / {num(todas.Sharpe.median())} / {num(todas.Sharpe.max())}",
        "combinações com Sharpe > 0": f"{(todas.Sharpe > 0).sum()} de {len(todas)}",
        "CAGR mínimo / máximo": f"{pct(todas.CAGR.min(), 2)} / {pct(todas.CAGR.max(), 2)}",
        "combinações com CAGR acima do CDI": f"{(todas.CAGR > cagr(cdi)).sum()} de {len(todas)}",
    }, name="valor").rename_axis("grade").to_frame()

    def fmt(g):
        return g.assign(Sharpe=g.Sharpe.map(num), CAGR=g.CAGR.map(lambda v: pct(v, 2)),
                        **{"Max DD": g["Max DD"].map(pct), "Vol": g.Vol.map(pct)}).set_index("janela (meses)")
    rel += ["## 4. Grades de parâmetros\n",
            "**Atenção:** todas as combinações usam os mesmos dados e o mesmo período. Elas mostram se o "
            "resultado depende de um parâmetro específico, mas NÃO são evidências independentes: nove "
            "Sharpes parecidos não valem como nove testes.\n",
            md(resumo_grade), "\n### Janela × rebalanceamento do agressivo\n",
            md(fmt(g_agr)), "\n### Janela × rebalanceamento do defensivo\n", md(fmt(g_def)), "\n![](4_grades.png)\n"]

    # 5 ---------------------------------------------------------------------------------------
    print("5. Fatias...")
    t5 = fatias(dados, base_m)
    t5.to_csv(SAIDA / "5_fatias.csv", index=False)
    rel += ["## 5. Fatias ±10 p.p. (uma de cada vez)\n",
            md(t5.assign(Sharpe=t5.Sharpe.map(num), CAGR=t5.CAGR.map(lambda v: pct(v, 2)),
                         **{"Max DD": t5["Max DD"].map(pct), "Vol": t5.Vol.map(pct)}).set_index("fatia")), "\n"]

    # 6 ---------------------------------------------------------------------------------------
    print("6. Piso de volume...")
    res_piso, univ = rodar_piso(dados, base)
    univ.to_csv(SAIDA / "6_universo_piso.csv")
    comp = pd.DataFrame({
        "Top 90 (padrão)": {**metricas_carteira(base, dados)},
        "Piso de R$ 1 mi/dia (real)": {**metricas_carteira(res_piso, dados)}}).T
    agr = pd.DataFrame({"Top 90 (padrão)": base.agressivo.retornos, "Piso de R$ 1 mi/dia (real)": res_piso.agressivo.retornos,
                        "Ibovespa": ibov})
    m_agr = resumo(agr, dados.cdi, "Ibovespa")
    vol_top = volume_mediano_escolhidas(dados, base.agressivo.carteiras)
    vol_piso = volume_mediano_escolhidas(dados, res_piso.agressivo.carteiras)
    t6 = pd.DataFrame({
        "carteira: CAGR": comp.CAGR.map(lambda v: pct(v, 2)), "carteira: Sharpe": comp.Sharpe.map(num),
        "carteira: Max DD": comp["Max DD"].map(pct),
        "agressivo: CAGR": m_agr.loc["CAGR", comp.index].map(lambda v: pct(v, 2)),
        "agressivo: Sharpe": m_agr.loc["Sharpe (CDI)", comp.index].map(num),
        "agressivo: Max DD": m_agr.loc["Max drawdown", comp.index].map(pct),
        "agressivo: giro médio/mês": [pct(base.agressivo.giro.iloc[1:].mean(), 0), pct(res_piso.agressivo.giro.iloc[1:].mean(), 0)],
        "volume mediano das escolhidas (R$ mi/dia, média das datas)": [num(vol_top.mean(), 1), num(vol_piso.mean(), 1)],
        "idem, 2011-14": [num(vol_top.loc[:"2014"].mean(), 1), num(vol_piso.loc[:"2014"].mean(), 1)],
    }).T.rename_axis("medida")
    t6.to_csv(SAIDA / "6_piso_volume.csv")
    ano = univ.groupby(univ.index.year).mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(univ.index, univ["universo com piso"], color="#2a78d6", label="Universo com piso de R$ 1 mi/dia (real)")
    ax.plot(univ.index, univ["universo top 90"], color="#898781", label="Universo padrão (90 mais líquidas)")
    _eixo_datas(ax, univ.index[0], univ.index[-1]); ax.legend(loc="upper left")
    _titulo(ax, "Tamanho do universo do bloco agressivo", "Empresas elegíveis em cada mês (uma classe por empresa)")
    fig.savefig(SAIDA / "6_universo_piso.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    rel += ["## 6. Piso de volume no agressivo (teste, NÃO candidato)\n",
            "O custo de 0,2% subestima o custo das ações menos líquidas (spread e impacto maiores): "
            "este resultado é otimista.\n", md(t6), "\n",
            md(ano.map(lambda v: num(v, 0)).rename_axis("ano (média)")), "\n![](6_universo_piso.png)\n"]

    # 7 ---------------------------------------------------------------------------------------
    m = resumo(series.assign(Ibovespa=ibov), dados.cdi, "Ibovespa")
    linhas = {}
    for c in [CART, DEF, AGR]:
        sr = m.at["Sharpe (CDI)", c]
        linhas[c] = {"Sharpe (CDI)": num(sr), "t ≈ Sharpe × √anos": num(sr * np.sqrt(anos)),
                     "anos necessários (95%)": f"{(Z_95 / sr) ** 2:.0f}" if sr > 0 else "∞ (Sharpe ≤ 0)",
                     "anos que temos": num(anos, 1)}
    t7 = pd.DataFrame(linhas).T.rename_axis("série")
    t7.to_csv(SAIDA / "7_anos_de_dado.csv")
    t7b = significancia(series, ibov, cdi, anos, m)
    t7b.to_csv(SAIDA / "7_significancia.csv")
    todas_series = series.assign(Ibovespa=ibov, CDI=cdi)
    t7c = pd.DataFrame({"período todo": todas_series.apply(cagr),
                        "sem 2017-19": sem_anos(todas_series, [2017, 2018, 2019], anos)}).T
    t7c.to_csv(SAIDA / "7_sem_2017_19.csv")
    rel += ["## 7. Quantos anos de dado seriam necessários?\n",
            f"Regra: t ≈ Sharpe × √anos; para 95% de confiança, anos ≥ ({num(Z_95)} / Sharpe)².\n", md(t7), "\n",
            "### Intervalo do Sharpe e t do alpha\n",
            "Erro-padrão do Sharpe ≈ √((1 + SR²/2) / anos). Alpha = intercepto da regressão do excesso "
            "diário sobre o CDI contra o excesso do Ibovespa, anualizado (× 252). t com Newey-West.\n",
            md(t7b), "\n### CAGR sem 2017-19\n", md(t7c.map(lambda v: pct(v, 2)).rename_axis("CAGR")), "\n"]

    (SAIDA / "resumo.md").write_text("\n".join(rel), encoding="utf-8")
    print(f"Pronto: {SAIDA}")


if __name__ == "__main__":
    main()
