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
Custo de transação (P16): CUSTO_OPERACAO sobre o giro de cada rebalanceamento, dentro de cada
bloco e na volta a 65/35 (ver backtest.py).

Cada bloco é uma função selecionar(janela, data) -> tickers, que roda no loop de backtest.py.

Uso (a partir da raiz do projeto):
    python src/estrategia.py    # roda a estratégia e imprime as métricas contra o Ibovespa
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial

import pandas as pd

from backtest import (Resultado, calcular_giro, datas_rebalanceamento, descontar_custo,
                      pesos_finais, retornos_buy_and_hold, rodar_backtest)
from dados import Dados, carregar_dados
from fatores import low_vol, lucro_preco, momentum, nota, quality, tamanho, ultimo_balanco
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

# P16: custo sobre o valor negociado, em cada compra e cada venda (exemplo da Aula 3).
# 0 = sem custo (a versão da Entrega 2).
CUSTO_OPERACAO = 0.002


@dataclass
class ResultadoEstrategia:
    carteira: pd.Series   # retorno diário da carteira 65/35, já descontados os custos
    defensivo: Resultado  # retornos, carteiras, giro e custo de cada rebalanceamento do bloco
    agressivo: Resultado  # idem, bloco agressivo
    giro_entre_blocos: pd.Series   # giro da volta a 65/35 em cada trimestre (P10)
    custo_entre_blocos: pd.Series  # custo dessa volta, em fração do valor da carteira


def melhores(valores: pd.Series, fatia: float) -> list[str]:
    """Os tickers com os `fatia` maiores valores (pelo menos 1), ignorando NaN."""
    validos = valores.dropna()
    n = max(1, int(len(validos) * fatia))
    return list(validos.nlargest(n).index)


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------
def elegiveis_defensivo(janela: Dados, tickers: list[str], pl_negativo: str) -> list[str]:
    """Empresas que entram no ranking de Quality + Low Vol: têm ROE, têm Dív/PL no mesmo balanço
    (ou são financeiras, que não têm o indicador: P2), têm Low Vol (12 meses de histórico) e,
    com pl_negativo='excluir', não têm patrimônio líquido negativo (P3).

    As duas notas são calculadas sobre ESTE conjunto. Se cada nota usasse um grupo diferente,
    um percentil de 0,8 em Quality e um de 0,8 em Low Vol não significariam a mesma coisa,
    e a soma deixaria de dar o mesmo peso aos dois fatores."""
    if pl_negativo not in ("excluir", "pior_nota"):
        raise ValueError(f"tratamento de PL negativo desconhecido: {pl_negativo}")
    balanco = ultimo_balanco(janela, tickers)
    tem_div_pl = balanco["div_pl"].notna() | balanco["provavel_financeira"]
    elegivel = balanco["roe"].notna() & tem_div_pl & low_vol(janela, tickers).notna()
    if pl_negativo == "excluir":
        elegivel &= ~balanco["patrimonio_negativo"]
    return list(elegivel[elegivel].index)


def selecionar_defensivo(janela: Dados, data_atual: pd.Timestamp,
                         metodo: str = METODO_NOTA, pl_negativo: str = PL_NEGATIVO) -> list[str]:
    tickers = universo_liquido(janela, data_atual)
    # Primeiro o conjunto elegível; depois as duas notas sobre ele, na mesma régua, e a soma
    elegiveis = elegiveis_defensivo(janela, tickers, pl_negativo)
    combinada = (nota(quality(janela, elegiveis, metodo, pl_negativo), True, metodo)
                 + nota(low_vol(janela, elegiveis), False, metodo))
    candidatas = melhores(combinada, FATIA_QUALITY_LOWVOL)
    return melhores(lucro_preco(janela, candidatas), FATIA_VALUE)


def selecionar_agressivo(janela: Dados, data_atual: pd.Timestamp) -> list[str]:
    tickers = universo_liquido(janela, data_atual)
    pequenas = melhores(-tamanho(janela, tickers), FATIA_SIZE)
    return melhores(momentum(janela, pequenas), FATIA_MOMENTUM)


