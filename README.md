# IQF: Estratégia de Factor Investing

Carteira 65% defensiva (Quality + Low Vol → Value, rebalanceamento trimestral) e 35% agressiva (Size → Momentum, rebalanceamento mensal), comparada ao Ibovespa.

## Como rodar

```bash
pip install -r requirements.txt
python src/limpeza.py        # data/raw/*.xlsx -> data/processed/*.parquet
```

Os xlsx brutos do Economatica não estão no Git. Peça a pasta `data/raw/` para o grupo (OneDrive).

Para carregar os dados limpos:

```python
import pandas as pd
precos = pd.read_parquet("data/processed/precos_diarios.parquet")
vm     = pd.read_parquet("data/processed/valor_mercado_mensal.parquet")
fund   = pd.read_parquet("data/processed/fundamentos_trimestrais.parquet")
```
