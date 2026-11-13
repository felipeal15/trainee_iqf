# Diagnóstico do bloco agressivo (sequencial)

Gerado por `python src/diagnostico.py sequencial`. Período 03/01/2011 a 23/10/2026; custo principal 0,2% por operação. Nada aqui muda a estratégia.

## 1. Contribuição por ação

| medida | valor |
|---|---|
| ações diferentes que passaram pelo bloco | 120 |
| soma das contribuições (antes do custo) | 124,4% |
| soma dos custos | −28,6% |
| soma das contribuições positivas | 335,9% |
| soma das contribuições negativas | −211,4% |
| 15 maiores / positivas | 52,4% |
| 15 menores / negativas | 69,7% |
| 5 menores / negativas | 33,1% |
| ações com contribuição negativa | 47 de 120 |
| meses na carteira por ação (mediana) | 7 |
| das 15 menores, quantas pararam de negociar | 3 |
| das 15 maiores, quantas pararam de negociar | 5 |

### 15 menores

| ticker | contribuição | meses | retorno médio no mês | na carteira | situação | 12m antes de sair |
|---|---|---|---|---|---|---|
| MNDL4 | −18,1% | 5 | −21,7% | 06/2011–10/2011 | troca de código → MNDL3 (03/2012) | 22,6% |
| CASH3 | −15,0% | 7 | −15,0% | 08/2021–07/2025 | ativa | — |
| RAPT4 | −12,6% | 14 | −6,3% | 01/2013–12/2020 | ativa | — |
| GFSA3 | −12,2% | 12 | −7,1% | 05/2013–01/2023 | ativa | — |
| SEER3 | −12,0% | 7 | −11,0% | 01/2015–03/2018 | ativa | — |
| BEEF3 | −10,3% | 46 | −1,6% | 02/2013–11/2025 | ativa | — |
| LIGT3 | −9,1% | 29 | −2,2% | 05/2011–07/2023 | ativa | — |
| ETER3 | −8,9% | 5 | −10,9% | 12/2020–07/2021 | ativa | — |
| ELPL4 | −8,6% | 12 | −4,7% | 08/2011–11/2017 | troca de código → ELPL3 (11/2017) | 68,8% |
| VIVR3 | −8,1% | 3 | −18,1% | 07/2021–09/2021 | ativa | — |
| ENAT3 | −7,5% | 14 | −3,8% | 01/2016–07/2024 | saiu da bolsa (07/2024) | 58,2% |
| AUAU3 | −7,2% | 6 | −8,4% | 08/2021–01/2025 | ativa | — |
| WIZC3 | −6,9% | 6 | −7,9% | 06/2017–09/2021 | ativa | — |
| SBFG3 | −6,0% | 8 | −5,2% | 02/2020–09/2020 | ativa | — |
| POSI3 | −4,9% | 6 | −5,8% | 05/2021–10/2021 | ativa | — |

### 15 maiores

| ticker | contribuição | meses | retorno médio no mês | na carteira | situação | 12m antes de sair |
|---|---|---|---|---|---|---|
| MGLU3 | 30,7% | 12 | 17,9% | 07/2014–06/2017 | ativa | — |
| CSMG3 | 18,8% | 29 | 4,5% | 01/2012–04/2025 | ativa | — |
| DIRR3 | 15,7% | 23 | 4,8% | 08/2023–03/2026 | ativa | — |
| CVCB3 | 13,6% | 21 | 4,2% | 04/2016–04/2025 | ativa | — |
| SAUD3 | 10,7% | 25 | 2,8% | 12/2010–03/2018 | ativa | — |
| GOLL54 | 9,9% | 40 | 1,5% | 05/2013–07/2023 | saiu da bolsa (03/2026) | −99,2% |
| CESP6 | 9,9% | 11 | 6,2% | 09/2018–02/2021 | saiu da bolsa (03/2022) | −2,3% |
| ENEV3 | 9,7% | 13 | 5,3% | 03/2011–10/2019 | ativa | — |
| BRAP4 | 9,0% | 21 | 3,0% | 11/2016–09/2026 | ativa | — |
| HGTX3 | 8,9% | 25 | 2,1% | 12/2010–06/2021 | saiu da bolsa (09/2021) | 102,4% |
| BIDI4 | 8,1% | 3 | 18,8% | 04/2019–06/2019 | saiu da bolsa (06/2022) | −84,0% |
| FLRY3 | 8,0% | 12 | 4,7% | 04/2016–06/2026 | ativa | — |
| AMBP3 | 7,9% | 5 | 11,1% | 08/2021–08/2024 | ativa | — |
| MBRF3 | 7,6% | 42 | 1,1% | 08/2012–07/2024 | ativa | — |
| SMLS3 | 7,3% | 10 | 5,1% | 02/2014–09/2015 | saiu da bolsa (06/2021) | 130,1% |