# ---------------------------------------------------------------------------
# Carteira
# ---------------------------------------------------------------------------
def juntar_blocos(blocos: pd.DataFrame, pesos: pd.Series, datas_rebal: pd.DatetimeIndex,
                  custo_operacao: float = 0.0) -> tuple[pd.Series, pd.Series]:
    """Retorno diário da carteira que volta para `pesos` em cada data de `datas_rebal` e,
    entre elas, deixa cada bloco andar com o próprio retorno (que já desconta o custo interno
    do bloco). Voltar para `pesos` exige vender um bloco e comprar o outro: esse giro também
    paga custo. Devolve os retornos e o giro de cada data."""
    dias = blocos.index
    limites = list(datas_rebal) + [dias.max()]
    # Na primeira data os blocos já nascem nos pesos-alvo: o custo de montar está nos blocos
    pesos_antes = pesos
    pedacos, giros = [], {}
    for inicio, fim in zip(limites[:-1], limites[1:]):
        periodo = blocos.loc[(dias > inicio) & (dias <= fim)]
        giros[inicio] = calcular_giro(pesos_antes, pesos)
        retornos = retornos_buy_and_hold(periodo, pesos)
        pedacos.append(descontar_custo(retornos, giros[inicio] * custo_operacao))
        pesos_antes = pesos_finais(periodo, pesos)
    return pd.concat(pedacos).rename("carteira"), pd.Series(giros, name="giro")


def rodar_estrategia(dados: Dados, metodo: str = METODO_NOTA, pl_negativo: str = PL_NEGATIVO,
                     custo_operacao: float = CUSTO_OPERACAO) -> ResultadoEstrategia:
    trimestral = datas_rebalanceamento(dados.calendario, "Q")
    mensal = datas_rebalanceamento(dados.calendario, "M")
    defensivo = rodar_backtest(dados, trimestral,
                               partial(selecionar_defensivo, metodo=metodo, pl_negativo=pl_negativo),
                               custo_operacao=custo_operacao)
    agressivo = rodar_backtest(dados, mensal, selecionar_agressivo, custo_operacao=custo_operacao)
    blocos = pd.DataFrame({"defensivo": defensivo.retornos, "agressivo": agressivo.retornos})
    pesos = pd.Series({"defensivo": PESO_DEFENSIVO, "agressivo": PESO_AGRESSIVO})
    carteira, giro = juntar_blocos(blocos, pesos, trimestral, custo_operacao)
    return ResultadoEstrategia(carteira=carteira, defensivo=defensivo, agressivo=agressivo,
                               giro_entre_blocos=giro,
                               custo_entre_blocos=(giro * custo_operacao).rename("custo"))


def resumo_giro(res: ResultadoEstrategia) -> pd.DataFrame:
    """Giro e custo de cada bloco e da volta a 65/35. Giro e custo anuais = soma no período
    dividida pelo número de anos (custo em % do valor do próprio bloco)."""
    anos = (res.carteira.index[-1] - res.carteira.index[0]).days / 365.25
    linhas = {}
    for nome, giro, custo in [("Bloco defensivo", res.defensivo.giro, res.defensivo.custo),
                              ("Bloco agressivo", res.agressivo.giro, res.agressivo.custo),
                              ("Volta a 65/35", res.giro_entre_blocos, res.custo_entre_blocos)]:
        linhas[nome] = {"rebalanceamentos": len(giro),
                        "giro médio": giro.iloc[1:].mean(),  # sem a montagem inicial
                        "giro anual": giro.sum() / anos,
                        "custo anual": custo.sum() / anos}
    return pd.DataFrame(linhas).T


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
    print(f"\nPeríodo: {retornos.index[0]:%d/%m/%Y} a {retornos.index[-1]:%d/%m/%Y}"
          f" | custo por operação: {CUSTO_OPERACAO:.2%}")
    print(formatar(resumo(retornos, dados.cdi, benchmark="Ibovespa")).to_string())
    print("\nGiro (soma de |peso novo - peso antigo|) e custo:")
    print(resumo_giro(res).to_string(formatters={
        "rebalanceamentos": "{:.0f}".format, "giro médio": "{:.0%}".format,
        "giro anual": "{:.0%}".format, "custo anual": "{:.2%}".format}))


if __name__ == "__main__":
    main()
