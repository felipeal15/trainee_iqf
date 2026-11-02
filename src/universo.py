"""
universo.py — Quais ações podem entrar na carteira em cada rebalanceamento (P1 do contexto.md).

Não temos a composição histórica do Ibovespa. Aproximamos pelos critérios do próprio índice:
as N ações com maior volume financeiro médio nos últimos 3 meses, desde que tenham negociado
em quase todos os pregões. Como só usa dado até a data do rebalanceamento e a base inclui
ações canceladas, não há viés de sobrevivência.

Uso (com src/ no path):
    from universo import universo_liquido
    tickers = universo_liquido(janela, data_atual)
"""

from __future__ import annotations

import pandas as pd

from dados import Dados

# ---------------------------------------------------------------------------
# Configuração (P1 do contexto.md)
# ---------------------------------------------------------------------------
N_ATIVOS = 90                               # ~ número de ativos do Ibovespa
JANELA_LIQUIDEZ = pd.DateOffset(months=3)
PRESENCA_MINIMA = 0.90                      # negociada em pelo menos 90% dos pregões da janela


def empresa(ticker: str) -> str:
    """'PETR4' -> 'PETR'. Na B3, as 4 letras identificam a empresa e o número, a classe."""
    return ticker[:4]


def universo_liquido(janela: Dados, data_atual: pd.Timestamp) -> list[str]:
    """Tickers elegíveis em data_atual, com uma classe por empresa."""
    vol = janela.volume.loc[janela.volume.index > data_atual - JANELA_LIQUIDEZ]
    presenca = vol.notna().mean()
    volume_medio = vol.fillna(0).mean()  # dia sem negócio conta como volume zero
    top = volume_medio[presenca >= PRESENCA_MINIMA].nlargest(N_ATIVOS)
    # Uma classe por empresa (a mais líquida). Valor de mercado e fundamentos são da empresa:
    # com PETR3 e PETR4 juntas, a Petrobras contaria duas vezes nos rankings e na carteira.
    mais_liquida = top.groupby(top.index.map(empresa)).idxmax()
    return sorted(mais_liquida)
