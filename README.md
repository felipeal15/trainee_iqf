# IQF: Estratégia de Factor Investing

Carteira de risco moderado comparada ao Ibovespa, com dois blocos:

- **Defensivo (65%), rebalanceado a cada trimestre:** nota de Quality (ROE alto, dívida baixa) + nota de Low Vol, somadas; ficam as 30% melhores e, entre elas, as 50% mais baratas pelo L/P (Value).
- **Agressivo (35%), rebalanceado todo mês:** nota de Size (menor valor de mercado) + nota de Momentum 12-1, somadas (interseccional, P18); ficam as 30% melhores. A regra da Entrega 1 (sequencial: Size e depois Momentum) continua no código para comparação (`COMBINACAO_AGRESSIVO = "sequencial"`).
- Peso igual dentro de cada bloco; a carteira volta a 65/35 a cada trimestre.

**Universo:** as 90 ações mais líquidas em cada data (uma classe por empresa, sem BDRs), numa base do Economatica que **inclui as ações canceladas** (sem viés de sobrevivência). **Custo de transação:** 0,2% sobre o valor negociado, proporcional ao giro de cada rebalanceamento. **Período:** jan/2011 a out/2026.

Todas as decisões, com data e motivo (P1 a P22), e as limitações conhecidas estão em [`contexto.md`](contexto.md).

## Como rodar

```bash
pip install -r requirements.txt
python src/limpeza.py              # data/raw/*.xlsx -> data/processed/*.parquet
python src/backtest.py             # teste do motor: peso igual no universo x Ibovespa
python src/estrategia.py           # estratégia 65/35: métricas x Ibovespa, giro e custo
python src/diagnostico.py sequencial      # diagnóstico do bloco agressivo da Entrega 1
python src/diagnostico.py interseccional  # diagnóstico do bloco agressivo atual (P18)
python src/robustez.py             # robustez da Aula 3 (leva alguns minutos)
```

## Onde estão os resultados

| O quê | Onde |
|---|---|
| Métricas, gráficos e carteiras da estratégia | `notebooks/entrega2_backtest.ipynb` (abrir e dar *Run All*) |
| Diagnóstico do bloco agressivo (Entrega 1, sequencial) | `resultados/diagnostico/resumo.md` |
| Diagnóstico do bloco agressivo atual (interseccional) | `resultados/diagnostico_interseccional/resumo.md` |
| Robustez: CDI, subperíodos, grades, fatias, piso de volume, significância, tearsheets do QuantStats | `resultados/robustez/resumo.md` e `resultados/robustez/*.html` |

## Dados

Os xlsx brutos do Economatica não estão no Git (licenciados para o Insper). Peça a pasta `data/raw/` para o grupo (OneDrive). O download foi feito removendo o filtro "Ativo/Cancelado = ativo" do screening, para trazer as ações canceladas.
O Ibovespa, o CDI e o IPCA são baixados na primeira execução (precisa de internet) e ficam em `data/processed/`.

Para usar as bases já no formato do backtest (num notebook, com `sys.path.append("src")`):

```python
from dados import carregar_dados
dados = carregar_dados()   # dados.retorno, dados.volume, dados.valor_mercado, dados.fundamentos, dados.ibov, dados.cdi
```

Para carregar os dados limpos:

```python
import pandas as pd
precos = pd.read_parquet("data/processed/precos_diarios.parquet")
vm     = pd.read_parquet("data/processed/valor_mercado_mensal.parquet")
fund   = pd.read_parquet("data/processed/fundamentos_trimestrais.parquet")
```
