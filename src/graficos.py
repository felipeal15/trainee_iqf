"""
graficos.py — Gráficos do resultado do backtest (os da Aula 2), em matplotlib.

    acumulado(retornos, ...)        retorno acumulado de cada série
    underwater(retornos, ...)       quanto cada série está abaixo do próprio topo
    piores_quedas(retornos, ...)    curva de uma série com os n piores drawdowns destacados
    retornos_anuais(retornos, ...)  retorno de cada ano, lado a lado

Todos recebem retornos DIÁRIOS (data no índice; uma coluna por série, ou uma Series) e
devolvem a figura. A cor segue a série: a mesma série tem a mesma cor em todos os gráficos.

Uso (num notebook, com src/ no path):
    from graficos import aplicar_estilo, acumulado
    aplicar_estilo()
    acumulado(retornos[["Estratégia 65/35", "Ibovespa"]], "Retorno acumulado")
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

from metricas import curva, drawdown, periodos_drawdown

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
# Paleta categórica conferida para daltonismo (as 4 primeiras cores, nesta ordem).
# O CDI é uma referência, não uma série da estratégia, e fica em cinza.
CORES = {
    "Estratégia 65/35": "#2a78d6",
    "Ibovespa": "#eb6834",
    "Bloco defensivo": "#1baf7a",
    "Bloco agressivo": "#eda100",
    "CDI": "#898781",
}
CORES_EXTRAS = ["#e87ba4", "#008300", "#6250d6", "#e34948"]  # séries com outros nomes

FUNDO = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"


def aplicar_estilo() -> None:
    """Grade e eixos discretos, linhas finas, fundo claro."""
    plt.rcParams.update({
        "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
        "figure.dpi": 110,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "text.color": TINTA, "axes.labelcolor": TINTA_SECUNDARIA,
        "xtick.color": TINTA_FRACA, "ytick.color": TINTA_FRACA,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "axes.edgecolor": EIXO, "axes.linewidth": 1,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRADE, "grid.linewidth": 1,
        "lines.linewidth": 1.3,  # ~2px em 110 dpi
        "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
        "legend.frameon": False,
    })


def _cor(nome: str, posicao: int) -> str:
    return CORES.get(nome, CORES_EXTRAS[posicao % len(CORES_EXTRAS)])


def _titulo(ax: plt.Axes, titulo: str, subtitulo: str) -> None:
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="semibold", pad=24 if subtitulo else 10)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, color=TINTA_SECUNDARIA, va="bottom")


def _eixo_datas(ax: plt.Axes, inicio: pd.Timestamp, fim: pd.Timestamp) -> None:
    ax.set_xlim(inicio, fim)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _rotulos_no_fim(ax: plt.Axes, finais: pd.Series, cores: dict[str, str], formato: str) -> None:
    """Ponto + rótulo (nome e último valor) no fim de cada linha. Rótulos que ficariam
    sobrepostos sobem um pouco e ganham um traço fino até a linha."""
    ymin, ymax = ax.get_ylim()
    folga = (ymax - ymin) * 0.065
    x0, x1 = ax.get_xlim()
    x_texto = x1 + (x1 - x0) * 0.02
    altura_rotulo, anterior = {}, -np.inf
    for nome, y in finais.sort_values().items():
        altura_rotulo[nome] = max(y, anterior + folga)
        anterior = altura_rotulo[nome]
    for nome, y in finais.items():
        ax.plot(x1, y, "o", ms=6, color=cores[nome], mec=FUNDO, mew=1.5, clip_on=False, zorder=5)
        deslocado = altura_rotulo[nome] - y > folga * 0.05
        ax.annotate(f"{nome}  {formato.format(y)}", xy=(x1, y), xytext=(x_texto, altura_rotulo[nome]),
                    va="center", color=TINTA, annotation_clip=False,
                    arrowprops={"arrowstyle": "-", "color": EIXO, "lw": 1} if deslocado else None)


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def acumulado(retornos: pd.DataFrame, titulo: str, subtitulo: str = "") -> plt.Figure:
    """Retorno acumulado de cada série desde o início (0% = capital inicial)."""
    acum = curva(retornos) - 1
    cores = {nome: _cor(nome, i) for i, nome in enumerate(acum.columns)}
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(0, color=EIXO, lw=1)
    for nome, serie in acum.items():
        ax.plot(serie.index, serie, color=cores[nome], label=nome, zorder=3)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _eixo_datas(ax, acum.index[0], acum.index[-1])
    _rotulos_no_fim(ax, acum.iloc[-1], cores, "{:+.0%}")
    ax.legend(loc="upper left")
    _titulo(ax, titulo, subtitulo)
    return fig


def underwater(retornos: pd.DataFrame, titulo: str, subtitulo: str = "") -> plt.Figure:
    """Distância de cada série até o próprio topo. A primeira série ganha uma área clara;
    o fundo de cada série é rotulado."""
    dd = drawdown(retornos)
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (nome, serie) in enumerate(dd.items()):
        cor = _cor(nome, i)
        if i == 0:
            ax.fill_between(serie.index, serie, 0, color=cor, alpha=0.10, lw=0)
        ax.plot(serie.index, serie, color=cor, label=nome, zorder=3)
        fundo = serie.idxmin()
        ax.plot(fundo, serie[fundo], "o", ms=6, color=cor, mec=FUNDO, mew=1.5, zorder=5)
        ax.annotate(f"{serie[fundo]:.1%} em {fundo:%m/%Y}".replace("-", "−"),
                    xy=(fundo, serie[fundo]), xytext=(8, 0), textcoords="offset points",
                    color=TINTA, va="center")
    ax.axhline(0, color=EIXO, lw=1)
    ax.set_ylim(dd.min().min() * 1.12, 0.02)  # folga embaixo para os rótulos dos fundos
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _eixo_datas(ax, dd.index[0], dd.index[-1])
    ax.legend(loc="lower right", ncols=len(dd.columns))
    _titulo(ax, titulo, subtitulo)
    return fig


def piores_quedas(retornos: pd.Series, titulo: str, subtitulo: str = "", n: int = 5) -> plt.Figure:
    """Retorno acumulado de uma série com os n piores drawdowns em faixas cinza, do topo
    até a recuperação (ou até o fim, se ainda não recuperou), numeradas da pior para a menor."""
    acum = curva(retornos) - 1
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for i, p in periodos_drawdown(retornos).head(n).iterrows():
        fim = acum.index[-1] if pd.isna(p["recuperação"]) else p["recuperação"]
        ax.axvspan(p["topo"], fim, color=EIXO, alpha=0.30, lw=0)
        ax.text(p["topo"], 0.98, f" {i + 1}º  {p['queda']:.0%}", transform=ax.get_xaxis_transform(),
                color=TINTA_SECUNDARIA, va="top", fontsize=9)
    ax.axhline(0, color=EIXO, lw=1)
    ax.plot(acum.index, acum, color=_cor(retornos.name, 0), zorder=3)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _eixo_datas(ax, acum.index[0], acum.index[-1])
    _titulo(ax, titulo, subtitulo)
    return fig


def retornos_anuais(retornos: pd.DataFrame, titulo: str, subtitulo: str = "") -> plt.Figure:
    """Retorno de cada ano civil, uma barra por série. O último ano pode estar incompleto."""
    anual = (1 + retornos).groupby(retornos.index.year).prod() - 1
    k = len(anual.columns)
    largura = 0.7 / k
    x = np.arange(len(anual))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for i, nome in enumerate(anual.columns):
        ax.bar(x + (i - (k - 1) / 2) * largura, anual[nome], width=largura, color=_cor(nome, i),
               label=nome, edgecolor=FUNDO, linewidth=1, zorder=3)
    ax.axhline(0, color=EIXO, lw=1, zorder=4)
    ax.set_xticks(x, [str(ano) for ano in anual.index])
    ax.set_xlim(-0.6, len(anual) - 0.4)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.legend(loc="upper left", ncols=k)
    _titulo(ax, titulo, subtitulo)
    return fig