![](1_contribuicao.png)


## 2. Size e Momentum separados (mesmo universo, mesmo custo, mensal)

| série | custo | CAGR | Volatilidade | Sharpe (CDI) | Max drawdown | Alpha | Beta |
|---|---|---|---|---|---|---|---|
| Universo peso igual | custo 0,2% | 6,66% | 22,7% | −0,02 | −49,0% | −0,50% | 0,92 |
| Só Size (30% menores) | custo 0,2% | −1,15% | 29,1% | −0,22 | −69,0% | −6,57% | 1,06 |
| Só Momentum (30% maiores) | custo 0,2% | 10,98% | 22,8% | 0,16 | −52,4% | 3,56% | 0,84 |
| Bloco agressivo | custo 0,2% | 1,89% | 30,3% | −0,10 | −64,1% | −3,07% | 0,94 |
| Ibovespa | custo 0,2% | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |
| CDI | custo 0,2% | 9,93% | 0,2% | — | 0,0% | 0,00% | −0,00 |
| Universo peso igual | sem custo | 6,99% | 22,7% | −0,01 | −48,9% | −0,19% | 0,92 |
| Só Size (30% menores) | sem custo | −0,36% | 29,1% | −0,20 | −68,2% | −5,76% | 1,06 |
| Só Momentum (30% maiores) | sem custo | 12,24% | 22,8% | 0,21 | −52,4% | 4,71% | 0,84 |
| Bloco agressivo | sem custo | 3,76% | 30,3% | −0,04 | −62,1% | −1,23% | 0,94 |
| Ibovespa | sem custo | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |


| variante | ações por carteira | giro médio por mês |
|---|---|---|
| Universo peso igual | 86 | 12% |
| Só Size (30% menores) | 25 | 33% |
| Só Momentum (30% maiores) | 25 | 47% |
| Bloco agressivo | 7 | 75% |

![](2_size_x_momentum.png)


## 3. O que é "small" no nosso universo (R$ bi nominais)

| R$ bi | universo_mediana | menores30_mediana | menores30_maior | bloco_mediana | bloco_menor | bloco_maior |
|---|---|---|---|---|---|---|
| período todo (média das datas) | 14,2 | 5,1 | 7,8 | 5,5 | 2,7 | 7,5 |
| 2023-26 | 18,5 | 5,6 | 9,2 | 6,2 | 3,0 | 8,7 |
| última data (09/2026) | 19,9 | 5,0 | 8,3 | 7,7 | 3,3 | 8,3 |


| ano (média, R$ bi) | universo_mediana | menores30_mediana | menores30_maior | bloco_mediana | bloco_menor | bloco_maior |
|---|---|---|---|---|---|---|
| 2010 | 8,9 | 3,9 | 5,4 | 4,4 | 2,5 | 5,4 |
| 2011 | 8,2 | 4,0 | 5,6 | 4,5 | 1,6 | 5,4 |
| 2012 | 8,3 | 3,6 | 5,8 | 4,7 | 2,2 | 5,6 |
| 2013 | 8,6 | 3,7 | 5,8 | 4,1 | 1,8 | 5,7 |
| 2014 | 8,6 | 3,8 | 5,4 | 3,8 | 2,1 | 5,1 |
| 2015 | 7,7 | 2,7 | 4,6 | 3,1 | 1,9 | 4,3 |
| 2016 | 8,9 | 2,9 | 4,7 | 3,1 | 1,4 | 4,5 |
| 2017 | 11,0 | 4,6 | 6,6 | 4,5 | 2,7 | 5,9 |
| 2018 | 14,0 | 5,4 | 7,7 | 5,7 | 2,9 | 7,4 |
| 2019 | 19,2 | 7,6 | 10,1 | 7,8 | 4,1 | 9,5 |
| 2020 | 18,6 | 7,5 | 10,0 | 7,8 | 4,1 | 9,8 |
| 2021 | 22,0 | 7,3 | 12,2 | 5,6 | 1,3 | 11,3 |
| 2022 | 19,6 | 6,1 | 10,4 | 8,5 | 5,9 | 10,2 |
| 2023 | 18,2 | 5,4 | 9,3 | 6,4 | 3,6 | 8,8 |
| 2024 | 20,4 | 6,1 | 9,9 | 6,6 | 3,3 | 9,4 |
| 2025 | 17,1 | 5,5 | 8,7 | 5,3 | 1,8 | 8,3 |
| 2026 | 18,4 | 5,4 | 8,7 | 6,7 | 3,2 | 8,4 |

