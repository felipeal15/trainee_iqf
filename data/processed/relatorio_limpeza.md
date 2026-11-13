# Relatório de limpeza

- Tickers no screening do Economatica: **1420**
- Removidos por não terem nenhum preço desde 2000: **303**
- Tickers mantidos: **1117**

## Preços diários
- Período: 03/01/2000 a 23/10/2026
- Dias sem pregão removidos (linhas vazias): **349**
- Preços com volume zero/ausente removidos (não são negócios reais): **260**
- Observações (data x ticker com preço): **2,058,787**
- Retornos diários com |r| > 100% marcados em `retorno_suspeito` (NÃO removidos): **594**, sendo **81** em dias com volume > R$ 1 mi

| data | ticker | retorno | volume (R$ mil) |
|---|---|---|---|
| 13/07/2007 | CTMI3 | +106553% | 1,317,077 |
| 27/03/2019 | GSHP3 | +13900% | 5,108 |
| 29/06/2007 | EALT3 | +7044% | 5 |
| 09/05/2001 | TPEC3B | +5400% | 0 |
| 25/09/2009 | MEND3 | +4068% | 6 |
| 02/07/2001 | PTQS4 | +3561% | 24 |
| 18/06/2021 | SHUL3 | +2836% | 115 |
| 12/09/2003 | BSLI4 | +2512% | 0 |
| 20/08/2004 | LEVE3 | +2445% | 120 |
| 04/04/2007 | DHBI3 | +2201% | 8 |

## Valor de mercado (mensal)
- Observações: **184,573**
- Valores carregados do mês anterior (ação sem negócio no fim do mês, até 2 meses): **8,411**

## Fundamentos (trimestral)
- Trimestres: 2000Q1 a 2026Q3
- Observações (trimestre x ticker com algum dado): **63,745**
- Defasagem aplicada: `data_disponivel = fim do trimestre + 3 meses`
- P/L negativo (prejuízo): **17.8%** das observações com P/L
- Patrimônio líquido negativo (Dív/PL < 0): **6,597** observações
- Prováveis financeiras (têm ROE mas nunca têm Dív/PL): **94** tickers

<details><summary>Lista de prováveis financeiras</summary>

ABCB11, ABCB3, ABCB4, BAZA3, BBAS3, BBAS4, BBCM4, BBDC3, BBDC4, BBSE3, BECE3, BECE4, BEES3, BEES4, BEMG3, BEMG4, BEPA4, BESP3, BESP4, BFIT3, BFIT4, BGIP3, BGIP4, BICB11, BICB3, BICB4, BIDI11, BIDI3, BIDI4, BMCT4, BMEB3, BMEB4, BMGB11, BMGB4, BMIN3, BMIN4, BNBR3, BNBR4, BNCA3, BPAC11, BPAC3, BPAC5, BPAN4, BPAR3, BPIA3, BRIV3, BRIV4, BRSR11, BRSR3, BRSR5, BRSR6, BSCT3, BSCT5, BSCT6, BSGR3, BSLI3, BSLI4, CRIV3, CRIV4, CSAB3, CSAB4, CSMB3, CZRS4, DAYC3, DAYC4, DMFN3, FIGE3, IDVL3, IDVL4, IRBR3, ITUB3, ITUB4, MERC3, MERC4, MODL11, MODL3, MODL4, PINE3, PINE4, PPLA11, PPLA35, PPLA36, PRBC11, PRBC4, SANB11, SANB3, SANB4, SASG3, SFSA3, SFSA4, SLCP3, UBBR11, UBBR3, UBBR4

</details>

## Arquivos gerados
| arquivo | linhas | tamanho |
|---|---|---|
| `precos_diarios.parquet` | 2,058,787 | 38.6 MB |
| `valor_mercado_mensal.parquet` | 184,573 | 1.1 MB |
| `fundamentos_trimestrais.parquet` | 63,745 | 1.5 MB |