"""
fatores.py — Métrica de cada fator numa data de rebalanceamento, e como virar nota.

Todas as funções recebem a `janela` (as bases recortadas até a data, ver dados.py) e uma lista
de tickers, e devolvem uma Series indexada por ticker. NaN = sem dado suficiente: a ação fica
fora do ranking daquele fator.

| Fator    | Métrica                                                    | Melhor |
|----------|------------------------------------------------------------|--------|
| Low Vol  | desvio-padrão dos retornos diários de 12 meses, anualizado | menor  |
| Momentum | retorno de t-252 a t-21 pregões (12 meses sem o último)    | maior  |
| Size     | valor de mercado da empresa                                | menor  |
| Value    | L/P = último lucro 12m divulgado / valor de mercado atual  | maior  |
| Quality  | ROE (maior) e Dívida Bruta / PL (menor)                    | —      |

As fórmulas e as decisões P2, P3 e P4 estão em contexto.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dados import Dados

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
PREGOES_ANO = 252
PREGOES_MES = 21
# Low Vol e Momentum só valem com histórico: a ação precisa ter negociado em pelo menos 80%
# dos últimos 252 pregões (uma estreia recente não tem 12 meses de retorno)
HISTORICO_MINIMO = 0.8
# Janela dos fatores de preço (Low Vol e Momentum), em pregões: 12 meses. Só muda no teste de
# robustez (P20, robustez.py); o Momentum sempre pula o último mês (12-1, 9-1, 6-1).
JANELA_FATORES_PRECO = PREGOES_ANO
# No z-score, valores além de 3 desvios são cortados (ROE de 300%, Dív/PL de 5.000%)
LIMITE_ZSCORE = 3.0


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def _retornos_12m(janela: Dados, tickers: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Últimos JANELA_FATORES_PRECO retornos diários (252 = 12 meses) e se a ação tem
    histórico suficiente."""
    r = janela.retorno.reindex(columns=tickers).iloc[-JANELA_FATORES_PRECO:]
    tem_historico = r.notna().sum() >= HISTORICO_MINIMO * JANELA_FATORES_PRECO
    return r, tem_historico


def low_vol(janela: Dados, tickers: list[str]) -> pd.Series:
    r, tem_historico = _retornos_12m(janela, tickers)
    return (r.std() * np.sqrt(PREGOES_ANO)).where(tem_historico)


def momentum(janela: Dados, tickers: list[str]) -> pd.Series:
    """MOM = P(t-21) / P(t-252) - 1, montado a partir dos retornos diários, para que um
    retorno suspeito zerado em dados.py (P5) também não entre aqui."""
    r, tem_historico = _retornos_12m(janela, tickers)
    sem_ultimo_mes = r.iloc[:-PREGOES_MES].fillna(0.0)  # dia sem negócio: preço parado
    return ((1 + sem_ultimo_mes).prod() - 1).where(tem_historico)


def tamanho(janela: Dados, tickers: list[str]) -> pd.Series:
    """Valor de mercado da empresa no mês mais recente da janela, em R$ mil."""
    return janela.valor_mercado.reindex(columns=tickers).iloc[-1]