![](3_tamanho.png)


## 4. Concentração e diversificação

| medida | Bloco agressivo | Só Size (30% menores) | Só Momentum (30% maiores) | Universo peso igual |
|---|---|---|---|---|
| ações por carteira (média) | 6,9 | 25,1 | 24,7 | 85,5 |
| mín | 6 | 24 | 23 | 83 |
| máx | 7 | 26 | 26 | 87 |
| vol. média das ações | 47,7% | 51,6% | 40,3% | 42,3% |
| vol. da carteira | 30,3% | 29,0% | 22,7% | 22,7% |
| carteira / ações | 0,63 | 0,56 | 0,56 | 0,54 |
| correlação média implícita | 0,30 | 0,29 | 0,29 | 0,28 |
| R² diário contra o universo | 0,66 | 0,91 | 0,82 | 1,00 |
| risco específico (1 − R²) | 34,4% | 9,5% | 18,1% | 0,0% |



## 5. Por período

| ano | Bloco agressivo | Universo peso igual | Só Size (30% menores) | Só Momentum (30% maiores) | Ibovespa | CDI |
|---|---|---|---|---|---|---|
| 2011 | −1,8% | −13,8% | −23,3% | 3,6% | −18,1% | 11,6% |
| 2012 | 37,0% | 16,0% | 11,1% | 23,0% | 7,4% | 8,4% |
| 2013 | −0,7% | −7,4% | −25,1% | 0,9% | −15,5% | 8,1% |
| 2014 | 2,0% | −3,7% | −12,1% | 1,4% | −2,9% | 10,8% |
| 2015 | −33,7% | −15,7% | −29,5% | −5,8% | −13,3% | 13,2% |
| 2016 | 4,9% | 43,0% | 52,0% | 18,6% | 38,9% | 14,0% |
| 2017 | 66,8% | 37,0% | 51,5% | 53,5% | 26,9% | 10,0% |
| 2018 | −13,0% | 13,6% | 8,5% | 5,6% | 15,0% | 6,4% |
| 2019 | 43,3% | 49,0% | 54,7% | 51,7% | 31,9% | 6,0% |
| 2020 | −5,6% | 2,5% | 0,1% | 18,1% | 2,9% | 2,8% |
| 2021 | −23,2% | −15,7% | −25,2% | −9,4% | −12,1% | 4,4% |
| 2022 | 1,9% | −11,7% | −22,3% | −6,9% | 5,0% | 12,4% |
| 2023 | −15,5% | 16,3% | −4,4% | 8,0% | 22,0% | 13,0% |
| 2024 | −25,0% | −21,5% | −37,5% | −3,3% | −10,4% | 10,9% |
| 2025 | 44,8% | 31,6% | 34,4% | 25,4% | 34,0% | 14,3% |
| 2026 | 0,8% | 21,0% | 16,7% | 10,8% | 27,3% | 11,5% |


| subperíodo (CAGR) | Bloco agressivo | Universo peso igual | Só Size (30% menores) | Só Momentum (30% maiores) | Ibovespa | CDI |
|---|---|---|---|---|---|---|
| 2011-14 | 8,0% | −2,8% | −13,5% | 6,9% | −7,9% | 9,7% |
| 2015-16 (recessão) | −16,7% | 9,8% | 3,5% | 5,7% | 9,8% | 13,7% |
| 2017-19 | 27,7% | 32,5% | 36,6% | 35,1% | 24,5% | 7,5% |
| 2020 (Covid) | −5,7% | 2,5% | 0,1% | 18,2% | 2,9% | 2,8% |
| 2021-22 (alta de juros) | −11,7% | −13,8% | −24,0% | −8,2% | −4,0% | 8,4% |
| 2023-26 | −2,0% | 10,4% | −1,7% | 10,3% | 17,8% | 13,1% |

### Piores quedas do bloco

| # | topo | fundo | recuperação | queda do bloco | Universo peso igual no mesmo trecho | Ibovespa no mesmo trecho |
|---|---|---|---|---|---|---|
| 0 | 06/2021 | 06/2024 | não recuperou | −64,1% | −35,4% | −8,4% |
| 1 | 01/2020 | 03/2020 | 05/2021 | −60,2% | −47,1% | −44,0% |
| 2 | 09/2014 | 05/2016 | 07/2017 | −46,8% | −16,2% | −16,0% |
| 3 | 07/2011 | 08/2011 | 10/2012 | −41,2% | −18,8% | −17,6% |
| 4 | 10/2017 | 06/2018 | 08/2019 | −31,7% | −9,2% | −8,6% |

### Momentum crash

