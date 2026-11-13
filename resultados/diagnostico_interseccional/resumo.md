# Diagnóstico do bloco agressivo (interseccional)

Gerado por `python src/diagnostico.py interseccional`. Período 03/01/2011 a 23/10/2026; custo principal 0,2% por operação. Nada aqui muda a estratégia.

## 1. Contribuição por ação

| medida | valor |
|---|---|
| ações diferentes que passaram pelo bloco | 177 |
| soma das contribuições (antes do custo) | 185,2% |
| soma dos custos | −17,8% |
| soma das contribuições positivas | 286,3% |
| soma das contribuições negativas | −101,1% |
| 15 maiores / positivas | 39,6% |
| 15 menores / negativas | 57,6% |
| 5 menores / negativas | 28,2% |
| ações com contribuição negativa | 62 de 177 |
| meses na carteira por ação (mediana) | 20 |
| das 15 menores, quantas pararam de negociar | 4 |
| das 15 maiores, quantas pararam de negociar | 1 |

### 15 menores

| ticker | contribuição | meses | retorno médio no mês | na carteira | situação | 12m antes de sair |
|---|---|---|---|---|---|---|
| AZUL54 | −7,8% | 30 | −6,4% | 03/2018–04/2024 | troca de código → AZUL3 (01/2026) | −99,9% |
| GFSA3 | −7,4% | 40 | −4,6% | 12/2012–03/2024 | ativa | — |
| CASH3 | −5,0% | 8 | −15,5% | 08/2021–07/2025 | ativa | — |
| MNDL4 | −4,3% | 4 | −25,6% | 06/2011–09/2011 | troca de código → MNDL3 (03/2012) | 22,6% |
| AUAU3 | −4,0% | 13 | −7,6% | 07/2021–01/2025 | ativa | — |
| LIGT3 | −4,0% | 68 | −1,5% | 01/2011–07/2023 | ativa | — |
| SOMA3 | −3,7% | 11 | −8,3% | 09/2021–07/2023 | saiu da bolsa (07/2024) | −47,1% |
| PCAR3 | −3,6% | 20 | −4,5% | 03/2022–12/2025 | ativa | — |
| RAPT4 | −3,5% | 32 | −2,7% | 01/2011–12/2020 | ativa | — |
| ENAT3 | −3,1% | 17 | −4,6% | 01/2012–07/2024 | saiu da bolsa (07/2024) | 58,2% |
| WIZC3 | −2,6% | 9 | −6,8% | 04/2017–09/2021 | ativa | — |
| ANIM3 | −2,5% | 6 | −10,4% | 01/2015–08/2015 | ativa | — |
| SEER3 | −2,3% | 9 | −6,1% | 01/2015–03/2018 | ativa | — |
| ETER3 | −2,3% | 5 | −10,9% | 12/2020–07/2021 | ativa | — |
| VIVR3 | −2,2% | 3 | −18,1% | 07/2021–09/2021 | ativa | — |

### 15 maiores

| ticker | contribuição | meses | retorno médio no mês | na carteira | situação | 12m antes de sair |
|---|---|---|---|---|---|---|
| MGLU3 | 15,4% | 33 | 11,6% | 07/2014–02/2026 | ativa | — |
| PRIO3 | 9,3% | 51 | 4,6% | 08/2011–09/2026 | ativa | — |
| CSMG3 | 8,4% | 69 | 3,0% | 01/2012–09/2026 | ativa | — |
| BRAP4 | 8,1% | 87 | 2,3% | 08/2016–09/2026 | ativa | — |
| ENEV3 | 8,0% | 60 | 3,3% | 12/2010–09/2026 | ativa | — |
| MRVE3 | 7,7% | 105 | 1,8% | 12/2010–09/2026 | ativa | — |
| EMBJ3 | 7,5% | 60 | 3,1% | 12/2010–08/2025 | ativa | — |
| CYRE3 | 7,0% | 100 | 1,7% | 03/2012–07/2026 | ativa | — |
| CPLE6 | 6,9% | 67 | 2,6% | 11/2013–04/2025 | troca de código → CPLE3 (11/2025) | 55,3% |
| IRBR3 | 6,7% | 41 | 4,1% | 05/2018–09/2026 | ativa | — |
| RADL3 | 6,6% | 44 | 3,7% | 08/2011–05/2026 | ativa | — |
| TAEE11 | 5,9% | 82 | 1,8% | 09/2012–09/2026 | ativa | — |
| MOVI3 | 5,8% | 21 | 6,9% | 08/2019–09/2026 | ativa | — |
| FLRY3 | 5,2% | 61 | 2,1% | 04/2016–09/2026 | ativa | — |
| EQTL3 | 4,8% | 50 | 2,4% | 01/2013–08/2023 | ativa | — |

![](1_contribuicao.png)