def _ultima_linha_com(f: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """A linha inteira do balanço mais recente de cada ticker em que `coluna` existe.
    (groupby().last() não serve: ele pula NaN coluna por coluna e mistura trimestres.)"""
    return (f.dropna(subset=[coluna]).sort_values("data_referencia")
            .drop_duplicates("ticker", keep="last").set_index("ticker"))


def ultimo_balanco(janela: Dados, tickers: list[str]) -> pd.DataFrame:
    """Último dado já divulgado de cada ticker.

    roe e div_pl vêm do MESMO balanço: o mais recente em que o ROE existe. Se o Dív/PL estiver
    vazio nesse balanço, fica vazio (não é buscado em outro trimestre). As duas métricas do
    Quality descrevem a empresa na mesma data.
    patrimonio_negativo (P3) vem do balanço mais recente com Dív/PL, mesmo sem ROE: o
    Economatica não calcula ROE com PL negativo, então o balanço "com ROE" é sempre de antes
    de o PL ficar negativo e esconderia essa informação.
    lucro_12m_mil é o último lucro divulgado, buscado à parte: o Value (L/P) combina o lucro
    mais recente conhecido com o valor de mercado de hoje e não depende do ROE.
    provavel_financeira (banco/seguradora, P2) é fixa por ticker."""
    f = janela.fundamentos[janela.fundamentos["ticker"].isin(tickers)]
    quality = _ultima_linha_com(f, "roe")[["roe", "div_pl"]]
    lucro = _ultima_linha_com(f, "lucro_12m_mil")["lucro_12m_mil"]
    balanco = quality.join(lucro, how="outer").reindex(tickers)
    patrimonio_negativo = _ultima_linha_com(f, "div_pl")["patrimonio_negativo"]
    balanco["patrimonio_negativo"] = patrimonio_negativo.reindex(tickers, fill_value=False).astype(bool)
    financeira = f.groupby("ticker")["provavel_financeira"].any()
    balanco["provavel_financeira"] = financeira.reindex(tickers, fill_value=False).astype(bool)
    return balanco


def lucro_preco(janela: Dados, tickers: list[str]) -> pd.Series:
    """L/P com o último lucro divulgado e o valor de mercado de hoje (ver "Descoberta sobre
    o P/L" no contexto.md). P4: empresa com prejuízo tem L/P negativo e vai para o fim da fila."""
    return ultimo_balanco(janela, tickers)["lucro_12m_mil"] / tamanho(janela, tickers)


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------
def nota(valores: pd.Series, maior_melhor: bool, metodo: str) -> pd.Series:
    """Transforma uma métrica em nota comparável entre fatores (quanto maior, melhor).
        'rank'   : percentil de 0 a 1 dentro do grupo
        'zscore' : (x - média) / desvio, cortado em ±LIMITE_ZSCORE
    NaN continua NaN."""
    x = valores if maior_melhor else -valores
    if metodo == "rank":
        return x.rank(pct=True)
    if metodo == "zscore":
        return ((x - x.mean()) / x.std()).clip(-LIMITE_ZSCORE, LIMITE_ZSCORE)
    raise ValueError(f"método de nota desconhecido: {metodo}")


def quality(janela: Dados, tickers: list[str], metodo: str, pl_negativo: str) -> pd.Series:
    """Nota de Quality = média das notas de ROE (alto) e Dív/PL (baixo).

    P2: bancos e seguradoras não têm Dív/PL. Recebem a nota mediana nesse componente, sem
        prêmio nem punição. Empresa NÃO financeira sem Dív/PL fica sem nota de Quality
        (dado faltando, não setor sem o indicador), e elegiveis_defensivo a deixa de fora.
    P3: com patrimônio líquido negativo, o Dív/PL fica negativo (pareceria a menor dívida de
        todas) e o ROE troca de sinal. pl_negativo = 'excluir' tira a empresa do ranking;
        'pior_nota' a mantém com a pior nota de Quality.
    """
    balanco = ultimo_balanco(janela, tickers)
    negativo = balanco["patrimonio_negativo"]
    validas = balanco[~negativo]  # o ranking é feito só entre empresas com PL positivo
    nota_div = nota(validas["div_pl"], maior_melhor=False, metodo=metodo)
    financeira_sem_div = validas["provavel_financeira"] & validas["div_pl"].isna()
    nota_div[financeira_sem_div] = nota_div.median()  # P2: só financeira ganha a mediana
    nota_quality = (nota(validas["roe"], maior_melhor=True, metodo=metodo) + nota_div) / 2
    nota_quality = nota_quality.reindex(tickers)
    if pl_negativo == "pior_nota":
        nota_quality[negativo] = nota_quality.min()
    elif pl_negativo != "excluir":
        raise ValueError(f"tratamento de PL negativo desconhecido: {pl_negativo}")
    return nota_quality
