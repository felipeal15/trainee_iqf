"""
dados.py — Carrega as bases limpas e o benchmark no formato que o backtest usa.

Entrada (data/processed/):
    precos_diarios.parquet          gerado por limpeza.py
    valor_mercado_mensal.parquet    gerado por limpeza.py
    fundamentos_trimestrais.parquet gerado por limpeza.py
    benchmark_diario.parquet        Ibovespa (yfinance ^BVSP) e CDI (BCB, SGS 12).
                                    Baixado na primeira execução e guardado.

Saída: um objeto Dados com as bases de mercado no formato LARGO (linhas = datas,
colunas = tickers), que é o mais prático para o loop do backtest.

Uso (com src/ no path):
    from dados import carregar_dados
    dados = carregar_dados()
    janela = dados.janela(data_atual, lookback)   # só o que era conhecido em data_atual

As decisões por trás de cada tratamento estão em contexto.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"
ARQ_BENCHMARK = PROCESSED / "benchmark_diario.parquet"

TICKER_IBOV = "^BVSP"  # Ibovespa já é índice de retorno total (reinveste dividendos)
SERIE_CDI = 12         # SGS/BCB: taxa DI diária, em % ao dia
URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
# A API do BCB só aceita janelas de até 10 anos para séries diárias
JANELA_SGS_ANOS = 10


# ---------------------------------------------------------------------------
# Estrutura
# ---------------------------------------------------------------------------
@dataclass
class Dados:
    retorno: pd.DataFrame        # diário, datas x tickers. NaN = ação sem negócio no dia
    volume: pd.DataFrame         # diário, em R$ mil. NaN = ação sem negócio no dia
    valor_mercado: pd.DataFrame  # mensal, em R$ mil, valor de mercado da EMPRESA
    fundamentos: pd.DataFrame    # longo, uma linha por trimestre x ticker (ver limpeza.py)
    ibov: pd.Series              # retorno diário do Ibovespa
    cdi: pd.Series               # retorno diário do CDI

    @property
    def calendario(self) -> pd.DatetimeIndex:
        """Dias de pregão da base."""
        return self.retorno.index

    def janela(self, data_atual: pd.Timestamp, lookback: pd.DateOffset) -> Dados:
        """Recorta todas as bases para (data_atual - lookback, data_atual].

        É o passo "Filtrar database para o período desejado" do loop da Aula 2. A lógica da
        estratégia só recebe esse recorte, o que impede por construção o uso de dado do futuro.
        Fundamentos entram pela data em que foram divulgados (data_disponivel), não pela
        data do balanço.
        """
        inicio = data_atual - lookback

        def corta(x):
            return x.loc[(x.index > inicio) & (x.index <= data_atual)]

        disponivel = self.fundamentos["data_disponivel"]
        return Dados(
            retorno=corta(self.retorno),
            volume=corta(self.volume),
            valor_mercado=corta(self.valor_mercado),
            fundamentos=self.fundamentos[(disponivel > inicio) & (disponivel <= data_atual)],
            ibov=corta(self.ibov),
            cdi=corta(self.cdi),
        )


# ---------------------------------------------------------------------------
# Benchmark: Ibovespa e CDI
# ---------------------------------------------------------------------------
def baixar_benchmark(inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Fechamento do Ibovespa e taxa diária do CDI (decimal), uma linha por data."""
    ibov = yf.download(TICKER_IBOV, start=inicio, end=fim + pd.Timedelta(days=1),
                       auto_adjust=True, progress=False)["Close"][TICKER_IBOV]

    partes = []
    for ano in range(inicio.year, fim.year + 1, JANELA_SGS_ANOS):
        de = max(inicio, pd.Timestamp(year=ano, month=1, day=1))
        ate = min(fim, pd.Timestamp(year=ano + JANELA_SGS_ANOS - 1, month=12, day=31))
        resp = requests.get(URL_SGS.format(serie=SERIE_CDI), timeout=60, params={
            "formato": "json", "dataInicial": f"{de:%d/%m/%Y}", "dataFinal": f"{ate:%d/%m/%Y}"})
        resp.raise_for_status()
        partes.append(pd.DataFrame(resp.json()))
    cdi = pd.concat(partes)
    cdi = pd.Series(cdi["valor"].astype(float).values / 100,
                    index=pd.to_datetime(cdi["data"], format="%d/%m/%Y"))

    bench = pd.DataFrame({"ibov": ibov, "cdi": cdi})
    bench.index.name = "data"
    return bench.reset_index()


