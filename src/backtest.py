"""
backtest.py — Loop do backtest da Aula 2 para uma carteira de peso igual.

    Parâmetros: rebalanceamento, lookback, data de início e de fim
    Para cada data de rebalanceamento t:
        1. recorta as bases para (t - lookback, t]                 -> Dados.janela
        2. a lógica da estratégia devolve a lista de tickers       -> selecionar(janela, t)
        3. compra peso igual no fechamento de t e segura até o próximo rebalanceamento
        4. guarda os retornos diários da carteira
    Saída: série de retornos diários da carteira (entrada de metricas.py)

A lógica da estratégia entra como uma função selecionar(janela, data_atual) -> list[str].
O mesmo loop serve para o bloco defensivo, para o agressivo e para testes.

Hipóteses da primeira versão:
    - Sinal e operação no fechamento do mesmo pregão (t), sem custo de transação (P9).
    - Dia sem negócio, ou ação que saiu da bolsa, conta como retorno zero: a posição fica
      parada no último preço até o próximo rebalanceamento.

Uso (a partir da raiz do projeto):
    python src/backtest.py      # teste de sanidade: peso igual no universo x Ibovespa
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from dados import Dados, carregar_dados
from universo import universo_liquido

# ---------------------------------------------------------------------------
# Parâmetros (Aula 2)
# ---------------------------------------------------------------------------
# P6: primeiro dia com retorno. A carteira é montada no último pregão anterior a essa data.
INICIO = pd.Timestamp("2011-01-01")
FIM = None  # None = última data da base
# Histórico que a lógica da estratégia enxerga em cada rebalanceamento. 13 meses cobrem com
# folga Momentum 12-1 e Low Vol (252 pregões) e incluem o último balanço divulgado.
LOOKBACK = pd.DateOffset(months=13)

Selecionar = Callable[[Dados, pd.Timestamp], list[str]]


@dataclass
class Resultado:
    retornos: pd.Series                       # retorno diário da carteira
    carteiras: dict[pd.Timestamp, list[str]]  # tickers escolhidos em cada rebalanceamento


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------
def datas_rebalanceamento(calendario: pd.DatetimeIndex, frequencia: str,
                          inicio: pd.Timestamp = INICIO,
                          fim: pd.Timestamp | None = FIM) -> pd.DatetimeIndex:
    """P7: último pregão de cada mês (frequencia='M') ou trimestre ('Q').
    A primeira data é o último fim de período antes de `inicio`."""
    fim = calendario.max() if fim is None else fim
    pregoes = pd.Series(calendario, index=calendario)
    ultimo_pregao = pregoes.groupby(calendario.to_period(frequencia)).max()
    # Descarta o período em andamento: o último pregão dele ainda não aconteceu
    ultimo_pregao = ultimo_pregao[ultimo_pregao.index.end_time.normalize() <= calendario.max()]
    primeira = ultimo_pregao[ultimo_pregao < inicio].iloc[-1]
    datas = ultimo_pregao[(ultimo_pregao >= primeira) & (ultimo_pregao < fim)]
    return pd.DatetimeIndex(datas.values)


def retornos_buy_and_hold(retornos: pd.DataFrame, tickers: list[str]) -> pd.Series:
    """Retorno diário de uma carteira que compra peso igual em `tickers` no início do período
    e não mexe mais. Os pesos andam com os preços (quem sobe passa a pesar mais), como numa
    carteira real entre dois rebalanceamentos."""
    r = retornos.reindex(columns=tickers).fillna(0.0)
    valor = (1 + r).cumprod().mean(axis=1)  # valor da carteira, começando em 1
    return valor.pct_change().fillna(valor.iloc[0] - 1)


def rodar_backtest(dados: Dados, datas_rebal: pd.DatetimeIndex, selecionar: Selecionar,
                   lookback: pd.DateOffset = LOOKBACK,
                   fim: pd.Timestamp | None = FIM) -> Resultado:
    fim = dados.calendario.max() if fim is None else fim
    limites = list(datas_rebal) + [fim]
    pedacos, carteiras = [], {}
    for data_atual, data_prox_rebal in zip(limites[:-1], limites[1:]):
        janela = dados.janela(data_atual, lookback)
        tickers = selecionar(janela, data_atual)
        if not tickers:
            raise ValueError(f"{data_atual:%d/%m/%Y}: a estratégia não selecionou nenhuma ação")
        carteiras[data_atual] = tickers
        # Compra no fechamento de data_atual: os retornos contam a partir do pregão seguinte
        dias = dados.calendario
        periodo = dados.retorno.loc[(dias > data_atual) & (dias <= data_prox_rebal)]
        pedacos.append(retornos_buy_and_hold(periodo, tickers))
    return Resultado(retornos=pd.concat(pedacos).rename("carteira"), carteiras=carteiras)


# ---------------------------------------------------------------------------
# Teste de sanidade
# ---------------------------------------------------------------------------
def main() -> None:
    print("Carregando dados...")
    dados = carregar_dados()
    datas = datas_rebalanceamento(dados.calendario, "M")
    print(f"{len(datas)} rebalanceamentos mensais, de {datas[0]:%d/%m/%Y} a {datas[-1]:%d/%m/%Y}")

    # Peso igual em todo o universo líquido. NÃO é a estratégia: serve para validar dados e loop.
    # Deve andar perto do Ibovespa (correlação alta, beta perto de 1). Se não andar, o problema
    # está nos dados ou no motor, e não na lógica dos fatores.
    res = rodar_backtest(dados, datas, universo_liquido)
    tabela = pd.DataFrame({"Universo peso igual": res.retornos,
                           "Ibovespa": dados.ibov.reindex(res.retornos.index)})

    anos = len(tabela) / 252
    acumulado = (1 + tabela).prod() - 1
    resumo = pd.DataFrame({
        "retorno acumulado": acumulado,
        "CAGR": (1 + acumulado) ** (1 / anos) - 1,
        "volatilidade": tabela.std() * np.sqrt(252),
    })
    cov = tabela.cov()
    beta = cov.iloc[0, 1] / cov.iloc[1, 1]
    n_acoes = pd.Series({d: len(t) for d, t in res.carteiras.items()})

    print(f"\nPeríodo: {tabela.index[0]:%d/%m/%Y} a {tabela.index[-1]:%d/%m/%Y} ({anos:.1f} anos)")
    print(resumo.to_string(float_format="{:.1%}".format))
    print(f"\nCorrelação diária com o Ibovespa: {tabela.corr().iloc[0, 1]:.2f} | beta: {beta:.2f}")
    print(f"Ações no universo: mín {n_acoes.min()}, média {n_acoes.mean():.0f}, máx {n_acoes.max()}")


if __name__ == "__main__":
    main()