## 2. Size e Momentum separados (mesmo universo, mesmo custo, mensal)

| série | custo | CAGR | Volatilidade | Sharpe (CDI) | Max drawdown | Alpha | Beta |
|---|---|---|---|---|---|---|---|
| Universo peso igual | custo 0,2% | 6,45% | 22,7% | −0,03 | −49,0% | −0,71% | 0,92 |
| Só Size (30% menores) | custo 0,2% | −1,91% | 29,1% | −0,25 | −72,3% | −7,34% | 1,06 |
| Só Momentum (30% maiores) | custo 0,2% | 11,13% | 22,8% | 0,16 | −52,4% | 3,70% | 0,84 |
| Bloco agressivo sequencial (Entrega 1) | custo 0,2% | 1,41% | 30,4% | −0,12 | −64,1% | −3,54% | 0,94 |
| Bloco agressivo | custo 0,2% | 7,82% | 24,1% | 0,04 | −55,7% | 0,95% | 0,88 |
| Ibovespa | custo 0,2% | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |
| CDI | custo 0,2% | 9,93% | 0,2% | — | 0,0% | 0,00% | −0,00 |
| Universo peso igual | sem custo | 6,79% | 22,7% | −0,02 | −48,9% | −0,39% | 0,92 |
| Só Size (30% menores) | sem custo | −1,12% | 29,1% | −0,22 | −71,2% | −6,53% | 1,06 |
| Só Momentum (30% maiores) | sem custo | 12,39% | 22,8% | 0,21 | −52,4% | 4,85% | 0,84 |
| Bloco agressivo sequencial (Entrega 1) | sem custo | 3,28% | 30,4% | −0,05 | −62,1% | −1,68% | 0,94 |
| Bloco agressivo | sem custo | 9,04% | 24,1% | 0,09 | −55,7% | 2,10% | 0,89 |
| Ibovespa | sem custo | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |


| variante | ações por carteira | giro médio por mês |
|---|---|---|
| Universo peso igual | 86 | 13% |
| Só Size (30% menores) | 25 | 33% |
| Só Momentum (30% maiores) | 25 | 47% |
| Bloco agressivo sequencial (Entrega 1) | 7 | 76% |
| Bloco agressivo | 25 | 47% |

![](2_size_x_momentum.png)


## 3. O que é "small" no nosso universo (R$ bi nominais)

| R$ bi | universo_mediana | menores30_mediana | menores30_maior | bloco_mediana | bloco_menor | bloco_maior |
|---|---|---|---|---|---|---|
| período todo (média das datas) | 14,4 | 5,1 | 7,9 | 8,0 | 2,1 | 28,7 |
| 2023-26 | 19,2 | 5,7 | 9,4 | 9,4 | 2,1 | 41,9 |
| última data (09/2026) | 21,9 | 5,2 | 8,5 | 13,6 | 3,1 | 53,5 |


| ano (média, R$ bi) | universo_mediana | menores30_mediana | menores30_maior | bloco_mediana | bloco_menor | bloco_maior |
|---|---|---|---|---|---|---|
| 2010 | 8,9 | 3,9 | 5,4 | 5,4 | 1,6 | 12,3 |
| 2011 | 8,2 | 3,8 | 5,5 | 5,7 | 1,3 | 14,8 |
| 2012 | 8,3 | 3,6 | 5,8 | 6,4 | 1,6 | 21,3 |
| 2013 | 8,6 | 3,7 | 5,8 | 6,5 | 1,6 | 17,5 |
| 2014 | 8,7 | 3,9 | 5,6 | 5,8 | 1,3 | 20,3 |
| 2015 | 8,1 | 2,9 | 4,7 | 5,6 | 1,2 | 24,1 |
| 2016 | 9,0 | 2,9 | 4,8 | 4,9 | 1,0 | 18,5 |
| 2017 | 11,0 | 4,6 | 6,6 | 5,5 | 2,4 | 14,8 |
| 2018 | 14,0 | 5,4 | 7,7 | 7,6 | 2,3 | 23,3 |
| 2019 | 19,2 | 7,6 | 10,1 | 9,1 | 3,7 | 28,7 |
| 2020 | 18,6 | 7,5 | 10,0 | 9,5 | 2,8 | 31,7 |
| 2021 | 22,0 | 7,3 | 12,2 | 13,1 | 1,3 | 44,6 |
| 2022 | 19,6 | 6,1 | 10,4 | 11,3 | 4,1 | 36,9 |
| 2023 | 18,2 | 5,4 | 9,3 | 10,2 | 2,5 | 35,7 |
| 2024 | 20,4 | 6,1 | 9,9 | 10,3 | 1,9 | 40,0 |
| 2025 | 17,5 | 5,7 | 9,1 | 7,7 | 1,3 | 45,4 |
| 2026 | 21,3 | 5,6 | 9,1 | 9,5 | 2,7 | 48,0 |

