"""
metricas.py — Métricas de avaliação da Aula 2, calculadas na mão.

Todas recebem retornos DIÁRIOS com a data no índice, como os que o backtest devolve.

| Métrica           | Conta                                                                 |
|-------------------|-----------------------------------------------------------------------|
| Retorno acumulado | prod(1 + r) - 1                                                       |
| CAGR              | (1 + acumulado) ** (1 / anos) - 1, com anos = dias corridos / 365,25  |
| Volatilidade      | desvio-padrão diário x raiz(252)                                      |
| Sharpe            | média do retorno acima do CDI / desvio-padrão dele, x raiz(252)       |
| Max drawdown      | maior queda do topo até o fundo                                       |
| Beta              | cov(carteira, benchmark) / var(benchmark)                             |
| Alpha             | retorno anual acima do CDI que o beta não explica (alpha de Jensen)   |
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PREGOES_ANO = 252

# Como exibir cada linha da tabela de resumo
FORMATOS = {
    "Retorno acumulado": "{:.1%}",
    "CAGR": "{:.2%}",
    "Volatilidade (anual)": "{:.1%}",
    "Sharpe (CDI)": "{:.2f}",
    "Max drawdown": "{:.1%}",
    "Maior drawdown (dias)": "{:.0f}",
    "Beta": "{:.2f}",
    "Alpha (anual)": "{:.2%}",
    "Correlação": "{:.2f}",
}


def curva(retornos: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Quanto vale R$ 1 investido no início."""
    return (1 + retornos).cumprod()


def drawdown(retornos: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Quanto a carteira está abaixo do maior valor que já atingiu (0 = no topo).
    O topo começa em 1, o capital inicial, para contar uma queda logo no primeiro dia."""
    c = curva(retornos)
    return c / c.cummax().clip(lower=1.0) - 1


def cagr(retornos: pd.Series) -> float:
    anos = (retornos.index[-1] - retornos.index[0]).days / 365.25
    return (1 + retornos).prod() ** (1 / anos) - 1


def periodos_drawdown(retornos: pd.Series) -> pd.DataFrame:
    """Cada período abaixo do topo: data do topo, do fundo e da recuperação (vazia se ainda
    não recuperou), queda máxima e duração em dias corridos. Ordenado da pior queda para a menor."""
    dd = drawdown(retornos)
    abaixo = dd < 0
    id_periodo = (~abaixo).cumsum()  # fica constante enquanto a carteira está abaixo do topo
    linhas = []
    for _, d in dd[abaixo].groupby(id_periodo[abaixo]):
        pos_inicio = dd.index.get_loc(d.index[0])
        pos_fim = dd.index.get_loc(d.index[-1])
        topo = dd.index[max(pos_inicio - 1, 0)]
        recuperacao = dd.index[pos_fim + 1] if pos_fim + 1 < len(dd) else pd.NaT
        ate = dd.index[-1] if pd.isna(recuperacao) else recuperacao
        linhas.append({"topo": topo, "fundo": d.idxmin(), "recuperação": recuperacao,
                       "queda": d.min(), "dias": (ate - topo).days})
    colunas = ["topo", "fundo", "recuperação", "queda", "dias"]
    return pd.DataFrame(linhas, columns=colunas).sort_values("queda").reset_index(drop=True)


def resumo(retornos: pd.DataFrame, cdi: pd.Series, benchmark: str) -> pd.DataFrame:
    """Tabela de métricas, uma coluna por série. `benchmark` é o nome da coluna usada no
    beta, no alpha e na correlação."""
    cdi = cdi.reindex(retornos.index)
    excesso_bench = retornos[benchmark] - cdi
    tabela = {}
    for nome, r in retornos.items():
        excesso = r - cdi
        beta = r.cov(retornos[benchmark]) / retornos[benchmark].var()
        tabela[nome] = {
            "Retorno acumulado": (1 + r).prod() - 1,
            "CAGR": cagr(r),
            "Volatilidade (anual)": r.std() * np.sqrt(PREGOES_ANO),
            # O próprio CDI não tem retorno acima do CDI: Sharpe indefinido
            "Sharpe (CDI)": (excesso.mean() / excesso.std() * np.sqrt(PREGOES_ANO)
                             if excesso.std() > 0 else np.nan),
            "Max drawdown": drawdown(r).min(),
            "Maior drawdown (dias)": periodos_drawdown(r)["dias"].max(),
            "Beta": beta,
            "Alpha (anual)": (excesso - beta * excesso_bench).mean() * PREGOES_ANO,
            "Correlação": r.corr(retornos[benchmark]),
        }
    return pd.DataFrame(tabela)


def formatar(tabela: pd.DataFrame) -> pd.DataFrame:
    """Tabela de resumo com cada linha no formato certo (% ou número), para exibir.
    Métrica que não se aplica (ex.: Sharpe do próprio CDI) aparece como '—'."""
    return tabela.apply(
        lambda linha: linha.map(lambda v: "—" if pd.isna(v) else FORMATOS[linha.name].format(v)),
        axis=1)
