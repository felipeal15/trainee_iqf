"""
diagnostico.py — Diagnóstico do bloco agressivo (correção 2 do monitor: "levantem o retorno por
ativo dessa parte para ver o que está acontecendo").

NÃO muda a estratégia nem escolhe parâmetros: usa as mesmas funções, o mesmo universo, o mesmo
custo (CUSTO_OPERACAO) e o mesmo rebalanceamento mensal, e só DESCREVE o resultado.

    1. Contribuição de cada ação para o retorno do bloco
    2. Size e Momentum separados, no mesmo universo (+ a carteira das perdedoras de Momentum,
       usada só como referência no teste de momentum crash)
    3. O que é "small" no nosso universo (valor de mercado em R$ bi)
    4. Concentração: nº de ações e benefício de diversificação
    5. Retorno por ano e por subperíodo, piores quedas e momentum crash
    6. Giro e custo
    7. Papel do bloco agressivo na carteira 65/35

Uso (a partir da raiz do projeto):
    python src/diagnostico.py   # grava tabelas (.csv), gráficos (.png) e resumo.md em
                                # resultados/diagnostico/
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

from backtest import LOOKBACK, Resultado, datas_rebalanceamento, rodar_backtest
from dados import RAIZ, Dados, carregar_dados
from estrategia import (CUSTO_OPERACAO, FATIA_MOMENTUM, FATIA_SIZE, PESO_AGRESSIVO,
                        PESO_DEFENSIVO, juntar_blocos, melhores, rodar_estrategia)
from fatores import momentum, tamanho
from graficos import (CORES, EIXO, TINTA_SECUNDARIA, _eixo_datas, _titulo, acumulado,
                      aplicar_estilo, retornos_anuais, underwater)
from metricas import cagr, curva, periodos_drawdown, resumo
from universo import universo_liquido

SAIDA = RAIZ / "resultados" / "diagnostico"

# Nomes das séries (os da estratégia usam as cores fixas de graficos.py)
AGR, DEF, CART = "Bloco agressivo", "Bloco defensivo", "Estratégia 65/35"
UNIV, SIZE, MOM, PERD = ("Universo peso igual", "Só Size (30% menores)",
                         "Só Momentum (30% maiores)", "Perdedoras de Momentum (30% menores)")

# Subperíodos definidos pelo ciclo econômico, não pelo resultado (pedidos no enunciado)
SUBPERIODOS = {"2011-14": ("2011", "2014"), "2015-16 (recessão)": ("2015", "2016"),
               "2017-19": ("2017", "2019"), "2020 (Covid)": ("2020", "2020"),
               "2021-22 (alta de juros)": ("2021", "2022"), "2023-26": ("2023", "2026")}


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------
def pct(x: float, casas: int = 1) -> str:
    return "—" if pd.isna(x) else f"{x:.{casas}%}".replace(".", ",").replace("-", "−")


def num(x: float, casas: int = 2) -> str:
    return "—" if pd.isna(x) else f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def md(df: pd.DataFrame) -> str:
    """Tabela Markdown simples (sem depender do pacote tabulate)."""
    linhas = ["| " + " | ".join([str(df.index.name or "")] + [str(c) for c in df.columns]) + " |",
              "|" + "---|" * (len(df.columns) + 1)]
    linhas += ["| " + " | ".join([str(i)] + [str(v) for v in row]) + " |"
               for i, row in zip(df.index, df.values)]
    return "\n".join(linhas)


def tabela_metricas(retornos: pd.DataFrame, dados: Dados) -> pd.DataFrame:
    m = resumo(retornos, dados.cdi, benchmark="Ibovespa")
    return pd.DataFrame({
        "CAGR": m.loc["CAGR"].map(lambda v: pct(v, 2)),
        "Volatilidade": m.loc["Volatilidade (anual)"].map(pct),
        "Sharpe (CDI)": m.loc["Sharpe (CDI)"].map(num),
        "Max drawdown": m.loc["Max drawdown"].map(pct),
        "Alpha": m.loc["Alpha (anual)"].map(lambda v: pct(v, 2)),
        "Beta": m.loc["Beta"].map(num),
    }).rename_axis("série")


def salvar(fig: plt.Figure, nome: str) -> None:
    fig.savefig(SAIDA / nome, dpi=130, bbox_inches="tight")
    plt.close(fig)


def mensal(retornos: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return (1 + retornos).resample("ME").prod() - 1


# ---------------------------------------------------------------------------
# Variantes do bloco (mesmo universo, mesmo custo, mesmo rebalanceamento)
# ---------------------------------------------------------------------------
def rodar_variantes(dados: Dados, datas: pd.DatetimeIndex) -> dict[float, dict[str, Resultado]]:
    """Roda cada variante com custo 0 e com CUSTO_OPERACAO. O universo de cada data é
    calculado uma vez e reaproveitado."""
    univ = {t: universo_liquido(dados.janela(t, LOOKBACK), t) for t in datas}
    regras = {
        UNIV: lambda j, u: u,
        SIZE: lambda j, u: melhores(-tamanho(j, u), FATIA_SIZE),
        MOM: lambda j, u: melhores(momentum(j, u), FATIA_MOMENTUM),
        AGR: lambda j, u: melhores(momentum(j, melhores(-tamanho(j, u), FATIA_SIZE)), FATIA_MOMENTUM),
        PERD: lambda j, u: melhores(-momentum(j, u), FATIA_MOMENTUM),
    }
    saida = {}
    for custo in (0.0, CUSTO_OPERACAO):
        saida[custo] = {nome: rodar_backtest(dados, datas, lambda j, t, f=f: f(j, univ[t]),
                                             custo_operacao=custo)
                        for nome, f in regras.items()}
    return saida


# ---------------------------------------------------------------------------
# 1. Contribuição por ação
# ---------------------------------------------------------------------------
def situacao(dados: Dados, ticker: str) -> tuple[str, float]:
    """Se a ação parou de negociar antes do fim da base: troca de código (outro ticker com o
    mesmo valor de mercado continua negociando, ver P17) ou saída da bolsa (falência,
    aquisição ou fechamento de capital: a base não diz qual). Devolve também o retorno nos
    12 meses antes da última negociação (queda grande sugere falência/recuperação)."""
    r, vm = dados.retorno, dados.valor_mercado
    ultimo = r[ticker].last_valid_index()
    if ultimo >= r.index[-1] - pd.Timedelta(days=31):
        return "ativa", np.nan
    antes = (1 + r[ticker].loc[:ultimo].iloc[-252:].fillna(0)).prod() - 1
    mes = vm[ticker].last_valid_index()
    if mes is not None:
        mesmos = vm.loc[mes][vm.loc[mes] == vm.at[mes, ticker]].index.drop(ticker)
        seguem = [t for t in mesmos if r[t].last_valid_index() > ultimo]
        if seguem:
            return f"troca de código → {seguem[0]} ({ultimo:%m/%Y})", antes
    return f"saiu da bolsa ({ultimo:%m/%Y})", antes


def contribuicao(dados: Dados, bloco: Resultado) -> pd.DataFrame:
    """Peso inicial x retorno da ação em cada período, somado. A soma de todas as ações dá a
    soma dos retornos mensais do bloco antes do custo (soma simples, não composta)."""
    r = dados.retorno
    datas = list(bloco.carteiras) + [r.index[-1]]
    linhas = []
    for t0, t1 in zip(datas[:-1], datas[1:]):
        tickers = bloco.carteiras[t0]
        periodo = r.loc[(r.index > t0) & (r.index <= t1), tickers].fillna(0.0)
        ret = (1 + periodo).prod() - 1
        linhas += [{"data": t0, "ticker": t, "retorno": ret[t], "contribuicao": ret[t] / len(tickers)}
                   for t in tickers]
    df = pd.DataFrame(linhas)
    por = df.groupby("ticker").agg(contribuicao=("contribuicao", "sum"), meses=("data", "count"),
                                   retorno_medio_mes=("retorno", "mean"),
                                   primeira=("data", "min"), ultima=("data", "max"))
    sit = {t: situacao(dados, t) for t in por.index}
    por["situacao"] = [sit[t][0] for t in por.index]
    por["retorno_12m_antes_de_sair"] = [sit[t][1] for t in por.index]
    return por.sort_values("contribuicao")


def grafico_contribuicao(por: pd.DataFrame) -> plt.Figure:
    sel = pd.concat([por.head(15), por.tail(15)])
    fig, ax = plt.subplots(figsize=(9, 8))
    cores = [CORES[AGR] if v > 0 else "#e34948" for v in sel["contribuicao"]]
    rotulos = [f"{t}{' †' if s != 'ativa' else ''}  ({m} m)"
               for t, s, m in zip(sel.index, sel["situacao"], sel["meses"])]
    ax.barh(range(len(sel)), sel["contribuicao"], color=cores, zorder=3)
    ax.set_yticks(range(len(sel)), rotulos, fontsize=8.5)
    ax.axvline(0, color=EIXO, lw=1)
    ax.grid(axis="x"); ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _titulo(ax, "Bloco agressivo: 15 maiores e 15 menores contribuições",
            "Soma de peso × retorno em cada mês, antes do custo. † = parou de negociar; (m) = meses na carteira")
    return fig


# ---------------------------------------------------------------------------
# 3. Tamanho
# ---------------------------------------------------------------------------
def tamanhos(dados: Dados, variantes: dict[str, Resultado]) -> pd.DataFrame:
    """Valor de mercado (R$ bi, nominal) do universo, das 30% menores e do bloco, por data."""
    vm = dados.valor_mercado / 1e6  # R$ mil -> R$ bi
    linhas = []
    for t, univ in variantes[UNIV].carteiras.items():
        hoje = vm.loc[:t].iloc[-1]
        pequenas, bloco = hoje[variantes[SIZE].carteiras[t]], hoje[variantes[AGR].carteiras[t]]
        linhas.append({"data": t, "universo_mediana": hoje[univ].median(),
                       "menores30_mediana": pequenas.median(), "menores30_maior": pequenas.max(),
                       "bloco_mediana": bloco.median(), "bloco_menor": bloco.min(),
                       "bloco_maior": bloco.max()})
    return pd.DataFrame(linhas).set_index("data")


def grafico_tamanho(tam: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.fill_between(tam.index, tam["bloco_menor"], tam["bloco_maior"], color=CORES[AGR],
                    alpha=0.15, lw=0, label="Bloco agressivo: menor a maior")
    ax.plot(tam.index, tam["bloco_mediana"], color=CORES[AGR], label="Bloco agressivo: mediana")
    ax.plot(tam.index, tam["menores30_maior"], color=TINTA_SECUNDARIA, ls="--",
            label="Maior das 30% menores (corte do Size)")
    ax.plot(tam.index, tam["universo_mediana"], color=CORES["Estratégia 65/35"],
            label="Universo: mediana")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R$ {v:g} bi"))
    _eixo_datas(ax, tam.index[0], tam.index[-1])
    ax.legend(loc="upper left", fontsize=8.5)
    _titulo(ax, "O que é \"small\" no nosso universo", "Valor de mercado da empresa, R$ bi nominais, escala log")
    return fig


# ---------------------------------------------------------------------------
# 4. Concentração
# ---------------------------------------------------------------------------
def diversificacao(dados: Dados, bloco: Resultado, referencia: pd.Series) -> dict[str, float]:
    """Volatilidade do bloco x volatilidade média das ações que ele contém (dentro de cada
    mês), correlação média implícita e quanto da variância diária NÃO é explicada pelo
    universo peso igual (risco específico das poucas ações)."""
    r = dados.retorno
    datas = list(bloco.carteiras) + [r.index[-1]]
    var_acoes, var_bloco, n = [], [], []
    for t0, t1 in zip(datas[:-1], datas[1:]):
        dias = (r.index > t0) & (r.index <= t1)
        if dias.sum() < 5:
            continue
        var_acoes.append(r.loc[dias, bloco.carteiras[t0]].var().mean())
        var_bloco.append(bloco.retornos.loc[(bloco.retornos.index > t0) & (bloco.retornos.index <= t1)].var())
        n.append(len(bloco.carteiras[t0]))
    va, vb, nm = np.mean(var_acoes), np.mean(var_bloco), np.mean(n)
    rho = (vb / va - 1 / nm) / (1 - 1 / nm)  # var_carteira = var_media x (1/n + (1-1/n) rho)
    r2 = bloco.retornos.corr(referencia.reindex(bloco.retornos.index)) ** 2
    return {"ações por carteira (média)": nm, "mín": min(n), "máx": max(n),
            "vol. média das ações": np.sqrt(va * 252), "vol. da carteira": np.sqrt(vb * 252),
            "carteira / ações": np.sqrt(vb / va), "correlação média implícita": rho,
            "R² diário contra o universo": r2, "risco específico (1 − R²)": 1 - r2}


# ---------------------------------------------------------------------------
# 5. Períodos e momentum crash
# ---------------------------------------------------------------------------
def por_subperiodo(retornos: pd.DataFrame) -> pd.DataFrame:
    linhas = {}
    for nome, (ini, fim) in SUBPERIODOS.items():
        trecho = retornos.loc[ini:fim]
        linhas[nome] = {c: pct(cagr(trecho[c]), 1) for c in retornos.columns}
    return pd.DataFrame(linhas).T.rename_axis("subperíodo (CAGR)")


def piores_quedas_com_mercado(serie: pd.Series, outras: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    linhas = []
    for _, p in periodos_drawdown(serie).head(n).iterrows():
        janela = outras.loc[(outras.index > p["topo"]) & (outras.index <= p["fundo"])]
        linha = {"topo": f"{p['topo']:%m/%Y}", "fundo": f"{p['fundo']:%m/%Y}",
                 "recuperação": "não recuperou" if pd.isna(p["recuperação"]) else f"{p['recuperação']:%m/%Y}",
                 "queda do bloco": pct(p["queda"])}
        linha.update({f"{c} no mesmo trecho": pct((1 + janela[c]).prod() - 1) for c in outras.columns})
        linhas.append(linha)
    return pd.DataFrame(linhas).rename_axis("#")


def momentum_crash(m: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Estado definido ANTES de olhar o resultado (Daniel e Moskowitz, 2016, com 12 meses para
    casar com o nosso Momentum 12-1): 'rebote' = Ibovespa caiu nos 12 meses anteriores e
    sobe no mês. É quando as ações que mais caíram costumam liderar."""
    passado = (1 + m["Ibovespa"]).rolling(12).apply(np.prod, raw=True).shift(1) - 1
    rebote = (passado < 0) & (m["Ibovespa"] > 0)
    m = m.assign(**{"Momentum − Perdedoras": m[MOM] - m[PERD]})
    colunas = [AGR, MOM, PERD, "Momentum − Perdedoras", UNIV, "Ibovespa"]
    tab = pd.DataFrame({
        f"rebote ({rebote.sum()} meses)": m.loc[rebote, colunas].mean(),
        f"demais ({(~rebote & passado.notna()).sum()} meses)": m.loc[~rebote & passado.notna(), colunas].mean(),
    }).map(lambda v: pct(v, 2)).rename_axis("retorno médio mensal")
    return tab, rebote


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------
def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    aplicar_estilo()
    print("Carregando dados...")
    dados = carregar_dados()
    mensais = datas_rebalanceamento(dados.calendario, "M")
    print("Rodando a estratégia padrão (sem custo e com custo)...")
    est = {c: rodar_estrategia(dados, custo_operacao=c) for c in (0.0, CUSTO_OPERACAO)}
    print("Rodando as variantes do bloco agressivo...")
    var = rodar_variantes(dados, mensais)
    # A variante "Bloco agressivo" tem de ser exatamente o bloco da estratégia
    assert var[CUSTO_OPERACAO][AGR].carteiras == est[CUSTO_OPERACAO].agressivo.carteiras
    assert var[CUSTO_OPERACAO][AGR].retornos.equals(est[CUSTO_OPERACAO].agressivo.retornos)

    v = var[CUSTO_OPERACAO]
    idx = v[AGR].retornos.index
    ibov, cdi = dados.ibov.reindex(idx).rename("Ibovespa"), dados.cdi.reindex(idx).rename("CDI")
    r = pd.DataFrame({nome: res.retornos for nome, res in v.items()}).assign(Ibovespa=ibov, CDI=cdi)
    r0 = pd.DataFrame({nome: res.retornos for nome, res in var[0.0].items()}).assign(Ibovespa=ibov)
    rel = [f"# Diagnóstico do bloco agressivo\n\nGerado por `python src/diagnostico.py`. "
           f"Período {idx[0]:%d/%m/%Y} a {idx[-1]:%d/%m/%Y}; custo principal {pct(CUSTO_OPERACAO)} "
           "por operação. Nada aqui muda a estratégia.\n"]

    # 1. Contribuição -----------------------------------------------------------------------
    por = contribuicao(dados, v[AGR])
    por.to_csv(SAIDA / "1_contribuicao_por_acao.csv")
    salvar(grafico_contribuicao(por), "1_contribuicao.png")
    pos, neg = por.loc[por.contribuicao > 0, "contribuicao"], por.loc[por.contribuicao < 0, "contribuicao"]
    custo_total = v[AGR].custo.sum()
    conc = pd.Series({
        "ações diferentes que passaram pelo bloco": f"{len(por)}",
        "soma das contribuições (antes do custo)": pct(por.contribuicao.sum()),
        "soma dos custos": pct(-custo_total),
        "soma das contribuições positivas": pct(pos.sum()),
        "soma das contribuições negativas": pct(neg.sum()),
        "15 maiores / positivas": pct(por.tail(15).contribuicao.sum() / pos.sum()),
        "15 menores / negativas": pct(por.head(15).contribuicao.sum() / neg.sum()),
        "5 menores / negativas": pct(por.head(5).contribuicao.sum() / neg.sum()),
        "ações com contribuição negativa": f"{len(neg)} de {len(por)}",
        "meses na carteira por ação (mediana)": f"{por.meses.median():.0f}",
        "das 15 menores, quantas pararam de negociar": f"{(por.head(15).situacao != 'ativa').sum()}",
        "das 15 maiores, quantas pararam de negociar": f"{(por.tail(15).situacao != 'ativa').sum()}",
    }, name="valor").rename_axis("medida").to_frame()

    def fmt_por(df):
        return pd.DataFrame({"contribuição": df.contribuicao.map(pct), "meses": df.meses,
                             "retorno médio no mês": df.retorno_medio_mes.map(pct),
                             "na carteira": [f"{a:%m/%Y}–{b:%m/%Y}" for a, b in zip(df.primeira, df.ultima)],
                             "situação": df.situacao,
                             "12m antes de sair": df.retorno_12m_antes_de_sair.map(pct)})
    rel += ["## 1. Contribuição por ação\n", md(conc), "\n### 15 menores\n", md(fmt_por(por.head(15))),
            "\n### 15 maiores\n", md(fmt_por(por.tail(15).iloc[::-1])), "\n![](1_contribuicao.png)\n"]

    # 2. Size x Momentum ---------------------------------------------------------------------
    t2 = pd.concat({"custo 0,2%": tabela_metricas(r[[UNIV, SIZE, MOM, AGR, "Ibovespa", "CDI"]], dados),
                    "sem custo": tabela_metricas(r0[[UNIV, SIZE, MOM, AGR, "Ibovespa"]], dados)})
    t2.to_csv(SAIDA / "2_size_x_momentum.csv")
    giros = pd.DataFrame({n: {"ações por carteira": f"{np.mean([len(c) for c in v[n].carteiras.values()]):.0f}",
                              "giro médio por mês": pct(v[n].giro.iloc[1:].mean(), 0)}
                          for n in [UNIV, SIZE, MOM, AGR]}).T.rename_axis("variante")
    salvar(acumulado(r[[UNIV, SIZE, MOM, AGR, "CDI"]], "Size e Momentum separados, mesmo universo",
                     f"Peso igual, mensal, custo de {pct(CUSTO_OPERACAO)}"), "2_size_x_momentum.png")
    rel += ["\n## 2. Size e Momentum separados (mesmo universo, mesmo custo, mensal)\n",
            md(t2.reset_index(level=0).rename(columns={"level_0": "custo"})), "\n", md(giros),
            "\n![](2_size_x_momentum.png)\n"]

    # 3. Tamanho -----------------------------------------------------------------------------
    tam = tamanhos(dados, v)
    tam.to_csv(SAIDA / "3_tamanho_por_data.csv")
    salvar(grafico_tamanho(tam), "3_tamanho.png")
    por_ano = tam.groupby(tam.index.year).mean().map(lambda x: num(x, 1)).rename_axis("ano (média, R$ bi)")
    resumo_tam = pd.DataFrame({
        "período todo (média das datas)": tam.mean(), "2023-26": tam.loc["2023":].mean(),
        f"última data ({tam.index[-1]:%m/%Y})": tam.iloc[-1]}).T.map(lambda x: num(x, 1)).rename_axis("R$ bi")
    rel += ["\n## 3. O que é \"small\" no nosso universo (R$ bi nominais)\n", md(resumo_tam), "\n",
            md(por_ano), "\n![](3_tamanho.png)\n"]

    # 4. Concentração ------------------------------------------------------------------------
    t4 = pd.DataFrame({n: diversificacao(dados, v[n], r[UNIV]) for n in [AGR, SIZE, MOM, UNIV]})
    t4.to_csv(SAIDA / "4_concentracao.csv")
    formatos = {"ações por carteira (média)": lambda x: num(x, 1), "mín": lambda x: f"{x:.0f}",
                "máx": lambda x: f"{x:.0f}", "carteira / ações": lambda x: num(x, 2),
                "correlação média implícita": lambda x: num(x, 2), "R² diário contra o universo": lambda x: num(x, 2)}
    t4f = t4.apply(lambda linha: linha.map(formatos.get(linha.name, pct)), axis=1).rename_axis("medida")
    rel += ["\n## 4. Concentração e diversificação\n", md(t4f), "\n"]

    # 5. Períodos ----------------------------------------------------------------------------
    serie5 = r[[AGR, UNIV, SIZE, MOM, "Ibovespa", "CDI"]]
    anual = ((1 + serie5).groupby(serie5.index.year).prod() - 1)
    anual.to_csv(SAIDA / "5_retorno_anual.csv")
    salvar(retornos_anuais(r[[AGR, UNIV, "Ibovespa"]], "Retorno por ano",
                           f"Custo de {pct(CUSTO_OPERACAO)}; 2026 até outubro"), "5_retorno_anual.png")
    sub = por_subperiodo(serie5)
    quedas = piores_quedas_com_mercado(r[AGR], r[[UNIV, "Ibovespa"]])
    m = mensal(r[[AGR, MOM, PERD, UNIV, "Ibovespa"]])
    crash, rebote = momentum_crash(m)
    piores = m[AGR].nsmallest(10)
    passado = (1 + m["Ibovespa"]).rolling(12).apply(np.prod, raw=True).shift(1) - 1
    t_piores = pd.DataFrame({"bloco": piores.map(pct), "universo": m.loc[piores.index, UNIV].map(pct),
                             "Ibovespa no mês": m.loc[piores.index, "Ibovespa"].map(pct),
                             "Ibovespa 12m antes": passado[piores.index].map(pct),
                             "Momentum − Perdedoras": (m[MOM] - m[PERD])[piores.index].map(pct),
                             "rebote?": rebote[piores.index].map({True: "sim", False: "não"})})
    t_piores.index = [f"{d:%m/%Y}" for d in t_piores.index]
    t_piores = t_piores.rename_axis("pior mês")
    sub.to_csv(SAIDA / "5_subperiodos.csv"); quedas.to_csv(SAIDA / "5_piores_quedas.csv")
    crash.to_csv(SAIDA / "5_momentum_crash.csv")
    rel += ["\n## 5. Por período\n", md(anual.map(pct).rename_axis("ano")), "\n", md(sub),
            "\n### Piores quedas do bloco\n", md(quedas), "\n### Momentum crash\n", md(crash), "\n",
            md(t_piores), "\n![](5_retorno_anual.png)\n"]

    # 6. Custo -------------------------------------------------------------------------------
    a0, a2 = cagr(est[0.0].agressivo.retornos), cagr(est[CUSTO_OPERACAO].agressivo.retornos)
    anos = (idx[-1] - idx[0]).days / 365.25
    cdi_cagr, univ_cagr = cagr(cdi), cagr(r[UNIV])
    t6 = pd.Series({
        "CAGR sem custo": pct(a0, 2), "CAGR com custo": pct(a2, 2),
        "perda de CAGR pelo custo": pct(a0 - a2, 2),
        "custo pago por ano (soma simples)": pct(v[AGR].custo.sum() / anos, 2),
        "custo acumulado (composto)": pct(1 - (1 - v[AGR].custo).prod(), 1),
        "distância até o CDI (com custo)": pct(cdi_cagr - a2, 2),
        "parte dessa distância explicada pelo custo": pct((a0 - a2) / (cdi_cagr - a2), 0),
        "distância até o universo peso igual (ambos com custo)": pct(univ_cagr - a2, 2),
        "parte dessa distância explicada pelo custo extra": pct(
            ((a0 - a2) - (cagr(r0[UNIV]) - univ_cagr)) / (univ_cagr - a2), 0),
    }, name="valor").rename_axis("medida").to_frame()
    t6.to_csv(SAIDA / "6_custo.csv")
    custo_df = pd.DataFrame({"Bloco agressivo sem custo": est[0.0].agressivo.retornos, AGR: r[AGR]})
    salvar(acumulado(custo_df, "Quanto o custo tira do bloco agressivo",
                     f"Mesmas carteiras; a diferença é só o custo de {pct(CUSTO_OPERACAO)} por operação"),
           "6_custo.png")
    rel += ["\n## 6. Giro e custo\n", md(t6), "\n![](6_custo.png)\n"]

    # 7. Papel na carteira -------------------------------------------------------------------
    e = est[CUSTO_OPERACAO]
    trimestrais = datas_rebalanceamento(dados.calendario, "Q")
    so_def_cdi, _ = juntar_blocos(pd.DataFrame({"defensivo": e.defensivo.retornos, "cdi": cdi}),
                                  pd.Series({"defensivo": PESO_DEFENSIVO, "cdi": PESO_AGRESSIVO}),
                                  trimestrais, CUSTO_OPERACAO)
    nome_ref = f"{PESO_DEFENSIVO:.0%} defensivo + {PESO_AGRESSIVO:.0%} CDI (referência)"
    r7 = pd.DataFrame({CART: e.carteira, DEF: e.defensivo.retornos, AGR: e.agressivo.retornos,
                       nome_ref: so_def_cdi, "Ibovespa": ibov, "CDI": cdi})
    t7 = tabela_metricas(r7, dados)
    corr = pd.Series({"diária, período todo": num(r7[AGR].corr(r7[DEF])),
                      "mensal, período todo": num(mensal(r7[AGR]).corr(mensal(r7[DEF])))}
                     | {f"diária, {k}": num(r7.loc[a:b, AGR].corr(r7.loc[a:b, DEF]))
                        for k, (a, b) in SUBPERIODOS.items()}, name="correlação agressivo × defensivo")
    c_cart, c_def, c_agr = curva(r7[CART]), curva(r7[DEF]), curva(r7[AGR])
    linhas = []
    for _, p in periodos_drawdown(r7[CART]).head(5).iterrows():
        trecho = slice(p["topo"], p["fundo"])
        linhas.append({"topo": f"{p['topo']:%m/%Y}", "fundo": f"{p['fundo']:%m/%Y}",
                       "carteira 65/35": pct(p["queda"]),
                       "só defensivo, mesmo trecho": pct(c_def[trecho].iloc[-1] / c_def[p["topo"]] - 1),
                       "só agressivo, mesmo trecho": pct(c_agr[trecho].iloc[-1] / c_agr[p["topo"]] - 1)})
    dd7 = pd.DataFrame(linhas).rename_axis("#")
    vol_sub = pd.DataFrame({k: {"vol. carteira 65/35": pct(r7.loc[a:b, CART].std() * np.sqrt(252)),
                                "vol. só defensivo": pct(r7.loc[a:b, DEF].std() * np.sqrt(252))}
                            for k, (a, b) in SUBPERIODOS.items()}).T.rename_axis("subperíodo")
    t7.to_csv(SAIDA / "7_papel_na_carteira.csv"); dd7.to_csv(SAIDA / "7_quedas_da_carteira.csv")
    salvar(underwater(r7[[CART, DEF]], "Quedas da carteira com e sem o bloco agressivo",
                      f"Custo de {pct(CUSTO_OPERACAO)}"), "7_drawdown_carteira.png")
    rel += ["\n## 7. Papel do bloco agressivo na carteira\n", md(t7), "\n", md(corr.to_frame()), "\n",
            "### Piores quedas da carteira e o que cada bloco fez no mesmo trecho\n", md(dd7), "\n",
            md(vol_sub), "\n![](7_drawdown_carteira.png)\n"]

    (SAIDA / "resumo.md").write_text("\n".join(rel), encoding="utf-8")
    print(f"Pronto: {SAIDA}")


if __name__ == "__main__":
    main()