![](3_tamanho.png)


## 4. Concentração e diversificação

| medida | Bloco agressivo | Só Size (30% menores) | Só Momentum (30% maiores) | Universo peso igual |
|---|---|---|---|---|
| ações por carteira (média) | 24,7 | 25,1 | 24,7 | 85,5 |
| mín | 23 | 24 | 23 | 83 |
| máx | 26 | 26 | 26 | 87 |
| vol. média das ações | 42,7% | 51,8% | 40,4% | 42,4% |
| vol. da carteira | 24,0% | 29,0% | 22,7% | 22,6% |
| carteira / ações | 0,56 | 0,56 | 0,56 | 0,53 |
| correlação média implícita | 0,29 | 0,28 | 0,29 | 0,28 |
| R² diário contra o universo | 0,88 | 0,90 | 0,82 | 1,00 |
| risco específico (1 − R²) | 12,1% | 9,5% | 18,1% | 0,0% |



## 5. Por período

| ano | Bloco agressivo | Universo peso igual | Só Size (30% menores) | Só Momentum (30% maiores) | Ibovespa | CDI |
|---|---|---|---|---|---|---|
| 2011 | −7,4% | −16,5% | −31,0% | 4,2% | −18,1% | 11,6% |
| 2012 | 24,6% | 16,0% | 11,1% | 23,0% | 7,4% | 8,4% |
| 2013 | −6,2% | −7,4% | −25,1% | 0,9% | −15,5% | 8,1% |
| 2014 | 1,5% | −3,7% | −12,7% | 0,6% | −2,9% | 10,8% |
| 2015 | −9,4% | −15,9% | −30,7% | −6,0% | −13,3% | 13,2% |
| 2016 | 22,1% | 42,7% | 54,3% | 16,6% | 38,9% | 14,0% |
| 2017 | 65,8% | 37,0% | 51,5% | 53,5% | 26,9% | 10,0% |
| 2018 | 2,7% | 13,6% | 8,5% | 5,6% | 15,0% | 6,4% |
| 2019 | 58,3% | 49,0% | 54,7% | 51,7% | 31,9% | 6,0% |
| 2020 | −3,7% | 2,5% | 0,1% | 18,1% | 2,9% | 2,8% |
| 2021 | −14,8% | −15,7% | −25,2% | −9,4% | −12,1% | 4,4% |
| 2022 | −10,5% | −11,7% | −22,3% | −6,9% | 5,0% | 12,4% |
| 2023 | 9,6% | 16,3% | −4,4% | 8,0% | 22,0% | 13,0% |
| 2024 | −20,7% | −21,5% | −37,5% | −3,3% | −10,4% | 10,9% |
| 2025 | 35,4% | 32,2% | 34,5% | 28,0% | 34,0% | 14,3% |
| 2026 | 16,1% | 21,3% | 16,1% | 13,1% | 27,3% | 11,5% |


| subperíodo (CAGR) | Bloco agressivo | Universo peso igual | Só Size (30% menores) | Só Momentum (30% maiores) | Ibovespa | CDI |
|---|---|---|---|---|---|---|
| 2011-14 | 2,4% | −3,6% | −15,9% | 6,8% | −7,9% | 9,7% |
| 2015-16 (recessão) | 5,2% | 9,6% | 3,4% | 4,7% | 9,8% | 13,7% |
| 2017-19 | 39,3% | 32,5% | 36,6% | 35,1% | 24,5% | 7,5% |
| 2020 (Covid) | −3,7% | 2,5% | 0,1% | 18,2% | 2,9% | 2,8% |
| 2021-22 (alta de juros) | −12,8% | −13,8% | −24,0% | −8,2% | −4,0% | 8,4% |
| 2023-26 | 8,6% | 10,6% | −1,8% | 11,5% | 17,8% | 13,1% |

### Piores quedas do bloco

| # | topo | fundo | recuperação | queda do bloco | Universo peso igual no mesmo trecho | Ibovespa no mesmo trecho |
|---|---|---|---|---|---|---|
| 0 | 01/2020 | 03/2020 | 05/2021 | −55,7% | −47,1% | −44,0% |
| 1 | 06/2021 | 06/2024 | não recuperou | −49,5% | −35,4% | −8,4% |
| 2 | 08/2014 | 01/2016 | 07/2016 | −27,6% | −37,1% | −38,6% |
| 3 | 06/2011 | 08/2011 | 02/2012 | −24,9% | −25,2% | −24,4% |
| 4 | 02/2018 | 06/2018 | 01/2019 | −23,5% | −16,4% | −20,4% |

### Momentum crash

