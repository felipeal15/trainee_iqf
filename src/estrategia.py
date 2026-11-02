"""
estrategia.py — A estratégia da Entrega 1: bloco defensivo (65%) + bloco agressivo (35%).

Bloco defensivo, rebalanceado a cada trimestre:
    1. nota combinada = Quality (ROE alto, dívida baixa) + Low Vol
    2. ficam as 30% melhores pela nota combinada
    3. entre elas, ficam as 50% mais baratas (maior L/P)
Bloco agressivo, rebalanceado todo mês:
    1. Size: as 30% menores por valor de mercado
    2. entre elas, as 30% com maior Momentum 12-1
Peso igual dentro de cada bloco. A carteira volta para 65/35 a cada trimestre (P10) e,
entre um trimestre e outro, os pesos dos blocos andam com o mercado.

Cada bloco é uma função selecionar(janela, data) -> tickers, que roda no loop de backtest.py.

Uso (a partir da raiz do projeto):
    python src/estrategia.py    # roda a estratégia e imprime as métricas contra o Ibovespa
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial

import pandas as pd

from backtest import Resultado, datas_rebalanceamento, rodar_backtest, retornos_buy_and_hold
from dados import Dados, carregar_dados
from fatores import low_vol, lucro_preco, momentum, nota, quality, tamanho
from metricas import formatar, resumo
from universo import universo_liquido

# ---------------------------------------------------------------------------
# Parâmetros (Entrega 1)
# ---------------------------------------------------------------------------
PESO_DEFENSIVO = 0.65
PESO_AGRESSIVO = 0.35
FATIA_QUALITY_LOWVOL = 0.30  # defensivo, passo 1: as 30% melhores pela nota combinada
FATIA_VALUE = 0.50           # defensivo, passo 2: as 50% mais baratas entre elas
FATIA_SIZE = 0.30            # agressivo, passo 1: as 30% menores
FATIA_MOMENTUM = 0.30        # agressivo, passo 2: as 30% com maior momentum entre elas

# Escolhas testadas no notebook (ver contexto.md). Estes são os valores padrão.
METODO_NOTA = "rank"   # "rank" (percentil) ou "zscore"
PL_NEGATIVO = "excluir"  # P3: "excluir" ou "pior_nota"


@dataclass
class ResultadoEstrategia:
    carteira: pd.Series   # retorno diário da carteira 65/35
    defensivo: Resultado  # retornos e carteiras de cada rebalanceamento do bloco defensivo
    agressivo: Resultado  # idem, bloco agressivo


def melhores(valores: pd.Series, fatia: float) -> list[str]:
    """Os tickers com os `fatia` maiores valores (pelo menos 1), ignorando NaN."""
    validos = valores.dropna()
    n = max(1, int(len(validos) * fatia))
    return list(validos.nlargest(n).index)


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------
def selecionar_defensivo(janela: Dados, data_atual: pd.Timestamp,
                         metodo: str = METODO_NOTA, pl_negativo: str = PL_NEGATIVO) -> list[str]:
    tickers = universo_liquido(janela, data_atual)
    # Quality e Low Vol viram nota na mesma escala antes de somar, para nenhuma dominar
    combinada = (nota(quality(janela, tickers, metodo, pl_negativo), True, metodo)
                 + nota(low_vol(janela, tickers), False, metodo))
    candidatas = melhores(combinada, FATIA_QUALITY_LOWVOL)
    return melhores(lucro_preco(janela, candidatas), FATIA_VALUE)


def selecionar_agressivo(janela: Dados, data_atual: pd.Timestamp) -> list[str]:
    tickers = universo_liquido(janela, data_atual)
    pequenas = melhores(-tamanho(janela, tickers), FATIA_SIZE)
    return melhores(momentum(janela, pequenas), FATIA_MOMENTUM)


# ---------------------------------------------------------------------------
# Carteira
# ---------------------------------------------------------------------------
def juntar_blocos(blocos: pd.DataFrame, pesos: pd.Series,
                  datas_rebal: pd.DatetimeIndex) -> pd.Series:
    """Retorno diário da carteira que volta para `pesos` em cada data de `datas_rebal` e,
    entre elas, deixa cada bloco andar com o próprio retorno."""
    dias = blocos.index
    limites = list(datas_rebal) + [dias.max()]
    pedacos = [retornos_buy_and_hold(blocos.loc[(dias > inicio) & (dias <= fim)], pesos)
               for inicio, fim in zip(limites[:-1], limites[1:])]
    return pd.concat(pedacos).rename("carteira")


def rodar_estrategia(dados: Dados, metodo: str = METODO_NOTA,
                     pl_negativo: str = PL_NEGATIVO) -> ResultadoEstrategia:
    trimestral = datas_rebalanceamento(dados.calendario, "Q")
    mensal = datas_rebalanceamento(dados.calendario, "M")
    defensivo = rodar_backtest(dados, trimestral,
                               partial(selecionar_defensivo, metodo=metodo, pl_negativo=pl_negativo))
    agressivo = rodar_backtest(dados, mensal, selecionar_agressivo)
    blocos = pd.DataFrame({"defensivo": defensivo.retornos, "agressivo": agressivo.retornos})
    pesos = pd.Series({"defensivo": PESO_DEFENSIVO, "agressivo": PESO_AGRESSIVO})
    return ResultadoEstrategia(carteira=juntar_blocos(blocos, pesos, trimestral),
                               defensivo=defensivo, agressivo=agressivo)


def main() -> None:
    print("Carregando dados...")
    dados = carregar_dados()
    print("Rodando a estratégia...")
    res = rodar_estrategia(dados)
    retornos = pd.DataFrame({
        "Estratégia 65/35": res.carteira,
        "Bloco defensivo": res.defensivo.retornos,
        "Bloco agressivo": res.agressivo.retornos,
        "Ibovespa": dados.ibov.reindex(res.carteira.index),
    })
    print(f"\nPeríodo: {retornos.index[0]:%d/%m/%Y} a {retornos.index[-1]:%d/%m/%Y}")
    print(formatar(resumo(retornos, dados.cdi, benchmark="Ibovespa")).to_string())


if __name__ == "__main__":
    main()