def carregar_benchmark(inicio: pd.Timestamp, fim: pd.Timestamp,
                       atualizar: bool = False) -> pd.DataFrame:
    """Lê o benchmark salvo. Baixa de novo se o arquivo não existir, se não cobrir até `fim`
    ou se `atualizar=True`."""
    if ARQ_BENCHMARK.exists() and not atualizar:
        bench = pd.read_parquet(ARQ_BENCHMARK)
        if bench["data"].max() >= fim:
            return bench.set_index("data")
    print("Baixando Ibovespa (yfinance) e CDI (Banco Central)...")
    bench = baixar_benchmark(inicio, fim)
    bench.to_parquet(ARQ_BENCHMARK, index=False, compression="zstd")
    return bench.set_index("data")


def retorno_no_calendario(indice: pd.Series, calendario: pd.DatetimeIndex) -> pd.Series:
    """Retorno diário de um índice nos pregões da base. Se o índice não tem valor em algum
    pregão, carrega o último valor (o retorno daquele dia é zero e o seguinte compensa)."""
    return indice.dropna().reindex(calendario, method="ffill").pct_change()


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------
def carregar_dados(atualizar_benchmark: bool = False) -> Dados:
    precos = pd.read_parquet(PROCESSED / "precos_diarios.parquet")
    precos["ticker"] = precos["ticker"].astype(str)
    # P5: retorno marcado como suspeito (> +100% em um dia, quase sempre erro de ajuste do
    # Economatica) vira 0. Conservador: pode cortar um ganho real raro, mas impede ganho falso.
    precos.loc[precos["retorno_suspeito"], "retorno"] = 0.0
    retorno = precos.pivot(index="data", columns="ticker", values="retorno")
    volume = precos.pivot(index="data", columns="ticker", values="volume_mil")

    vm = pd.read_parquet(PROCESSED / "valor_mercado_mensal.parquet")
    vm["ticker"] = vm["ticker"].astype(str)
    valor_mercado = vm.pivot(index="data", columns="ticker", values="valor_mercado_mil")

    fundamentos = pd.read_parquet(PROCESSED / "fundamentos_trimestrais.parquet")
    fundamentos["ticker"] = fundamentos["ticker"].astype(str)

    calendario = retorno.index
    bench = carregar_benchmark(calendario.min(), calendario.max(), atualizar_benchmark)
    # CDI vira um índice acumulado antes de ir para o calendário da B3, para não perder
    # nem duplicar dias quando os calendários do BCB e da bolsa não batem
    cdi_acumulado = (1 + bench["cdi"].dropna()).cumprod()

    return Dados(
        retorno=retorno,
        volume=volume,
        valor_mercado=valor_mercado,
        fundamentos=fundamentos,
        ibov=retorno_no_calendario(bench["ibov"], calendario).rename("ibov"),
        cdi=retorno_no_calendario(cdi_acumulado, calendario).rename("cdi"),
    )


if __name__ == "__main__":
    d = carregar_dados()
    print(f"Pregões: {len(d.calendario):,} ({d.calendario.min():%d/%m/%Y} a "
          f"{d.calendario.max():%d/%m/%Y}) | tickers: {d.retorno.shape[1]}")
    print(f"Valor de mercado: {d.valor_mercado.shape[0]} meses | "
          f"fundamentos: {len(d.fundamentos):,} linhas")
    print(f"Ibovespa: {d.ibov.notna().sum():,} dias | CDI: {d.cdi.notna().sum():,} dias")
