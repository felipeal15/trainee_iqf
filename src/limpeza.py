"""
limpeza.py — Transforma as planilhas brutas do Economatica em bases limpas para o backtest.

Entrada  (data/raw/):
    fechamento_ajust.xlsx  diária      Fechamento ajust p/ prov, moeda orig
    volume.xlsx            diária      Volume$ em milhares
    valor_mercado.xlsx     mensal      Valor Mercado da empresa, em milhares
    preco_lucro.xlsx       trimestral  P/L 12 meses, consolidado
    roe.xlsx               trimestral  RenPat (PL fim), 12 meses, consolidado
    div_pl.xlsx            trimestral  Dívida Bruta / Patrimônio Líquido, consolidado

Saída (data/processed/), todas no formato LONGO (uma linha por data x ticker):
    precos_diarios.parquet          data, ticker, fechamento_ajust, volume_mil, retorno
    valor_mercado_mensal.parquet    data, ticker, valor_mercado_mil, preenchido
    fundamentos_trimestrais.parquet trimestre, data_referencia, data_disponivel, ticker,
                                    pl, roe, div_pl, lucro_12m_mil + flags
    relatorio_limpeza.md            resumo do que foi feito e números de controle

Uso (a partir da raiz do projeto):
    python src/limpeza.py

As decisões por trás de cada tratamento estão em contexto.md.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
OUT = RAIZ / "data" / "processed"

ARQUIVOS = {
    "fechamento_ajust": "fechamento_ajust.xlsx",
    "volume_mil": "volume.xlsx",
    "valor_mercado_mil": "valor_mercado.xlsx",
    "pl": "preco_lucro.xlsx",
    "roe": "roe.xlsx",
    "div_pl": "div_pl.xlsx",
}

# Linha (0-based) onde está o cabeçalho "Data | indicador\n...\nTICKER".
# As 3 primeiras linhas do export do Economatica são lixo (nome de uma ação + linhas vazias).
LINHA_CABECALHO = 3

# Quantos meses o valor de mercado pode ser "carregado para frente" quando a ação
# não negociou no fim do mês. Mais do que isso, consideramos que não há dado.
FFILL_VALOR_MERCADO_MESES = 2

# Defasagem de divulgação dos balanços (prazos CVM: ITR em até 45 dias,
# DFP anual em até 3 meses). Usamos 3 meses para todos os trimestres — conservador.
DEFASAGEM_BALANCO_MESES = 3

# Retorno diário acima disso é sinalizado no relatório como possível erro de dado
# (não é removido automaticamente).
LIMITE_RETORNO_SUSPEITO = 1.0  # +100% em um dia

MESES_PT = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12,
}


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def ler_matriz_economatica(caminho: Path) -> pd.DataFrame:
    """Lê um export do Matrix do Economatica e devolve um DataFrame largo:
    índice = coluna 'Data' original (texto ou datetime), colunas = tickers, valores float."""
    df = pd.read_excel(caminho, header=LINHA_CABECALHO)
    # O ticker é a última linha do cabeçalho multilinha ("P/L\nEm moeda orig\n...\nPETR4")
    tickers = [str(c).split("\n")[-1].strip() for c in df.columns[1:]]
    df.columns = ["Data"] + tickers
    if df.columns.duplicated().any():
        dup = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(f"{caminho.name}: tickers duplicados no cabeçalho: {dup}")
    df = df.set_index("Data")
    # O Economatica marca ausência de dado com "-"
    df = df.replace("-", np.nan).apply(pd.to_numeric, errors="coerce")
    return df


def converter_mes(rotulo: str) -> pd.Timestamp:
    """'Fev-2000' -> 2000-02-29 (último dia do mês)."""
    mes, ano = rotulo.split("-")
    return pd.Timestamp(year=int(ano), month=MESES_PT[mes], day=1) + pd.offsets.MonthEnd(0)


def converter_trimestre(rotulo: str) -> pd.Period:
    """'3T2025' -> Period('2025Q3')."""
    return pd.Period(f"{rotulo[2:]}Q{rotulo[0]}", freq="Q")


def para_longo(largo: pd.DataFrame, nome_valor: str, nome_data: str = "data") -> pd.DataFrame:
    longo = largo.stack(future_stack=True).rename(nome_valor).reset_index()
    longo.columns = [nome_data, "ticker", nome_valor]
    return longo


# ---------------------------------------------------------------------------
# Limpeza
# ---------------------------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rel: list[str] = ["# Relatório de limpeza\n"]

    print("Lendo planilhas do Economatica...")
    bruto = {nome: ler_matriz_economatica(RAW / arq) for nome, arq in ARQUIVOS.items()}

    # 1) Todas as bases precisam ter os mesmos tickers -------------------------------
    referencia = list(bruto["fechamento_ajust"].columns)
    for nome, df in bruto.items():
        if set(df.columns) != set(referencia):
            raise ValueError(f"{nome}: conjunto de tickers diferente do fechamento")
    rel.append(f"- Tickers no screening do Economatica: **{len(referencia)}**")

    # 2) Tickers sem nenhum preço no período não servem para o backtest ------------
    com_preco = bruto["fechamento_ajust"].notna().any()
    sem_preco = sorted(com_preco[~com_preco].index)
    validos = sorted(com_preco[com_preco].index)
    rel.append(f"- Removidos por não terem nenhum preço desde 2000: **{len(sem_preco)}**")
    rel.append(f"- Tickers mantidos: **{len(validos)}**\n")
    bruto = {nome: df[validos] for nome, df in bruto.items()}

    # 3) Base diária: fechamento + volume -------------------------------------------
    fech = bruto["fechamento_ajust"]
    vol = bruto["volume_mil"]
    fech.index = pd.to_datetime(fech.index)
    vol.index = pd.to_datetime(vol.index)

    # Linhas inteiramente vazias = feriados / dias sem pregão
    feriados = fech.index[fech.notna().sum(axis=1) == 0]
    fech = fech.drop(index=feriados)
    vol = vol.reindex(fech.index)
    ultima_data = fech.index.max()

    precos = para_longo(fech, "fechamento_ajust").merge(
        para_longo(vol, "volume_mil"), on=["data", "ticker"], how="left"
    )
    # Só guardamos dias em que a ação teve preço
    precos = precos.dropna(subset=["fechamento_ajust"])
    # Preço com volume zero não é negócio real (ex.: ASAI3 em 26/02/2021, "preço" antes da
    # estreia que gerava um falso +386% no dia seguinte). Removemos essas linhas.
    volume_zero = precos["volume_mil"].fillna(0) <= 0
    n_volume_zero = int(volume_zero.sum())
    precos = precos[~volume_zero].sort_values(["ticker", "data"])
    # Retorno em relação ao último preço disponível da mesma ação.
    # Como o preço já é ajustado por proventos, isso é o retorno total (com dividendos).
    precos["retorno"] = precos.groupby("ticker")["fechamento_ajust"].pct_change()
    # Retornos absurdos (ex.: GSHP3 +13.900% por grupamento não ajustado) são marcados,
    # não removidos. A decisão de como tratá-los no backtest está em contexto.md.
    precos["retorno_suspeito"] = precos["retorno"].abs() > LIMITE_RETORNO_SUSPEITO
    precos["ticker"] = precos["ticker"].astype("category")
    precos = precos.reset_index(drop=True)

    suspeitos = precos[precos["retorno_suspeito"]]
    rel += [
        "## Preços diários",
        f"- Período: {fech.index.min():%d/%m/%Y} a {ultima_data:%d/%m/%Y}",
        f"- Dias sem pregão removidos (linhas vazias): **{len(feriados)}**",
        f"- Preços com volume zero/ausente removidos (não são negócios reais): **{n_volume_zero:,}**",
        f"- Observações (data x ticker com preço): **{len(precos):,}**",
        f"- Retornos diários com |r| > {LIMITE_RETORNO_SUSPEITO:.0%} marcados em `retorno_suspeito` "
        f"(NÃO removidos): **{len(suspeitos)}**, sendo **{int((suspeitos['volume_mil'] > 1000).sum())}** "
        f"em dias com volume > R$ 1 mi",
    ]
    if len(suspeitos):
        top = suspeitos.reindex(suspeitos["retorno"].abs().sort_values(ascending=False).index).head(10)
        rel.append("\n| data | ticker | retorno | volume (R$ mil) |\n|---|---|---|---|")
        rel += [f"| {r.data:%d/%m/%Y} | {r.ticker} | {r.retorno:+.0%} | {r.volume_mil:,.0f} |"
                for r in top.itertuples()]
    rel.append("")

    # 4) Base mensal: valor de mercado ---------------------------------------------
    vm = bruto["valor_mercado_mil"]
    vm.index = [converter_mes(m) for m in vm.index]
    vm.index.name = "data"
    vm_preenchido = vm.ffill(limit=FFILL_VALOR_MERCADO_MESES)
    flag_preenchido = vm.isna() & vm_preenchido.notna()
    # O último mês ainda não terminou: a data real do dado é a última data de preço
    vm_preenchido = vm_preenchido.rename(index={vm.index.max(): min(vm.index.max(), ultima_data)})
    flag_preenchido.index = vm_preenchido.index

    valor_mercado = para_longo(vm_preenchido, "valor_mercado_mil").merge(
        para_longo(flag_preenchido, "preenchido"), on=["data", "ticker"]
    )
    valor_mercado = valor_mercado.dropna(subset=["valor_mercado_mil"]).reset_index(drop=True)
    rel += [
        "## Valor de mercado (mensal)",
        f"- Observações: **{len(valor_mercado):,}**",
        f"- Valores carregados do mês anterior (ação sem negócio no fim do mês, até "
        f"{FFILL_VALOR_MERCADO_MESES} meses): **{int(valor_mercado['preenchido'].sum()):,}**",
        "",
    ]

    # 5) Base trimestral: P/L, ROE, Dív/PL ------------------------------------------
    tri = {}
    for nome in ["pl", "roe", "div_pl"]:
        df = bruto[nome]
        df.index = [converter_trimestre(t) for t in df.index]
        tri[nome] = df
    trimestres = sorted(set().union(*[df.index for df in tri.values()]))
    # Descarta trimestres que ainda não terminaram (ex.: 4T2026 do P/L, que é só o P/L de hoje)
    trimestres = [q for q in trimestres if q.end_time.normalize() <= ultima_data]
    for nome in tri:
        tri[nome] = tri[nome].reindex(trimestres)

    fund = None
    for nome, df in tri.items():
        longo = para_longo(df, nome, nome_data="trimestre")
        fund = longo if fund is None else fund.merge(longo, on=["trimestre", "ticker"], how="outer")

    fund["data_referencia"] = fund["trimestre"].apply(lambda q: q.end_time.normalize())
    fund["data_disponivel"] = fund["data_referencia"] + pd.offsets.MonthEnd(DEFASAGEM_BALANCO_MESES)

    # Lucro 12m implícito = valor de mercado no fim do trimestre / P/L.
    # Serve para recalcular o P/L em qualquer data usando só lucro já divulgado
    # (o P/L trimestral do Economatica usa o lucro do próprio trimestre — ver contexto.md).
    vm_fim_tri = vm.copy()
    vm_fim_tri.index = pd.PeriodIndex(vm_fim_tri.index, freq="Q")
    vm_fim_tri = vm_fim_tri.groupby(level=0).last()  # último mês de cada trimestre
    vm_fim_tri = para_longo(vm_fim_tri, "vm_fim_tri", nome_data="trimestre")
    fund = fund.merge(vm_fim_tri, on=["trimestre", "ticker"], how="left")
    fund["lucro_12m_mil"] = np.where(fund["pl"].abs() > 0, fund["vm_fim_tri"] / fund["pl"], np.nan)
    fund = fund.drop(columns="vm_fim_tri")

    # Flags para as armadilhas identificadas
    fund["pl_negativo"] = fund["pl"] < 0                    # empresa com prejuízo
    fund["patrimonio_negativo"] = fund["div_pl"] < 0        # Dív/PL < 0 => PL negativo
    nunca_div_pl = fund.groupby("ticker")["div_pl"].transform(lambda s: s.isna().all())
    tem_roe = fund.groupby("ticker")["roe"].transform(lambda s: s.notna().any())
    fund["provavel_financeira"] = nunca_div_pl & tem_roe     # bancos/seguradoras: sem Dív/PL

    fund = fund.dropna(subset=["pl", "roe", "div_pl"], how="all")
    fund["trimestre"] = fund["trimestre"].astype(str)
    colunas = ["trimestre", "data_referencia", "data_disponivel", "ticker", "pl", "roe", "div_pl",
               "lucro_12m_mil", "pl_negativo", "patrimonio_negativo", "provavel_financeira"]
    fund = fund[colunas].sort_values(["ticker", "data_referencia"]).reset_index(drop=True)

    financeiras = sorted(fund.loc[fund["provavel_financeira"], "ticker"].unique())
    rel += [
        "## Fundamentos (trimestral)",
        f"- Trimestres: {trimestres[0]} a {trimestres[-1]}",
        f"- Observações (trimestre x ticker com algum dado): **{len(fund):,}**",
        f"- Defasagem aplicada: `data_disponivel = fim do trimestre + {DEFASAGEM_BALANCO_MESES} meses`",
        f"- P/L negativo (prejuízo): **{fund['pl_negativo'].mean():.1%}** das observações com P/L",
        f"- Patrimônio líquido negativo (Dív/PL < 0): **{fund['patrimonio_negativo'].sum():,}** observações",
        f"- Prováveis financeiras (têm ROE mas nunca têm Dív/PL): **{len(financeiras)}** tickers",
        "",
        "<details><summary>Lista de prováveis financeiras</summary>\n",
        ", ".join(financeiras),
        "\n</details>\n",
    ]

    # 6) Salvar ---------------------------------------------------------------------
    valor_mercado["ticker"] = valor_mercado["ticker"].astype("category")
    fund["ticker"] = fund["ticker"].astype("category")
    opcoes = {"index": False, "compression": "zstd"}
    precos.to_parquet(OUT / "precos_diarios.parquet", **opcoes)
    valor_mercado.to_parquet(OUT / "valor_mercado_mensal.parquet", **opcoes)
    fund.to_parquet(OUT / "fundamentos_trimestrais.parquet", **opcoes)

    rel += [
        "## Arquivos gerados",
        "| arquivo | linhas | tamanho |",
        "|---|---|---|",
    ]
    for arq in ["precos_diarios", "valor_mercado_mensal", "fundamentos_trimestrais"]:
        p = OUT / f"{arq}.parquet"
        n = len(pd.read_parquet(p))
        rel.append(f"| `{p.name}` | {n:,} | {p.stat().st_size / 1e6:.1f} MB |")

    (OUT / "relatorio_limpeza.md").write_text("\n".join(rel), encoding="utf-8")
    print("\n".join(rel))
    print(f"\nPronto. Arquivos em {OUT}")


if __name__ == "__main__":
    main()
