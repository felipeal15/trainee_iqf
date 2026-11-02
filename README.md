# IQF: Estratégia de Factor Investing

Carteira 65% defensiva (Quality + Low Vol → Value, rebalanceamento trimestral) e 35% agressiva (Size → Momentum, rebalanceamento mensal), comparada ao Ibovespa.

## Como rodar

```bash
pip install -r requirements.txt
python src/limpeza.py        # data/raw/*.xlsx -> data/processed/*.parquet
python src/backtest.py       # teste do motor: peso igual no universo x Ibovespa
```

Os xlsx brutos do Economatica não estão no Git. Peça a pasta `data/raw/` para o grupo (OneDrive).
O Ibovespa e o CDI são baixados na primeira execução (precisa de internet) e ficam em `data/processed/benchmark_diario.parquet`.

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