| retorno médio mensal | rebote (38 meses) | demais (140 meses) |
|---|---|---|
| Bloco agressivo | 5,19% | −0,73% |
| Só Momentum (30% maiores) | 4,76% | 0,12% |
| Perdedoras de Momentum (30% menores) | 7,89% | −1,86% |
| Momentum − Perdedoras | −3,13% | 1,99% |
| Universo peso igual | 6,10% | −0,55% |
| Ibovespa | 6,03% | −0,47% |


| pior mês | bloco | universo | Ibovespa no mês | Ibovespa 12m antes | Momentum − Perdedoras | rebote? |
|---|---|---|---|---|---|---|
| 03/2020 | −41,5% | −33,2% | −29,9% | 9,0% | −5,8% | não |
| 10/2021 | −24,8% | −10,5% | −6,7% | 17,3% | −6,9% | não |
| 06/2022 | −19,7% | −15,1% | −11,5% | −11,8% | 11,0% | não |
| 05/2018 | −16,6% | −9,8% | −10,9% | 31,7% | −4,8% | não |
| 02/2023 | −15,0% | −10,6% | −7,6% | 1,0% | 10,6% | não |
| 08/2023 | −14,6% | −8,4% | −5,1% | 18,2% | 1,4% | não |
| 09/2021 | −13,8% | −5,9% | −6,6% | 19,5% | −0,9% | não |
| 01/2024 | −12,7% | −7,0% | −4,8% | 22,0% | 2,3% | não |
| 12/2024 | −12,2% | −8,1% | −4,3% | −1,3% | 8,3% | não |
| 07/2011 | −12,1% | −6,5% | −5,7% | — | 4,1% | não |

![](5_retorno_anual.png)


## 6. Giro e custo

| medida | valor |
|---|---|
| CAGR sem custo | 3,76% |
| CAGR com custo | 1,89% |
| perda de CAGR pelo custo | 1,87% |
| custo pago por ano (soma simples) | 1,81% |
| custo acumulado (composto) | 24,9% |
| distância até o CDI (com custo) | 8,04% |
| parte dessa distância explicada pelo custo | 23% |
| distância até o universo peso igual (ambos com custo) | 4,76% |
| parte dessa distância explicada pelo custo extra | 32% |

![](6_custo.png)


## 7. Papel do bloco agressivo na carteira

| série | CAGR | Volatilidade | Sharpe (CDI) | Max drawdown | Alpha | Beta |
|---|---|---|---|---|---|---|
| Estratégia 65/35 | 9,05% | 21,2% | 0,07 | −45,8% | 1,42% | 0,81 |
| Bloco defensivo | 12,22% | 19,4% | 0,21 | −39,8% | 3,95% | 0,74 |
| Bloco agressivo | 1,89% | 30,3% | −0,10 | −64,1% | −3,07% | 0,94 |
| 65% defensivo + 35% CDI (referência) | 11,86% | 12,5% | 0,20 | −26,0% | 2,53% | 0,47 |
| Ibovespa | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |
| CDI | 9,93% | 0,2% | — | 0,0% | 0,00% | −0,00 |


|  | correlação agressivo × defensivo |
|---|---|
| diária, período todo | 0,67 |
| mensal, período todo | 0,67 |
| diária, 2011-14 | 0,57 |
| diária, 2015-16 (recessão) | 0,66 |
| diária, 2017-19 | 0,65 |
| diária, 2020 (Covid) | 0,83 |
| diária, 2021-22 (alta de juros) | 0,60 |
| diária, 2023-26 | 0,68 |


### Piores quedas da carteira e o que cada bloco fez no mesmo trecho

| # | topo | fundo | carteira 65/35 | só defensivo, mesmo trecho | só agressivo, mesmo trecho |
|---|---|---|---|---|---|
| 0 | 01/2020 | 03/2020 | −45,8% | −39,2% | −56,6% |
| 1 | 09/2014 | 01/2016 | −31,8% | −23,2% | −46,6% |
| 2 | 07/2011 | 08/2011 | −24,1% | −12,1% | −41,2% |
| 3 | 03/2018 | 06/2018 | −22,9% | −18,4% | −31,1% |
| 4 | 02/2026 | 08/2026 | −20,3% | −14,5% | −30,4% |


| subperíodo | vol. carteira 65/35 | vol. só defensivo |
|---|---|---|
| 2011-14 | 17,5% | 17,6% |
| 2015-16 (recessão) | 19,9% | 20,2% |
| 2017-19 | 17,7% | 16,1% |
| 2020 (Covid) | 44,2% | 38,3% |
| 2021-22 (alta de juros) | 21,9% | 19,4% |
| 2023-26 | 18,1% | 15,4% |

![](7_drawdown_carteira.png)
