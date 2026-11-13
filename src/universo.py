"""
universo.py — Quais ações podem entrar na carteira em cada rebalanceamento (P1 do contexto.md).

Não temos a composição histórica do Ibovespa. Aproximamos pelos critérios do próprio índice:
as N ações com maior volume financeiro médio nos últimos 3 meses, desde que tenham negociado
em quase todos os pregões. O filtro só usa dado até a data do rebalanceamento, então não
introduz look-ahead. O viés de sobrevivência não depende deste filtro, e sim da base: desde
13/11/2026 ela inclui as ações canceladas (P11), então empresas que quebraram, fecharam o
capital ou foram compradas entram no universo enquanto negociavam.
Uma classe por empresa, identificada pelas 4 letras do ticker ou pelo valor de mercado (P17).

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


def identificar_empresas(tickers: list[str], valor_mercado: pd.Series) -> pd.Series:
    """ticker -> identificador da empresa (P17). Dois tickers são da mesma empresa se têm as
    mesmas 4 letras (PETR3/PETR4) OU o mesmo valor de mercado na data: o Economatica dá o valor
    de mercado da EMPRESA, igual em todas as classes. O segundo critério pega troca de código,
    como AMBV4 -> ABEV3 (Ambev, 2013), que nas 4 letras pareceriam empresas diferentes."""
    grupo = {t: t for t in tickers}  # cada ticker aponta para um representante do grupo

    def raiz(t: str) -> str:
        while grupo[t] != t:
            t = grupo[t]
        return t

    prefixo = pd.Series(tickers, index=tickers).map(empresa)
    vm = valor_mercado.reindex(tickers).dropna()  # sem valor de mercado: vale só o prefixo
    for chave in (prefixo, vm):
        for _, membros in chave.groupby(chave):
            for t in membros.index[1:]:
                grupo[raiz(t)] = raiz(membros.index[0])
    return pd.Series({t: raiz(t) for t in tickers})


def universo_liquido(janela: Dados, data_atual: pd.Timestamp) -> list[str]:
    """Tickers elegíveis em data_atual, com uma classe por empresa."""
    vol = janela.volume.loc[janela.volume.index > data_atual - JANELA_LIQUIDEZ]
    presenca = vol.notna().mean()
    volume_medio = vol.fillna(0).mean()  # dia sem negócio conta como volume zero
    top = volume_medio[presenca >= PRESENCA_MINIMA].nlargest(N_ATIVOS)
    # Uma classe por empresa (a mais líquida). Valor de mercado e fundamentos são da empresa:
    # com PETR3 e PETR4 juntas, a Petrobras contaria duas vezes nos rankings e na carteira.
    valor_mercado = janela.valor_mercado.reindex(columns=top.index).iloc[-1]
    mais_liquida = top.groupby(identificar_empresas(list(top.index), valor_mercado)).idxmax()
    return sorted(mais_liquida)
