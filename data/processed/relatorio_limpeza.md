# Relatório de limpeza

- Tickers no screening do Economatica: **475**
- Removidos por não terem nenhum preço desde 2000: **49**
- Tickers mantidos: **426**

## Preços diários
- Período: 03/01/2000 a 23/10/2026
- Dias sem pregão removidos (linhas vazias): **349**
- Preços com volume zero/ausente removidos (não são negócios reais): **154**
- Observações (data x ticker com preço): **1,312,656**
- Retornos diários com |r| > 100% marcados em `retorno_suspeito` (NÃO removidos): **249**, sendo **43** em dias com volume > R$ 1 mi

| data | ticker | retorno | volume (R$ mil) |
|---|---|---|---|
| 27/03/2019 | GSHP3 | +13900% | 5,108 |
| 29/06/2007 | EALT3 | +7044% | 5 |
| 18/06/2021 | SHUL3 | +2836% | 115 |
| 12/09/2003 | BSLI4 | +2512% | 0 |
| 20/08/2004 | LEVE3 | +2445% | 120 |
| 26/12/2000 | RSUL4 | +1264% | 0 |
| 14/03/2001 | CEEB5 | +1023% | 3 |
| 02/02/2007 | CASN3 | +1006% | 8 |
| 19/09/2019 | GPAR3 | +1000% | 205 |
| 25/07/2007 | SOND3 | +943% | 6 |

## Valor de mercado (mensal)
- Observações: **97,811**
- Valores carregados do mês anterior (ação sem negócio no fim do mês, até 2 meses): **2,945**

## Fundamentos (trimestral)
- Trimestres: 2000Q1 a 2026Q3
- Observações (trimestre x ticker com algum dado): **32,164**
- Defasagem aplicada: `data_disponivel = fim do trimestre + 3 meses`
- P/L negativo (prejuízo): **18.3%** das observações com P/L
- Patrimônio líquido negativo (Dív/PL < 0): **3,079** observações
- Prováveis financeiras (têm ROE mas nunca têm Dív/PL): **35** tickers

<details><summary>Lista de prováveis financeiras</summary>

ABCB4, BAZA3, BBAS3, BBDC3, BBDC4, BBSE3, BEES3, BEES4, BGIP3, BGIP4, BMEB3, BMEB4, BMGB4, BMIN3, BMIN4, BNBR3, BPAC11, BPAC3, BPAC5, BPAR3, BRSR3, BRSR5, BRSR6, BSLI3, BSLI4, FIGE3, IRBR3, ITUB3, ITUB4, PINE3, PINE4, PPLA11, SANB11, SANB3, SANB4

</details>

## Arquivos gerados
| arquivo | linhas | tamanho |
|---|---|---|
| `precos_diarios.parquet` | 1,312,656 | 26.2 MB |
| `valor_mercado_mensal.parquet` | 97,811 | 0.7 MB |
| `fundamentos_trimestrais.parquet` | 32,164 | 0.9 MB |