| retorno médio mensal | rebote (38 meses) | demais (140 meses) |
|---|---|---|
| Bloco agressivo | 5,48% | −0,25% |
| Só Momentum (30% maiores) | 4,72% | 0,15% |
| Perdedoras de Momentum (30% menores) | 7,90% | −1,87% |
| Momentum − Perdedoras | −3,18% | 2,01% |
| Universo peso igual | 6,09% | −0,55% |
| Ibovespa | 6,03% | −0,47% |


| pior mês | bloco | universo | Ibovespa no mês | Ibovespa 12m antes | Momentum − Perdedoras | rebote? |
|---|---|---|---|---|---|---|
| 03/2020 | −40,5% | −33,2% | −29,9% | 9,0% | −5,8% | não |
| 10/2021 | −17,8% | −10,5% | −6,7% | 17,3% | −6,9% | não |
| 06/2022 | −15,2% | −15,1% | −11,5% | −11,8% | 11,0% | não |
| 05/2018 | −14,0% | −9,8% | −10,9% | 31,7% | −4,8% | não |
| 08/2023 | −13,2% | −8,4% | −5,1% | 18,2% | 1,4% | não |
| 06/2013 | −10,7% | −9,0% | −11,3% | −1,8% | 3,4% | não |
| 02/2023 | −10,7% | −10,6% | −7,6% | 1,0% | 10,6% | não |
| 09/2014 | −10,0% | −8,9% | −11,7% | 22,6% | −2,9% | não |
| 04/2024 | −9,7% | −6,6% | −1,7% | 25,7% | 3,7% | não |
| 01/2024 | −9,6% | −7,0% | −4,8% | 22,0% | 2,3% | não |

![](5_retorno_anual.png)


## 6. Giro e custo

| medida | valor |
|---|---|
| CAGR sem custo | 9,04% |
| CAGR com custo | 7,82% |
| perda de CAGR pelo custo | 1,22% |
| custo pago por ano (soma simples) | 1,13% |
| custo acumulado (composto) | 16,3% |
| distância até o CDI (com custo) | 2,11% |
| parte dessa distância explicada pelo custo | 58% |
| distância até o universo peso igual (ambos com custo) | −1,37% |
| parte dessa distância explicada pelo custo extra | — (bloco acima do universo) |

![](6_custo.png)


## 7. Papel do bloco agressivo na carteira

| série | CAGR | Volatilidade | Sharpe (CDI) | Max drawdown | Alpha | Beta |
|---|---|---|---|---|---|---|
| Estratégia 65/35 | 11,06% | 20,0% | 0,15 | −43,7% | 3,02% | 0,79 |
| Bloco defensivo | 12,30% | 19,5% | 0,21 | −37,9% | 4,04% | 0,74 |
| Bloco agressivo | 7,82% | 24,1% | 0,04 | −55,7% | 0,95% | 0,88 |
| 65% defensivo + 35% CDI (referência) | 11,93% | 12,6% | 0,21 | −25,3% | 2,60% | 0,47 |
| Ibovespa | 7,11% | 23,1% | 0,00 | −47,7% | 0,00% | 1,00 |
| CDI | 9,93% | 0,2% | — | 0,0% | 0,00% | −0,00 |


|  | correlação agressivo × defensivo |
|---|---|
| diária, período todo | 0,80 |
| mensal, período todo | 0,78 |
| diária, 2011-14 | 0,80 |
| diária, 2015-16 (recessão) | 0,83 |
| diária, 2017-19 | 0,79 |
| diária, 2020 (Covid) | 0,88 |
| diária, 2021-22 (alta de juros) | 0,71 |
| diária, 2023-26 | 0,80 |


### Piores quedas da carteira e o que cada bloco fez no mesmo trecho

| # | topo | fundo | carteira 65/35 | só defensivo, mesmo trecho | só agressivo, mesmo trecho |
|---|---|---|---|---|---|
| 0 | 01/2020 | 03/2020 | −43,7% | −36,7% | −55,7% |
| 1 | 09/2014 | 01/2016 | −25,7% | −25,0% | −27,2% |
| 2 | 02/2018 | 06/2018 | −21,1% | −19,8% | −23,5% |
| 3 | 06/2011 | 08/2011 | −18,9% | −15,7% | −24,9% |
| 4 | 04/2026 | 08/2026 | −18,5% | −16,2% | −22,7% |


| subperíodo | vol. carteira 65/35 | vol. só defensivo |
|---|---|---|
| 2011-14 | 16,8% | 17,9% |
| 2015-16 (recessão) | 19,4% | 20,6% |
| 2017-19 | 17,2% | 16,1% |
| 2020 (Covid) | 41,5% | 38,3% |
| 2021-22 (alta de juros) | 20,3% | 19,4% |
| 2023-26 | 16,4% | 15,1% |

![](7_drawdown_carteira.png)
