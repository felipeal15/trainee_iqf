# Contexto do projeto — Estratégia de Factor Investing (IQF / Desafio Quant AI 2026)

Este arquivo registra **o que decidimos e por quê**. Leia antes de mexer no código.
Atualize sempre que uma decisão mudar (com data).

_Última atualização: 13/11/2026_

---

## 1. A estratégia (Entrega 1)

Carteira de **risco moderado**: a maior parte protege, a menor busca crescimento.
**Meta:** no backtest, superar o Ibovespa com quedas (drawdowns) menores que as do mercado.

**Universo:** não temos a composição histórica do Ibovespa. Em cada rebalanceamento, o universo são as **90 ações mais líquidas** (volume financeiro médio de 3 meses, negociadas em ≥ 90% dos pregões), uma classe por empresa (P1, P17), sem BDRs (P22), numa base que inclui as ações canceladas (P11). É uma aproximação dos critérios do Ibovespa, não o índice. **Benchmark:** Ibovespa.

### Bloco defensivo: 65% da carteira, rebalanceado a cada 3 meses
1. **Quality + Low Vol (interseccional):** nota combinada = Quality (ROE alto, dívida baixa) + Low Vol (baixa volatilidade). As duas notas são somadas para nenhuma dominar.
2. Ficam as **30% melhores** pela nota combinada.
3. **Value (sequencial):** entre elas, ficam as **50% mais baratas** pelo P/L.
4. Peso igual entre as ações selecionadas.

### Bloco agressivo: 35% da carteira, rebalanceado todo mês
1. **Size:** as **30% menores** por valor de mercado.
2. **Momentum (sequencial):** entre elas, ficam as **30% com maior retorno em 12 meses, ignorando o último mês** (12-1).
3. Peso igual entre as ações selecionadas.

> **Desde 13/11/2026 (P18), o bloco agressivo é interseccional:** nota de Size (menor = melhor) + nota de Momentum 12-1 (maior = melhor), no mesmo conjunto elegível; ficam as 30% melhores pela soma; peso igual, mensal, 35%. A regra sequencial acima é a da Entrega 1 e continua no código (`COMBINACAO_AGRESSIVO = "sequencial"`) só para comparação.

### Métricas por fator

| Fator | Métrica | Base |
|---|---|---|
| Quality | ROE (alto) e Dívida Bruta/PL (baixa) | `fundamentos_trimestrais` |
| Low Vol | Desvio-padrão dos retornos diários (12 meses), anualizado | `precos_diarios` |
| Value | P/L (baixo), calculado como L/P (alto) | `fundamentos_trimestrais` + `valor_mercado_mensal` |
| Size | Valor de mercado da empresa (baixo) | `valor_mercado_mensal` |
| Momentum | Retorno acumulado 12-1 meses | `precos_diarios` |

Fórmulas de referência:

- Retorno diário: $r_{i,t} = \tilde P_{i,t} / \tilde P_{i,t-1} - 1$ ($\tilde P$ = preço ajustado por proventos)
- Low Vol: $\sigma_i = \sqrt{252}\cdot\operatorname{std}(r_{i,t-251},\dots,r_{i,t})$
- Momentum: $MOM_i = \tilde P_{i,t-21} / \tilde P_{i,t-252} - 1$

**Avaliação:** retorno acumulado, CAGR, volatilidade, Sharpe, max drawdown, alpha e beta contra o Ibovespa (Aula 2).

---

## 2. Dados: o que foi baixado do Economatica

Baixado em **01/11/2026** pelo Felipe (só funciona no Wi-Fi do Insper). **Baixado de novo em 13/11/2026, incluindo as ações canceladas** (P11).

**Universo bruto:** Screening → Ações → "Básico: Ações negociadas na Bovespa", **removendo o filtro "Ativo/Cancelado = ativo"** (1.420 tickers). O screening "Básico" vem com esse filtro ligado e traz só as ações ativas hoje: foi por isso que o primeiro download (475 tickers) não tinha as canceladas. Formato, colunas e datas iguais aos do primeiro download, e valores idênticos nos tickers e datas em comum.

**Parâmetros comuns:** data inicial 01/01/2000, data final 23/10/2026, moeda original (R\$ nominal, **sem** ajuste por inflação), cabeçalho = código (ticker).

| Arquivo (`data/raw/`) | Indicador no Economatica | Parâmetros | Escala |
|---|---|---|---|
| `fechamento_ajust.xlsx` | Fechamento | ajust p/ prov (já vem assim por padrão) | dias |
| `volume.xlsx` | Volume\$ | em milhares de R\$ | dias |
| `valor_mercado.xlsx` | Valor Mercado **da empresa** | em milhares de R\$ | meses |
| `preco_lucro.xlsx` | Preco / Lucro | 12 meses, consolidado | trimestres |
| `roe.xlsx` | ROE Rent Pat **(pat final)** | 12 meses, consolidado | trimestres |
| `div_pl.xlsx` | Divida Bruta / Pat Liq | consolidado | trimestres |

**Para re-baixar:** "+" → Matrix → Criar coluna → digitar o indicador → desmarcar "corrente" → Adicionar → Mostrar itens do screening → seta dupla → OK → Parâmetros (datas, escala, moeda) → ícone do Excel.

### Por que essas escolhas
- **Preço ajustado por proventos:** sem o ajuste, todo dividendo e desdobramento aparece como queda falsa. Isso puniria justamente as empresas de Quality/Value (que mais pagam dividendos) e tornaria injusta a comparação com o Ibovespa, que é índice de retorno total.
- **Sem ajuste por inflação:** o benchmark (Ibovespa) e o CDI são nominais. Comparamos nominal com nominal.
- **Frequências diferentes por base:** cada dado é baixado na frequência em que muda e é usado. Preço muda todo dia. Valor de mercado é usado no rebalanceamento mensal. Balanço só muda a cada trimestre. Baixar tudo diário só repetiria valores e deixaria os arquivos pesados.
- **"Da empresa", não "da classe":** evita contar duas vezes empresas com mais de uma classe (PETR3/PETR4).
- **ROE com PL do fim do período:** mesma convenção que a mentoria usa para o ROIC ("AC fim"), padrão de mercado.
- **12 meses nos indicadores contábeis:** o acumulado de 12 meses evita a sazonalidade de usar um trimestre só e é atualizado a cada trimestre.

### O que NÃO baixamos (e de onde vem)
- **EV/EBITDA:** retirado. Value usa só P/L. Motivo: EV/EBITDA não existe para bancos, que pesam muito no Ibovespa, e simplifica o modelo. **Comunicar essa mudança na próxima entrega.**
- **Ibovespa (benchmark):** baixar com `yfinance`, ticker `^BVSP` (funciona de casa).
- **CDI (taxa livre de risco do Sharpe):** API do Banco Central, SGS série 12.
- **Composição histórica do Ibovespa:** não baixada. O universo será aproximado por filtro de liquidez (ver pendências).

---

## 3. Limpeza (`src/limpeza.py`)

Roda com `python src/limpeza.py` e gera, em `data/processed/`, três bases no **formato longo** (uma linha por data × ticker) em parquet, mais o `relatorio_limpeza.md`.

| Base | Colunas | Frequência |
|---|---|---|
| `precos_diarios.parquet` | data, ticker, fechamento_ajust, volume_mil, retorno, retorno_suspeito | diária |
| `valor_mercado_mensal.parquet` | data, ticker, valor_mercado_mil, preenchido | mensal |
| `fundamentos_trimestrais.parquet` | trimestre, data_referencia, data_disponivel, ticker, pl, roe, div_pl, lucro_12m_mil, pl_negativo, patrimonio_negativo, provavel_financeira | trimestral |

**Por que formato longo + parquet e não um CSV único:** as bases têm frequências diferentes. Juntar tudo numa tabela obrigaria a repetir valores ou deixar buracos, e facilitaria usar dado do futuro sem perceber. O parquet fica de 5 a 10 vezes menor que CSV e carrega em segundos. A junção acontece no backtest, data a data.

### Tratamentos aplicados

| # | Tratamento | Motivo | Números (rodada de 13/11/2026, com canceladas; entre parênteses, a de 01/11) |
|---|---|---|---|
| 1 | Remove as 3 linhas de lixo do topo e extrai o ticker do cabeçalho multilinha | Formato do export do Economatica | — |
| 2 | `"-"` → vazio (NaN) | É como o Economatica marca ausência de dado | — |
| 3 | Remove tickers sem nenhum preço desde 2000 | Inúteis para o backtest | 303 removidos, **1.117 mantidos** (49 e 426) |
| 4 | Remove linhas inteiramente vazias da base diária | Feriados / dias sem pregão | 349 dias |
| 5 | Remove preço com volume zero ou ausente | Não é negócio real. Ex.: ASAI3 tinha um "preço" em 26/02/2021, antes da estreia, que gerava um falso +386% | 260 linhas (154) |
| 6 | `retorno` = variação sobre o último preço disponível da mesma ação | Como o preço é ajustado, já é o retorno total (com dividendos) | 2.058.787 observações de preço (1.312.656) |
| 7 | Marca `retorno_suspeito` quando o retorno diário passa de 100% (**não remove**) | Erros de ajuste no Economatica. Ex.: GSHP3 +13.900% em 27/03/2019, grupamento não ajustado; CTMI3 +106.553% em 2007 | 594 casos, 81 com volume > R\$ 1 mi (249 e 43) |
| 8 | Valor de mercado: carrega o valor do mês anterior por até 2 meses (`preenchido = True`) | Ação sem negócio no último dia do mês | 8.411 valores (2.945) |
| 9 | Descarta trimestres que ainda não terminaram | A linha 4T2026 do P/L é só o P/L de hoje | — |
| 10 | `data_disponivel = fim do trimestre + 3 meses` | **Defasagem de divulgação** (prazos da CVM: ITR em 45 dias, DFP anual em 3 meses). Evita look-ahead bias. Desde a P21, a comparação com a data do rebalanceamento é feita por mês (em `dados.py`) | — |
| 11 | `lucro_12m_mil` = valor de mercado no fim do trimestre ÷ P/L | Ver "Descoberta sobre o P/L" abaixo | — |
| 12 | Flags `pl_negativo`, `patrimonio_negativo`, `provavel_financeira` | Armadilhas de ranking (ver pendências) | P/L < 0 em 17,8% das obs.; Dív/PL < 0 em 6.597 obs.; 94 financeiras (18,3%, 3.079 e 35) |

**Conferência das 94 prováveis financeiras (13/11/2026):** as 11 que chegam a entrar no universo líquido são todas bancos ou seguradoras (BBAS3, BBDC4, BBSE3, BIDI11/BIDI4, BPAC11, BPAN4, BRSR6, IRBR3, ITUB4, SANB11). Nove códigos antigos não puderam ser identificados pelo nome (BBCM4, BFIT3/4, BMCT4, BPIA3, BSGR3, CSMB3, DMFN3, SASG3, SLCP3), mas nenhum entra no universo: oito pararam de negociar antes de 2011 e o DMFN3 teve só 48 pregões. A classificação deles não afeta o backtest. Vale confirmar no Economatica se alguém tiver tempo.

### Descoberta sobre o P/L (importante para o backtest)
Testamos de onde vem o lucro do P/L trimestral do Economatica comparando o lucro implícito (valor de mercado ÷ P/L) entre linhas. Nas empresas que já tinham divulgado o 3T2026, a linha "3T2026" já usa o lucro do 3T2026, que não era conhecido em 30/09. Ou seja, o teste indica que a linha do trimestre *q* usa o **lucro do próprio trimestre *q***, divulgado semanas ou meses depois. Vale confirmar com a mentoria. Usar o P/L "de 30/09" no rebalanceamento de 30/09 seria usar informação do futuro.

**Solução:** extraímos o lucro implícito (`lucro_12m_mil = valor de mercado / P/L`) e, no backtest, recalculamos o indicador de Value com informação disponível na data:

$$
L/P_{i,t} = \frac{\text{lucro\_12m}_{i}\ \text{(último com data\_disponivel} \le t)}{\text{valor de mercado}_{i,t}}
$$

Isso combina o preço atual com o último lucro já divulgado, que é o que um investidor de verdade teria. Também resolve o P/L negativo (ver pendências).

Conferência: WEGE3 tem lucro 12m implícito de cerca de R\$ 6,3 bi, coerente com o lucro reportado.

### Verificação da limpeza (01/11/2026, antes do backtest)

| Achado | Impacto | O que fazer |
|---|---|---|
| **Viés de sobrevivência:** a base não tem ações canceladas. Faltam VALE5, LAME4, SULA11, CTIP3, HGTX3, JBSS3 etc. Só 19 dos 426 tickers param de negociar antes de 2026 (o primeiro em 2020), e em 2000 só 170 tickers têm preço | Backtest otimista, principalmente em Size e Momentum: empresas que quebraram ou foram compradas somem da amostra | **Resolvido em 13/11/2026 (P11):** base baixada de novo com as canceladas. O efeito foi maior no defensivo do que no agressivo, em p.p. (ver P11) |
| `retorno_suspeito` só pega altas: um retorno abaixo de −100% não existe, então queda falsa (desdobramento não ajustado, cisão) nunca é marcada. Ex.: PCAR3 −66% em 01/03/2021, que é a cisão do Assaí | Conservador para o retorno da carteira, mas distorce Low Vol e Momentum da ação afetada | Das 11 quedas > 50% com volume > R\$ 5 mi desde 2010, a maioria é real (AMER3, AZUL3). Manter e conferir caso a caso se alguma cair na carteira |
| Classes da mesma empresa têm o mesmo valor de mercado (PETR3 = PETR4, nos 24.855 casos) | A empresa contaria duas vezes no Size e na carteira | Resolvido no universo: uma classe por empresa, a mais líquida. Com as canceladas, a empresa passou a ser identificada também pelo valor de mercado (P17), por causa de trocas de código como AMBV4 → ABEV3 |
| P/L é por classe, valor de mercado é da empresa. Em multi-classe, `lucro_12m_mil` não é o lucro contábil (3T2025: PETR3 dá R\$ 75 bi, PETR4 dá R\$ 81 bi) | Nenhum para o ranking: o L/P recalculado continua sendo o da classe | Não usar `lucro_12m_mil` como lucro contábil em empresas com mais de uma classe |

---

## 4. Decisões pendentes (discutir com o grupo)

| # | Questão | Recomendação |
|---|---|---|
| P1 | **Universo:** não temos a composição histórica do Ibovespa | A cada rebalanceamento, usar as ~90 ações com maior volume financeiro médio nos últimos 3 meses e negociadas em ≥ 90% dos pregões. Imita os critérios do Ibovespa. **Implementado** em `universo.py`, com uma classe por empresa (84 a 88 empresas). Calibrar N: em 2010-15 a 90ª ação negociava só R\$ 1-2 mi/dia. **Correção (13/11/2026, medido na base atual, com canceladas e sem BDRs):** a 90ª ação negociava em média **R\$ 10,2 mi/dia** em 2010-15 (de 6,1 a 14,7, nominal) e R\$ 41 mi/dia em 2023-26. O "R\$ 1-2 mi" vinha da base antiga, sem as canceladas, e não vale mais |
| P2 | **Financeiras sem Dív/PL** (35 tickers, ex.: ITUB4, BBDC4, BBAS3, BPAC11, BBSE3) | Nota neutra (mediana) no componente de dívida do Quality. ROE e L/P valem normalmente. **Implementado** em `fatores.py` |
| P3 | **Patrimônio líquido negativo** (Dív/PL < 0) | Pior nota em Quality ou excluir. Num ranking ingênuo de "menor dívida", essas empresas apareceriam como as melhores. **As duas opções estão implementadas** (`PL_NEGATIVO` em `estrategia.py`, padrão "excluir") e comparadas no notebook |
| P4 | **P/L negativo** (prejuízo) | Ranquear por L/P (lucro ÷ preço). Prejuízo vira L/P negativo e vai para o fim da fila automaticamente. **Implementado** em `fatores.py` |
| P5 | **`retorno_suspeito`** | Tratar o retorno marcado como 0 (no retorno da carteira e no Momentum). É conservador: pode cortar um ganho real raro, mas impede ganhos falsos. A maioria está em ações ilíquidas que o filtro P1 já remove |
| P6 | **Início do backtest** | Jan/2011. Dados a partir de 2010 servem de histórico para Momentum/Low Vol de 12 meses, e o IFRS (contabilidade comparável) vale desde 2010. Pega a crise de 2015-16, a Covid e o ciclo de juros de 2021-22. Justificar no relatório (critério "escolha não oportunista de período") |
| P7 | **Datas de rebalanceamento** | Último pregão de cada mês (agressivo) e de mar/jun/set/dez (defensivo) |
| P8 | **"Small caps" dentro do Ibovespa** | As 30% menores do Ibovespa são, na prática, mid caps. Reconhecer essa limitação no relatório |
| P9 | **Custos de transação** | Começar sem custo. Depois testar algo como 0,1% por operação para ver a sensibilidade, já que o bloco mensal gira bastante. **Substituída pela P16** (custo proporcional ao giro, 13/11/2026) |
| P10 | **Quando voltar a 65/35:** os blocos rebalanceiam em frequências diferentes e os pesos derivam | Voltar a 65/35 a cada rebalanceamento trimestral, quando os dois blocos rebalanceiam juntos |
| P11 | **Viés de sobrevivência:** a base não tem ações canceladas | **Resolvido em 13/11/2026.** As 6 planilhas foram baixadas de novo sem o filtro "Ativo/Cancelado = ativo" (1.420 tickers, 1.117 depois da limpeza) e o `limpeza.py` rodou sem mudança de código. Em 2011, 43% das empresas do universo líquido eram ações que a base antiga não tinha (24% em média no período). Efeito isolado (mesmo código, P17 desligada), CAGR da carteira com custo de 0,2%: **10,34% → 9,01%** (−1,33 p.p.); defensivo 13,95% → 12,49% (−1,46 p.p.); agressivo 2,03% → 1,22% (−0,81 p.p.). Tabela completa na seção 5. Parte das "canceladas" são códigos antigos de empresas que continuam vivas (VIVT4, CPLE6, VALE5, GETI4, AMBV4) e parte são empresas compradas ou fechadas (SULA11, ENBR3, CIEL3, HGTX3, LINX3). A base antiga perdia as duas coisas. **Limitação que continua:** ação que sai da bolsa fica com retorno zero até o próximo rebalanceamento (hipótese do motor), sem modelar o valor recebido numa OPA ou a perda numa falência sem negociação |
| P12 | **Como somar as notas** ("para nenhuma dominar") | Ranking percentil (0 a 1) ou z-score cortado em ±3. **As duas opções estão implementadas** (`METODO_NOTA` em `estrategia.py`, padrão "rank") e comparadas no notebook. Escolher pelo argumento, não pelo backtest |
| P13 | **A mesma ação pode estar nos dois blocos** (ex.: CURY3 e BRAP4 aparecem no defensivo e no agressivo) | Hoje é permitido: os blocos são independentes, como na Entrega 1. Na prática o peso da ação soma. Decidir se fica assim |
| P14 | **Notas de Quality e Low Vol em conjuntos diferentes** (correção do monitor na Entrega 2, 13/11/2026) | **Corrigido.** Antes, o percentil de Quality era calculado só entre as empresas com PL positivo e o de Low Vol entre todo o universo; quem não tinha uma das notas só saía na soma. As duas notas "de 0 a 1" não estavam na mesma régua. Agora `elegiveis_defensivo()` (`estrategia.py`) define primeiro o conjunto elegível (ROE válido, Low Vol válido e, com `PL_NEGATIVO = "excluir"`, sem PL negativo) e as duas notas são calculadas sobre ele, nas 4 combinações de P3 × P12. Com "pior_nota", a empresa de PL negativo agora também precisa ter ROE para entrar. Efeito no padrão (rank/excluir): 4 de 64 trimestres com uma ação trocada, CAGR da carteira 11,33% → 11,33% |
| P15 | **Quality com dados de um balanço só, e mediana de Dív/PL só para financeiras** (13/11/2026) | **Corrigido**, em duas partes. (1) `ultimo_balanco()` pegava o último valor não vazio de cada coluna, então o ROE podia vir de um trimestre e o Dív/PL de outro. Agora ROE e Dív/PL vêm do **mesmo balanço**: o mais recente já divulgado em que o ROE existe. Se o Dív/PL estiver vazio nele, fica vazio. **Exceção necessária:** o Economatica nunca calcula ROE com PL negativo (100% dos 2.541 casos com Dív/PL < 0). O balanço "com ROE" é, portanto, sempre de antes de o PL ficar negativo, e a P3 nunca seria acionada (ex.: BEEF3 em 2016 e AMER3 em 2023 voltariam ao ranking com o PL antigo). Por isso a situação do PL (`patrimonio_negativo`) vem do balanço mais recente com Dív/PL. O `lucro_12m_mil` do Value continua sendo o último lucro divulgado, buscado à parte: o L/P combina de propósito o lucro mais recente com o preço de hoje, e amarrá-lo ao balanço do ROE deixaria o lucro mais velho sem motivo (31 casos). (2) A mediana de Dív/PL (P2) agora vale só para `provavel_financeira`. Não financeira sem Dív/PL fica sem nota de Quality e fora de `elegiveis_defensivo`, que passou a exigir Dív/PL ou ser financeira, para manter as duas notas no mesmo conjunto (P14). Na base atual não há nenhum caso desses no universo (BRAP4 e TIMS3 já ficavam fora por não terem ROE), então a parte (2) não muda nenhum número: é uma proteção para quando a base mudar (P11). Efeito total no padrão: 1 de 64 trimestres alterado, CAGR da carteira 11,33% → 11,30%. **Ressalva:** `provavel_financeira` é calculada na limpeza com a base inteira ("nunca teve Dív/PL"), ou seja, olha o histórico todo do ticker. Funciona como classificação de setor, mas vale declarar |
| P16 | **Custo de transação proporcional ao giro** (correção 3 do monitor, 13/11/2026) | **Implementado.** `CUSTO_OPERACAO = 0.002` (0,2% sobre o valor negociado, em cada compra e cada venda; exemplo da Aula 3), em `estrategia.py`. Em cada rebalanceamento de um bloco, giro = Σ \|peso novo − peso antigo\|, com o peso antigo **já andado com os preços** desde o rebalanceamento anterior (buy-and-hold). Ativo que sai tem peso novo 0 e ativo que entra tem peso antigo 0: trocar tudo dá giro 2, e a primeira montagem dá giro 1. Custo = giro × `CUSTO_OPERACAO`, pago no primeiro pregão depois do rebalanceamento: o retorno desse dia vira (1 + r)(1 − custo) − 1. A volta a 65/35 (P10) também paga: giro = Σ \|peso-alvo do bloco − peso antes\|, sem custo na primeira data, porque a montagem já está nos blocos. O custo fica no motor (`rodar_backtest(..., custo_operacao=)`, `calcular_giro`, `pesos_finais`, `descontar_custo` em `backtest.py`) e serve para qualquer `selecionar()`. Com custo 0, o resultado é idêntico bit a bit ao anterior (testado). **Simplificações:** custo igual para todas as ações (sem spread/impacto por liquidez); a volta a 65/35 é tratada à parte do giro interno dos blocos, então uma venda que as duas coisas pedem é contada duas vezes (efeito pequeno: 0,03% a.a.) |
| P17 | **Empresa identificada pelo valor de mercado, não só pelas 4 letras** (13/11/2026) | **Corrigido.** Com as canceladas na base, AMBV4 e ABEV3 (Ambev, troca de código em 2013) entravam juntas no universo de 10/2011 a 10/2013 (25 meses), porque têm prefixos diferentes: a Ambev contava duas vezes. Como o Economatica dá o valor de mercado da EMPRESA, igual em todas as classes (AMBV4 = ABEV3 em 322 de 322 meses), `identificar_empresas()` em `universo.py` junta na mesma empresa os tickers com as mesmas 4 letras **ou** o mesmo valor de mercado na data, e continua ficando a classe mais líquida. Ticker sem valor de mercado fica só com o critério das letras. Na base nova, a Ambev é o único caso no universo; na base antiga, a regra não muda nada (testado). Efeito: defensivo alterado em 4 de 64 trimestres e agressivo em 2 de 190 meses; CAGR da carteira com custo de 0,2% 9,01% → 8,96% |
| P18 | **Bloco agressivo interseccional** (decisão do grupo registrada em **13/11/2026, 17:48**, ANTES de rodar esta variante) | **Regra nova:** nota de Size (menor valor de mercado = melhor) + nota de Momentum 12-1 (maior = melhor), as duas calculadas sobre o MESMO conjunto elegível (ações do universo com valor de mercado e momentum válidos, mesma lógica da P14), somadas; ficam as 30% maiores pela soma. Peso igual, rebalanceamento mensal, 35% da carteira, mesmo `METODO_NOTA` do defensivo. **Justificativa:** (1) Aula 1 da liga, slide 15: combinações sequenciais "priorizam" o primeiro fator, e as interseccionais "equilibram a influência dos dois fatores"; (2) coerência com o bloco defensivo, que já soma Quality + Low Vol; (3) causas 2 e 3 do diagnóstico: o funil sequencial leva o Momentum para o pior pedaço do universo, e a fatia de 30% de 30% deixa a carteira com ~7 ações; (4) nenhum parâmetro novo: a fatia de 30% é a mesma da Entrega 1. **Compromisso:** a regra será mantida independentemente do resultado. A versão sequencial continua disponível só para comparação. **Nota de exatidão (acrescentada em 13/11/2026, depois da auditoria):** a regra foi decidida antes de rodar a variante interseccional, mas DEPOIS do diagnóstico, que já mostrava o "Só Momentum" acima do CDI. Portanto não é uma regra pré-registrada no sentido estrito: é uma revisão pós-diagnóstico. O horário de registro (17:48) também não é verificável pelo git, porque a P18, o código e os resultados entraram juntos no commit `aa4c7d3`. Por isso o paper apresenta lado a lado a regra pré-registrada da Entrega 1 (sequencial) e a revisão (interseccional), com e sem custo |
| P19 | **Correção 5 do monitor (rank único no defensivo): NÃO aplicada nesta entrega** (13/11/2026) | O defensivo não apresentou problema que motive a mudança (é o bloco que sustenta o resultado), o monitor deixou a decisão a critério do grupo, e preferimos fazer uma mudança estrutural por vez (a desta entrega foi a P18). Fica como próximo passo no paper |
| P20 | **Plano da análise de robustez** (registrado em **13/11/2026, 18:45**, ANTES de rodar) | `src/robustez.py` → `resultados/robustez/`. Custo de 0,2% em tudo, salvo indicação. **A estratégia está congelada: nada desta análise muda o padrão nem serve para escolher parâmetros.** (1) Tearsheets do QuantStats da carteira e de cada bloco contra o Ibovespa. O QuantStats só aceita `rf` fixo no HTML, então usa o CDI médio do período (taxa anual composta); o Sharpe oficial continua o nosso, com CDI diário. (2) Excesso sobre o CDI por ano. (3) Subperíodos 2011-14, 2015-16, 2017-19, 2020, 2021-22 e 2023-26. (4) Grades: janela dos fatores de preço (Low Vol e Momentum) de {6, 9, 12} meses × rebalanceamento do agressivo {mensal, trimestral}; e janela × rebalanceamento do defensivo {trimestral, semestral}. O Momentum continua pulando o último mês (6-1, 9-1, 12-1), e a volta a 65/35 acompanha o rebalanceamento do defensivo (P10: quando os dois blocos rebalanceiam juntos). (5) Fatias ±10 p.p., uma de cada vez: Quality+Low Vol 30% → 20%/40%, Value 50% → 40%/60%, Size+Momentum 30% → 20%/40%. (6) **Piso de volume no agressivo**, só como teste: no lugar das 90 mais líquidas, todas as ações com volume financeiro médio de 3 meses ≥ **R\$ 1 milhão/dia em reais de out/2026**, deflacionado pelo IPCA (SGS 433), mantendo presença ≥ 90% e uma classe por empresa (P17). **Por que R\$ 1 mi:** é a ordem de grandeza da 90ª ação do universo em 2010-15 (P1), então no começo o piso dá um universo parecido com o atual, e ele cresce quando o mercado cresce. **[Correção de 13/11/2026: essa premissa estava errada. Medida na base atual, a 90ª ação negociava R\$ 10,2 mi/dia em 2010-15, cerca de 10 vezes o piso, que corresponde a R\$ 0,4-0,6 mi nominais na época. Por isso o universo com piso já começa com ~180 empresas, o dobro do padrão. O piso NÃO foi trocado depois de ver o resultado: o teste continua valendo como "universo muito mais amplo e menos líquido", não como "universo parecido no começo".]** É justamente a crítica do monitor: um corte fixo em número de ações muda de significado ao longo do tempo. É também um piso baixo para um fundo de verdade. **O custo de 0,2% subestima o custo dessas ações menos líquidas** (spread e impacto maiores), então o resultado desse teste é otimista. (7) Anos de dado necessários: regra t ≈ Sharpe × √anos; para 95% de confiança, anos ≥ (1,96 / Sharpe)² |
| P21 | **Defasagem dos balanços comparada por MÊS** (decisão do grupo registrada em **13/11/2026, 19:28**, ANTES de ver o efeito; mantida qualquer que seja o resultado) | **Problema** (auditoria independente, confirmado pelo grupo: em 30 de 64 trimestres o balanço de 3 meses fica invisível): `data_disponivel` = fim do trimestre + 3 meses, no último dia do MÊS, era comparada com a data do rebalanceamento, que é o último PREGÃO do mês. Quando o mês termina em dia sem pregão (todo dezembro, entre outros), o balanço só entrava no trimestre seguinte: a defasagem real era de 3 ou 6 meses conforme o calendário, e não os 3 meses descritos. **Correção:** comparar por mês. Um balanço passa a valer no rebalanceamento do mês em que se completam os 3 meses (mês de `data_disponivel` ≤ mês do rebalanceamento), em `Dados.janela`, sem parâmetro novo. **Limitação:** para o 4º trimestre (DFP, prazo da CVM de 3 meses), no rebalanceamento de março pode haver empresa que divulgou nos últimos dias do mês, depois do último pregão |
| P22 | **BDRs fora do universo** (decisão do grupo registrada em **13/11/2026, 19:28**, ANTES de ver o efeito; mantida qualquer que seja o resultado) | **Problema** (auditoria independente): o universo incluía BDRs (ex.: AURA33, DAGB33, MILK33, CZLT33, AGEN33, JBSS32), e AURA33 e DAGB33 entravam no agressivo. A estratégia é de ações de empresas brasileiras; BDR é recibo de empresa estrangeira, com fundamentos não comparáveis. **Correção:** excluir do universo os códigos terminados em 32, 33, 34, 35 ou 39. A lista dos excluídos é conferida para garantir que nenhuma ação brasileira foi pega pela regra |

P5, P6, P7 e P10 (trimestral) já estão implementados como parâmetros, com as recomendações acima.

### Limitações conhecidas (registradas em 13/11/2026, depois da auditoria independente)

Não foram corrigidas: ficam declaradas no paper.

| Limitação | Efeito | Por que fica assim |
|---|---|---|
| **P5 é assimétrica:** o retorno marcado como suspeito (> +100% num dia) vira 0, mas a queda vizinha, que costuma ser o outro lado do mesmo erro de ajuste, fica. Ex.: PCAR3 (−66% em 01/03/2021, cisão do Assaí) não é marcada, porque a regra só olha altas | Pode deixar uma queda falsa sem a alta que a compensaria; distorce Low Vol e Momentum da ação afetada | Corrigir exige identificar eventos corporativos caso a caso; a maioria está em ações fora do universo líquido |
| **Anualização com 252 pregões:** a base tem em média **248 pregões por ano** (245 a 251, 2011-25) | Volatilidade e Sharpe ficam inflados por um fator √(252/248) ≈ 1,008 (menos de 1%); o CAGR usa dias corridos e não é afetado | Convenção de mercado; efeito desprezível |
| **Sobreposição entre os blocos (P13):** a mesma ação pode estar nos dois blocos. No padrão atual, nas datas trimestrais, **24% das ações do defensivo** estão também no agressivo (11% das do agressivo estão no defensivo) | O peso dessas ações soma, e a carteira fica mais concentrada do que 65/35 sugere | Os blocos são independentes desde a Entrega 1; mudar seria uma regra nova |
| **Custo fixo de 0,2%, independente da liquidez (P16)** | Subestima o custo das ações menos líquidas (spread e impacto maiores), principalmente no agressivo e no teste do piso de volume | Não temos dado de spread; um modelo por liquidez seria um parâmetro novo, sem calibração |
| **Defasagem do 4º trimestre (P21):** no rebalanceamento de março, a DFP pode ter sido divulgada nos últimos dias do mês, depois do último pregão | Pequeno risco de usar um balanço alguns dias antes de ele ser público | Prazo legal da CVM; a alternativa seria defasar mais um mês só no 4º trimestre |

---

## 5. Roadmap do backtest (Entrega 2)

Cada etapa é um commit. O motor (etapas 1 a 3) não sabe nada dos fatores: a estratégia entra como uma função `selecionar(janela, data) -> lista de tickers`, e cada bloco roda no mesmo loop.

| # | Etapa | Arquivo | O que faz | Status |
|---|---|---|---|---|
| 1 | Dados do backtest | `src/dados.py` | Bases em formato largo, P5 (suspeito → 0), Ibovespa e CDI com cache, `janela()` que recorta só o que era conhecido na data | ✅ |
| 2 | Universo | `src/universo.py` | P1: 90 mais líquidas em 3 meses, ≥ 90% dos pregões, uma classe por empresa | ✅ |
| 3 | Motor do loop | `src/backtest.py` | Datas (P6/P7), loop da Aula 2, buy-and-hold entre rebalanceamentos, teste de sanidade | ✅ |
| 4 | Métricas e gráficos | `src/metricas.py`, `src/graficos.py` | Retorno acumulado, CAGR, volatilidade, Sharpe (CDI), max drawdown, alpha e beta. Gráficos da Aula 2: acumulado vs Ibovespa, underwater, 5 piores quedas, retorno por ano | ✅ |
| 5 | Fatores | `src/fatores.py` | Métrica de cada fator por data: Low Vol, Momentum 12-1, Size, Value (L/P com lucro já divulgado, P4), Quality (ROE + Dív/PL, P2/P3) e a conversão em nota (P12) | ✅ |
| 6 | Bloco agressivo | `src/estrategia.py` | Size 30% → Momentum 30%, mensal | ✅ |
| 7 | Bloco defensivo | `src/estrategia.py` | Quality + Low Vol 30% → Value 50%, trimestral | ✅ |
| 8 | Carteira 65/35 | `src/estrategia.py` | Junta os dois blocos voltando a 65/35 a cada trimestre (P10) | ✅ |
| 9 | Material da Entrega 2 | `notebooks/entrega2_backtest.ipynb` | Métricas, gráficos, carteiras e comparação das escolhas P3/P12 | ✅ |
| 10 | Robustez | — | Custos (P16, feito), sensibilidade dos parâmetros, subperíodos | em andamento |

**Teste de sanidade do motor** (`python src/backtest.py`): peso igual em todo o universo, rebalanceado todo mês, de 03/01/2011 a 23/10/2026, sem custo. Não é a estratégia: serve para validar dados e loop.

| | Retorno acumulado | CAGR | Volatilidade | Correlação / beta com o Ibovespa |
|---|---|---|---|---|
| Universo peso igual, base antiga (01/11/2026) | 209,5% | 7,5% | 22,8% | 0,93 / 0,91 |
| Universo peso igual, base com canceladas | 184,4% | 6,9% | 22,7% | 0,94 / 0,92 |
| Universo peso igual, base com canceladas + P17 (atual) | 182,2% | 6,9% | 22,7% | 0,94 / 0,92 |
| Ibovespa | 195,9% | 7,2% | 23,1% | — |

83 a 88 ações por carteira. Anda junto com o índice, então dados e loop estão coerentes. Com as canceladas, o universo de peso igual passa a ficar um pouco **abaixo** do Ibovespa: só com as sobreviventes, ele ficava acima, um primeiro sinal do viés.

**Hipóteses do motor (v1):** sinal e operação no fechamento do mesmo pregão; custo de transação proporcional ao giro (P16; o teste de sanidade roda sem custo); dia sem negócio, ou ação que saiu da bolsa, conta como retorno zero até o próximo rebalanceamento.

**Primeira rodada da estratégia** (02/11/2026, padrão rank / excluir, sem custos; ainda sem análise):

| | CAGR | Volatilidade | Sharpe (CDI) | Max drawdown |
|---|---|---|---|---|
| Estratégia 65/35 | 11,3% | 21,4% | 0,17 | −47,1% |
| Bloco defensivo | 14,5% | 19,4% | 0,31 | −36,1% |
| Bloco agressivo | 3,7% | 31,6% | −0,03 | −67,7% |
| Ibovespa | 7,1% | 23,1% | 0,00 | −47,7% |
| CDI | 9,9% | 0,2% | — | 0% |

Carteiras: 11 a 13 ações no defensivo e 6 a 7 no agressivo. Nas 4 combinações de P3 × P12, o CAGR da carteira fica entre 11,0% e 11,8%. O z-score muda o defensivo em mais de 90% dos trimestres, mas o resultado quase não muda.

**Depois da correção P14** (13/11/2026, notas no mesmo conjunto): o padrão rank/excluir não muda (CAGR 11,33%, Sharpe 0,17, max drawdown −47,1%). Nas 4 combinações, o CAGR da carteira passa a ficar entre 11,1% e 11,5%. O z-score continua mudando o defensivo em 94% dos trimestres em relação ao rank.

| Combinação | CAGR carteira (antes → depois) | Sharpe carteira | Max DD carteira | CAGR defensivo | Sharpe defensivo | Max DD defensivo | Trimestres com o defensivo alterado |
|---|---|---|---|---|---|---|---|
| rank / excluir (padrão) | 11,33% → 11,33% | 0,17 → 0,17 | −47,1% → −47,1% | 14,49% → 14,49% | 0,31 → 0,31 | −36,1% → −36,1% | 4 de 64 |
| rank / pior_nota | 11,00% → 11,12% | 0,15 → 0,16 | −47,1% → −47,1% | 14,00% → 14,18% | 0,29 → 0,30 | −36,1% → −36,1% | 13 de 64 |
| zscore / excluir | 11,81% → 11,53% | 0,19 → 0,18 | −48,6% → −48,9% | 15,25% → 14,81% | 0,35 → 0,33 | −37,0% → −37,5% | 12 de 64 |
| zscore / pior_nota | 11,68% → 11,52% | 0,18 → 0,18 | −48,6% → −48,9% | 15,06% → 14,80% | 0,34 → 0,33 | −37,0% → −37,5% | 12 de 64 |

**Depois da correção P15** (13/11/2026, ROE e Dív/PL do mesmo balanço; mediana só para financeiras). Base de comparação: o resultado depois da P14. A parte (2) não alterou nenhuma carteira, então todo o efeito abaixo vem da parte (1). No padrão, a única troca foi em 12/2016: sai AZZA3, entra B3SA3. Ela vem de HYPE3 e RADL3, que não tinham ROE nos dois últimos balanços e por isso passaram a usar o Dív/PL do mesmo balanço do ROE (HYPE3: 20,5 → 61,3).

| Combinação | CAGR carteira (antes → depois) | Sharpe carteira | Max DD carteira | CAGR defensivo | Sharpe defensivo | Max DD defensivo | Trimestres com o defensivo alterado |
|---|---|---|---|---|---|---|---|
| rank / excluir (padrão) | 11,33% → 11,30% | 0,17 → 0,17 | −47,1% → −47,1% | 14,49% → 14,45% | 0,31 → 0,31 | −36,1% → −36,1% | 1 de 64 |
| rank / pior_nota | 11,12% → 11,09% | 0,16 → 0,16 | −47,1% → −47,1% | 14,18% → 14,14% | 0,30 → 0,29 | −36,1% → −36,1% | 1 de 64 |
| zscore / excluir | 11,53% → 11,69% | 0,18 → 0,18 | −48,9% → −48,9% | 14,81% → 15,09% | 0,33 → 0,34 | −37,5% → −37,5% | 1 de 64 |
| zscore / pior_nota | 11,52% → 11,43% | 0,18 → 0,17 | −48,9% → −48,9% | 14,80% → 14,66% | 0,33 → 0,32 | −37,5% → −37,5% | 1 de 64 |

Se a regra "último balanço com ROE" fosse aplicada também à situação do PL (sem a exceção da P15), o padrão cairia para 11,00%, com 4 trimestres alterados. Três dessas trocas viriam de empresas com PL negativo (BEEF3, AMER3) voltando ao ranking com dados antigos.

**Custo de transação (P16, 13/11/2026)**, padrão rank/excluir, de 03/01/2011 a 23/10/2026. O custo de 0% reproduz exatamente o resultado anterior. A partir daqui, o resultado principal é o de **0,2%**.

| Custo por operação | Carteira: CAGR / Vol / Sharpe / Max DD / Alpha | Defensivo: CAGR / Vol / Sharpe / Max DD / Alpha | Agressivo: CAGR / Vol / Sharpe / Max DD / Alpha |
|---|---|---|---|
| 0% (referência) | 11,30% / 21,4% / 0,17 / −47,1% / 3,52% | 14,45% / 19,4% / 0,31 / −36,1% / 5,93% | 3,68% / 31,6% / −0,03 / −67,7% / −0,90% |
| 0,1% | 10,82% / 21,4% / 0,15 / −47,1% / 3,08% | 14,20% / 19,4% / 0,30 / −36,1% / 5,71% | 2,85% / 31,6% / −0,05 / −67,7% / −1,72% |
| **0,2% (principal)** | **10,34% / 21,4% / 0,13 / −47,1% / 2,64%** | **13,95% / 19,4% / 0,29 / −36,2% / 5,49%** | **2,03% / 31,6% / −0,08 / −67,7% / −2,53%** |
| 0,5% | 8,90% / 21,4% / 0,06 / −47,1% / 1,31% | 13,21% / 19,4% / 0,25 / −36,3% / 4,83% | −0,40% / 31,6% / −0,16 / −67,8% / −4,97% |

Giro e custo com 0,2%. Giro em peso = Σ \|peso novo − peso antigo\|. Médias sem a montagem inicial; giro e custo anuais = soma no período ÷ anos.

| | Nomes trocados por rebal. | Giro médio por rebal. | Giro anual | Custo anual (% do bloco) | Perda de CAGR (0% → 0,2%) |
|---|---|---|---|---|---|
| Defensivo (trimestral) | 23% | 53% | 216% | 0,43% | 0,49 p.p. |
| Agressivo (mensal) | 30% | 66% | 801% | 1,60% | 1,65 p.p. |
| Volta a 65/35 (trimestral) | — | 4% | 17% | 0,03% | — |
| Carteira 65/35 | — | — | — | — | 0,96 p.p. |

**Nomes trocados × giro em peso:** os 23% e 30% de nomes trocados batem com a estimativa do monitor. Com peso igual, cada nome trocado gera uma venda e uma compra, então o giro em peso é cerca de **2 × a fração de nomes** (46% e 62%). Os ~5 p.p. restantes vêm de reequilibrar para peso igual as ações que ficam, que andaram com os preços. Com custo, o bloco agressivo rende 2,0% a.a., bem abaixo do CDI (9,9%): o custo agrava a fraqueza que ele já mostrava.

**Base com ações canceladas (P11) e empresa pelo valor de mercado (P17)**, 13/11/2026, padrão rank/excluir. A partir daqui, o **resultado principal** é o da última linha de cada bloco: base nova + P17, custo de 0,2%.

Efeito isolado do viés de sobrevivência (mesmo código, P17 desligada) e, separado, da P17. Formato: CAGR / Vol / Sharpe (CDI) / Max DD / Alpha.

| Bloco | Custo | Base antiga (só sobreviventes) | Base com canceladas | Base com canceladas + P17 |
|---|---|---|---|---|
| Carteira 65/35 | 0% | 11,30% / 21,4% / 0,17 / −47,1% / 3,52% | 10,06% / 21,2% / 0,11 / −44,2% / 2,35% | 10,01% / 21,3% / 0,11 / −44,2% / 2,31% |
| Carteira 65/35 | 0,2% | 10,34% / 21,4% / 0,13 / −47,1% / 2,64% | 9,01% / 21,2% / 0,07 / −44,2% / 1,38% | **8,96% / 21,3% / 0,06 / −44,2% / 1,34%** |
| Defensivo | 0% | 14,45% / 19,4% / 0,31 / −36,1% / 5,93% | 13,00% / 19,4% / 0,24 / −37,8% / 4,66% | 12,81% / 19,5% / 0,23 / −37,8% / 4,49% |
| Defensivo | 0,2% | 13,95% / 19,4% / 0,29 / −36,2% / 5,49% | 12,49% / 19,4% / 0,22 / −37,9% / 4,21% | **12,30% / 19,5% / 0,21 / −37,9% / 4,04%** |
| Agressivo | 0% | 3,68% / 31,6% / −0,03 / −67,7% / −0,90% | 3,09% / 30,4% / −0,06 / −62,1% / −1,87% | 3,28% / 30,4% / −0,05 / −62,1% / −1,68% |
| Agressivo | 0,2% | 2,03% / 31,6% / −0,08 / −67,7% / −2,53% | 1,22% / 30,4% / −0,12 / −64,1% / −3,73% | **1,41% / 30,4% / −0,12 / −64,1% / −3,54%** |

**Por que o viés pesou mais no defensivo, em p.p.** (−1,46 p.p. contra −0,81 p.p. no agressivo, com custo):
- Nas duas carteiras, cerca de um quarto do peso passa a ficar em ações que a base antiga não tinha (24% no defensivo, 22% no agressivo).
- No defensivo, essas ações renderam bem menos do que as demais: +1,4% por trimestre, contra +4,2%. São empresas grandes e estáveis que pareciam boas em Quality/Low Vol e depois foram compradas, fecharam o capital ou trocaram de código depois de anos fracos (SULA11, VIVT4, ENBR3, CPLE6, CIEL3, GETI4). A base antiga trocava essas empresas pelas sobreviventes, que já sabemos que deram certo.
- No agressivo, as canceladas não renderam menos do que as demais (+0,9% contra +0,5% ao mês, na média). O efeito vem de elas mudarem a composição do universo e dos cortes de Size, não de serem perdedoras. Em termos relativos, porém, o agressivo perde mais: 40% do próprio CAGR com custo (2,03% → 1,22%), contra 10% no defensivo.
- A intuição da Entrega 2 ("o viés pesa mais em Size e Momentum") **não se confirmou** em p.p. Vale dizer isso na banca.

**Diagnóstico do bloco agressivo** (correção 2 do monitor, 13/11/2026). Gerado por `python src/diagnostico.py`, que grava tabelas, gráficos e `resumo.md` em `resultados/diagnostico/`. Só descreve: não muda a estratégia nem escolhe parâmetros. Mesmo universo, custo de 0,2% e rebalanceamento mensal em todas as variantes. A variante "bloco agressivo" reproduz exatamente o bloco da estratégia (conferido no script).

| Variante (custo 0,2%) | Ações | Giro/mês | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|---|---|
| Universo peso igual | 86 | 13% | 6,45% | 22,7% | −0,03 | −49,0% |
| Só Size (30% menores) | 25 | 33% | **−1,91%** | 29,1% | −0,25 | −72,3% |
| Só Momentum (30% maiores) | 25 | 47% | **11,13%** | 22,8% | 0,16 | −52,4% |
| Bloco agressivo (Size → Momentum) | 7 | 76% | 1,41% | 30,4% | −0,12 | −64,1% |
| Ibovespa / CDI | — | — | 7,11% / 9,93% | 23,1% / 0,2% | 0,00 / — | −47,7% / 0% |

Hipóteses testadas:

| Hipótese | Veredito | Número |
|---|---|---|
| O fator Size falha no nosso universo | **Confirmada** | Só Size: −1,91% a.a. com custo (−1,12% sem), 8,4 p.p. abaixo do universo peso igual |
| O fator Momentum falha | **Refutada** | Só Momentum: 11,13% a.a. com custo, acima do CDI e do Ibovespa |
| A combinação piora o que funcionava sozinho | **Confirmada** | Momentum sozinho 11,13% → Momentum dentro das 30% menores 1,41% |
| O resultado ruim vem de poucas ações | **Refutada** | 121 ações passaram pelo bloco e 52 contribuíram negativamente; as 5 piores somam 31% das perdas, as 15 piores 67% |
| Ações que quebraram ou saíram da bolsa explicam as perdas | **Refutada** | Só 3 das 15 piores pararam de negociar; as maiores perdas são de empresas ativas (CASH3, GFSA3, SEER3, RAPT4) |
| "Small" no nosso universo é mid cap (monitor: mediana ~R\$ 3,5 bi, até ~R\$ 10 bi) | **Confirmada com ajuste** | Mediana das 30% menores de R\$ 2,9–3,9 bi em 2011-16 e R\$ 5,4–7,6 bi a partir de 2017; corte de R\$ 4,7–12,2 bi (~R\$ 9–10 bi em 2019-26). Valores nominais |
| A concentração (7 ações) aumenta o risco | **Confirmada** para risco específico; **refutada** para a vol total | 34% da variância diária não é explicada pelo universo (Só Size: 9,5%); mas a vol (30,3%) é quase a do Só Size com 25 ações (29,0%) |
| Momentum crash explica as quedas | **Refutada** para o bloco | O fenômeno existe no universo (Momentum − Perdedoras: −3,2% ao mês nos 38 meses de rebote, +2,0% nos demais), mas nenhum dos 10 piores meses do bloco foi de rebote: as quedas são de mercado em queda, amplificadas (03/2020: −41,5% contra −29,9% do Ibovespa) |
| O custo explica boa parte do resultado ruim | **Confirmada em parte** | −1,87 p.p. de CAGR; 22% da distância até o CDI e 31% da distância até o universo peso igual |
| O agressivo diversifica a carteira | **Refutada** | Correlação de 0,67 com o defensivo (0,83 em 2020); caiu mais do que o defensivo nas 5 piores quedas da carteira; a vol da carteira supera a do defensivo sozinho em 4 de 6 subperíodos |
| Small caps sofrem mais com juros altos | **Inconclusiva** | Só Size −24,0% a.a. em 2021-22 e −37,5% em 2024 (universo: −13,8% e −21,5%), mas é um ciclo só e 2015-16 é ambíguo |

Causas, em ordem de importância: (1) o prêmio de Size foi negativo no período e no universo (as "pequenas" são mid caps); (2) o funil sequencial restringe o Momentum, que funcionava, ao pior pedaço do universo; (3) a concentração em 7 ações gera giro de 76% ao mês (custo de 1,8% a.a.) e 34% de risco específico. Momentum crash e ações canceladas não explicam o resultado.

**Cuidado com overfitting:** o resultado do "Só Momentum" já foi visto. Qualquer mudança no bloco tem de ser justificada pela lógica e pela literatura, não por esta tabela, e o paper precisa dizer que este diagnóstico foi feito antes da mudança.

**Bloco agressivo interseccional (P18)**, 13/11/2026. A regra foi registrada na P18 às 17:48, antes de qualquer execução, e é mantida como foi registrada. A versão sequencial reproduz bit a bit o resultado anterior (testado). Mesmo defensivo, universo, fatias, pesos, custo e rebalanceamento. A partir daqui, o **resultado principal** é o interseccional com custo de 0,2%.

| | Custo | Sequencial (Entrega 1): CAGR / Vol / Sharpe / Max DD / Alpha / Beta | Interseccional (P18) |
|---|---|---|---|
| Carteira 65/35 | 0,2% | 8,96% / 21,3% / 0,06 / −44,2% / 1,34% / 0,81 | **11,06% / 20,0% / 0,15 / −43,7% / 3,02% / 0,79** |
| Carteira 65/35 | 0% | 10,01% / 21,3% / 0,11 / −44,2% / 2,31% / 0,81 | 11,85% / 20,0% / 0,19 / −43,6% / 3,74% / 0,79 |
| Defensivo | 0,2% | 12,30% / 19,5% / 0,21 / −37,9% / 4,04% / 0,74 | igual (o defensivo não mudou) |
| Defensivo | 0% | 12,81% / 19,5% / 0,23 / −37,8% / 4,49% / 0,74 | igual |
| Agressivo | 0,2% | 1,41% / 30,4% / −0,12 / −64,1% / −3,54% / 0,94 | **7,82% / 24,1% / 0,04 / −55,7% / 0,95% / 0,88** |
| Agressivo | 0% | 3,28% / 30,4% / −0,05 / −62,1% / −1,68% / 0,94 | 9,04% / 24,1% / 0,09 / −55,7% / 2,10% / 0,89 |

| Bloco agressivo (custo 0,2%) | Sequencial | Interseccional |
|---|---|---|
| Ações por carteira (mín / média / máx) | 6 / 6,9 / 7 | 23 / 24,7 / 26 |
| Giro médio por mês / giro anual | 76% / 914% | 47% / 563% |
| Custo anual do bloco | 1,83% | 1,13% |
| Valor de mercado mediano das escolhidas (média das datas; 2023-26) | R\$ 5,5 bi; R\$ 6,3 bi | R\$ 8,0 bi; R\$ 9,4 bi |
| Risco específico (1 − R² contra o universo) | 34% | 12% |
| Correlação diária com o defensivo | 0,67 | **0,80** |

Leitura:
- **O bloco continua com viés de tamanho.** A mediana das escolhidas (R\$ 8,0 bi) fica bem abaixo da mediana do universo (R\$ 14,4 bi), mas acima da das 30% menores (R\$ 5,1 bi).
- **O Size continua puxando para baixo.** O interseccional (7,82%) fica abaixo do Momentum sozinho (11,13%) e abaixo do CDI (9,93%), embora acima do Ibovespa (7,11%) e do universo peso igual (6,45%).
- **Ficou mais parecido com o defensivo** (correlação de 0,67 para 0,80), então diversifica menos a carteira.
- **Nada disso justifica mudar a regra:** a P18 foi registrada para ser mantida independentemente do resultado. O diagnóstico completo da variante nova está em `resultados/diagnostico_interseccional/` (`python src/diagnostico.py interseccional`).

**Robustez (Aula 3, plano da P20)**, 13/11/2026. Gerado por `python src/robustez.py` em `resultados/robustez/` (tabelas, gráficos, `resumo.md` e um tearsheet HTML do QuantStats para a carteira e para cada bloco). Estratégia congelada: as mudanças de código desta etapa só transformaram em parâmetro o que era fixo (`JANELA_FATORES_PRECO`, `FREQ_AGRESSIVO`, `FREQ_DEFENSIVO`, semestral em `datas_rebalanceamento`, `universo_por_piso`), e o padrão continua idêntico bit a bit (testado). Custo de 0,2%.

- **QuantStats:** funciona com o pandas 3.1, mas o HTML só aceita `rf` fixo. Usamos o CDI médio do período (10,09% a.a.). O Sharpe dele bate com o nosso, de CDI diário, na 2ª casa (0,15 / 0,21 / 0,04).
- **Ganhou do CDI?** No período todo, sim: carteira +1,13 p.p. a.a., defensivo +2,37 p.p., agressivo −2,11 p.p. e Ibovespa −2,82 p.p. Mas ano a ano a carteira ganha do CDI só em **8 de 16 anos**.
- **Subperíodos (CAGR da carteira):** 2011-14: 2,1% (CDI 9,7%); 2015-16: 9,8% (CDI 13,7%); **2017-19: 36,1%** (CDI 7,5%); 2020: −3,4%; 2021-22: −1,6% (CDI 8,4%); 2023-26: 15,1% (CDI 13,1%). A carteira bate o Ibovespa em 4 dos 6 subperíodos [corrigido na auditoria: eram 3, mais um empate em 2015-16, 9,8% × 9,8%; ver a robustez refeita abaixo], mas **o excesso sobre o CDI vem quase todo de 2017-19** (e de 2023-26). Em 2021-22, o defensivo segurou (3,9%) e o agressivo caiu (−12,8%).
- **Grades (Sharpe da carteira):** 12 combinações de janela {6, 9, 12} × rebalanceamento [corrigido na auditoria: são 9 combinações distintas, porque as 3 do rebalanceamento padrão aparecem nas duas grades]. Sharpe de 0,10 a 0,20 (padrão 0,15 = mediana), todos positivos; CAGR de 9,83% a 12,05%, acima do CDI em 11 de 12. Pela régua da Aula 3, **é robusta**: o resultado não depende de uma combinação só. Há um padrão consistente: o agressivo trimestral dá Sharpe maior em todas as janelas (+0,04 a +0,06, menos giro e custo), e o defensivo semestral dá menor. **Não muda o padrão** (P20): as diferenças estão dentro do ruído (ver anos de dado).
- **Fatias ±10 p.p.:** Sharpe de 0,13 a 0,17 e CAGR de 10,58% a 11,50% nas 6 variações; nenhuma muda o quadro.
- **Piso de volume no agressivo (teste, não candidato):** R\$ 1 mi/dia em reais de out/2026 (R\$ 0,41 mi nominais em 2010) dá um universo de 140 a 238 empresas, contra ~86. Agressivo 7,82% → 11,98% e carteira 11,06% → 12,65%. Porém as ações escolhidas negociam **8 vezes menos** (volume mediano de R\$ 6,7 mi/dia contra R\$ 55 mi; R\$ 3,8 mi em 2011-14), e o custo de 0,2% subestima o custo delas: o número é otimista. Sinal de que parte do prêmio de Size/Momentum está em ações menos líquidas, que um fundo real teria dificuldade de operar.
- **Anos de dado:** t ≈ Sharpe × √anos = 0,61 para a carteira, com 15,8 anos de dado. Para 95% de confiança seriam necessários **165 anos** (defensivo: 88; agressivo: 2.275). **O backtest não tem poder estatístico para afirmar que a estratégia supera o CDI**: o resultado é compatível com sorte. Isso vale para qualquer estratégia de ações com Sharpe dessa ordem, e é o argumento mais forte para não escolher parâmetros pelo backtest.

**P21 (defasagem por mês) e P22 (sem BDRs)**, 13/11/2026. As decisões foram registradas às 19:28, antes de medir. Cada uma foi medida sozinha e depois as duas juntas, que formam o **novo padrão**. Custo de 0,2%; formato: CAGR / Vol / Sharpe (CDI) / Max DD / Alpha.

| Estado | Carteira 65/35 | Defensivo | Agressivo |
|---|---|---|---|
| Antes (P18) | 11,06% / 20,0% / 0,15 / −43,7% / 3,02% | 12,30% / 19,5% / 0,21 / −37,9% / 4,04% | 7,82% / 24,1% / 0,04 / −55,7% / 0,95% |
| Só P21 | 10,68% / 20,0% / 0,14 / −45,3% / 2,67% | 11,74% / 19,4% / 0,18 / −39,8% / 3,52% | igual (não usa balanço) |
| Só P22 | 11,14% / 20,0% / 0,16 / −43,7% / 3,10% | 12,45% / 19,5% / 0,22 / −37,9% / 4,17% | 7,77% / 24,1% / 0,04 / −55,7% / 0,91% |
| **P21 + P22 (novo padrão)** | **10,98% / 20,0% / 0,15 / −45,3% / 2,94%** | **12,22% / 19,4% / 0,21 / −39,8% / 3,95%** | **7,77% / 24,1% / 0,04 / −55,7% / 0,91%** |

- **P21:** confirmado que, em 30 de 64 trimestres, o último pregão cai antes do último dia do mês (o balanço de 3 meses ficava invisível). Com a correção, o defensivo muda em **26 de 64 trimestres** (53 trocas).
- **P22:** a regra pegou 10 tickers, todos BDRs de empresas estrangeiras (AGEN33, AURA33, CZLT33, DAGB33, G2DI33, GBIO33, GPIV33, JBSS32, MILK33, PPLA35); nenhuma ação brasileira. Seis entravam no universo, e AURA33 (12 meses) e DAGB33 (2 meses) entravam no agressivo. A P22 muda o agressivo em 37 de 190 meses (o universo muda além das próprias BDRs) e o defensivo em 5 de 64 trimestres. PPLA11 e PPLA36 também são da PPLA, que é estrangeira, mas ficam fora da regra e nunca entram no universo.
- Os efeitos não se somam (−0,38 e +0,08 p.p. sozinhas, −0,08 p.p. juntas), porque a P22 muda o universo em que a P21 atua.

**Sequencial (regra pré-registrada na Entrega 1) × interseccional (revisão pós-diagnóstico, P18)**, com o novo padrão. As duas são apresentadas lado a lado (ver a nota da P18).

| | Custo | Sequencial: CAGR / Vol / Sharpe / Max DD / Alpha | Interseccional |
|---|---|---|---|
| Carteira 65/35 | 0,2% | 9,05% / 21,2% / 0,07 / −45,8% / 1,42% | 10,98% / 20,0% / 0,15 / −45,3% / 2,94% |
| Carteira 65/35 | 0% | 10,10% / 21,2% / 0,11 / −45,7% / 2,39% | 11,77% / 20,0% / 0,19 / −45,3% / 3,66% |
| Agressivo | 0,2% | 1,89% / 30,3% / −0,10 / −64,1% / −3,07% | 7,77% / 24,1% / 0,04 / −55,7% / 0,91% |
| Agressivo | 0% | 3,76% / 30,3% / −0,04 / −62,1% / −1,23% | 8,99% / 24,1% / 0,09 / −55,7% / 2,05% |

**Robustez refeita com o novo padrão (P21 + P22)**, 13/11/2026. `python src/robustez.py`; os diagnósticos (`diagnostico.py sequencial` e `interseccional`) também foram refeitos. Correções da auditoria aplicadas no script: combinações distintas da grade contadas pelos parâmetros efetivos; empate (< 0,1 p.p.) não conta como "bate"; e três medidas novas (intervalo do Sharpe, t do alpha e resultado sem 2017-19). O notebook foi atualizado e executado do início ao fim, e os números batem com `estrategia.py`.

- **CDI:** a carteira fica +1,05 p.p. a.a. acima do CDI no período (defensivo +2,29; agressivo −2,16; Ibovespa −2,82), mas só em 8 de 16 anos.
- **Subperíodos** (empate = diferença < 0,1 p.p.): a carteira **bate o Ibovespa em 3, perde em 3** e não empata em nenhum; bate o CDI em 2 e perde em 4. CAGR por subperíodo: 3,9% / 8,8% / 35,6% / −5,0% / −2,3% / 14,4%.
- **Sem 2017-19:** a carteira tem CAGR de **5,92%**, contra 10,52% do CDI e 3,41% do Ibovespa. O defensivo tem 7,84% e o agressivo 1,51%. **Todo o excesso sobre o CDI vem desses três anos.**
- **Grades:** **9 combinações distintas**, todas com Sharpe positivo (0,11 a 0,23; mediana 0,17; padrão 0,15) e CAGR acima do CDI (10,16% a 12,87%). O agressivo trimestral dá Sharpe maior em todas as janelas, e o defensivo semestral, menor. **As combinações usam os mesmos dados e não são evidências independentes**; o padrão não muda (P20).
- **Fatias ±10 p.p.:** Sharpe de 0,14 a 0,16 e CAGR de 10,84% a 11,30%.
- **Piso de volume:** carteira 12,57% e agressivo 11,93%, com as escolhidas negociando 8 vezes menos (R\$ 6,8 mi/dia contra R\$ 55 mi). Otimista pelo custo; a justificativa original do piso estava errada (ver P20).
- **Significância:** intervalo de 95% do Sharpe da carteira de **−0,35 a 0,64** (defensivo −0,29 a 0,70; agressivo −0,45 a 0,53). Alpha anual de 2,94% com **t (Newey-West, 9 defasagens) de 1,42**; excesso sobre o Ibovespa de 2,93% a.a. com t de 1,28. Defensivo: alpha de 3,95%, t de 1,73. Agressivo: t de 0,27. Nada é significativo a 95%; seriam necessários 173 anos de dado para a carteira (t = 0,59).


---

## 6. Estrutura do repositório

```
iqf-factor-strategy/
├── contexto.md          ← este arquivo
├── README.md
├── requirements.txt
├── data/
│   ├── raw/             ← xlsx do Economatica (fora do Git: ver .gitignore)
│   └── processed/       ← parquets limpos + relatorio_limpeza.md + benchmark_diario.parquet
├── src/
│   ├── limpeza.py       ← feito
│   ├── dados.py         ← feito: bases no formato do backtest + Ibovespa/CDI
│   ├── universo.py      ← feito: filtro de liquidez (P1)
│   ├── backtest.py      ← feito: loop da Aula 2
│   ├── fatores.py       ← feito: métrica e nota de cada fator por data
│   ├── estrategia.py    ← feito: blocos defensivo e agressivo, carteira 65/35
│   ├── metricas.py      ← feito: CAGR, Sharpe, drawdown, alpha/beta
│   ├── graficos.py      ← feito: gráficos da Aula 2
│   ├── diagnostico.py   ← diagnóstico do bloco agressivo (resultados/diagnostico/ = sequencial;
│                          resultados/diagnostico_interseccional/ = P18)
│   └── robustez.py      ← robustez da Aula 3 (P20, gera resultados/robustez/)
└── notebooks/
    └── entrega2_backtest.ipynb  ← resultado da Entrega 2 (métricas e gráficos)
```

⚠️ **Repositório privado.** Os dados do Economatica são licenciados para o Insper e não podem ficar públicos.

---

## 7. Cronograma

| Data | Entrega |
|---|---|
| 25/10 | Entrega 1: metodologia (feita) |
| 02/11 | Entrega 2: primeira versão do backtest |
| Semana de 03/11 | Aula de limpeza de dados (levar os dados baixados) |

---

## 8. Registro de uso de IA generativa

O uso de GenAI é **obrigatório** e vale **15% da nota** no Desafio (critério 4.7). Registrar aqui cada uso concreto: etapa, o que a IA fez, impacto.

| Data | Etapa | Ferramenta | O que foi feito | Impacto |
|---|---|---|---|---|
| 01/11/2026 | Coleta de dados | Claude | A partir dos slides, da Entrega 1 e da transcrição da aula, mapeou quais indicadores do Economatica medem cada fator e com quais parâmetros (ajuste por proventos, 12 meses, PL fim, frequência por base) | Reduziu as bases de 9 para 6 e evitou baixar dado diário desnecessário |
| 01/11/2026 | Validação dos dados | Claude | Conferiu as 6 planilhas (tickers, datas, unidades, coerência dos valores) e identificou bancos sem Dív/PL, patrimônio negativo, P/L negativo e a defasagem dos balanços | Armadilhas de ranking documentadas antes do backtest |
| 01/11/2026 | Limpeza | Claude | Escreveu o `limpeza.py`. Teste empírico mostrou que o P/L trimestral do Economatica usa lucro ainda não divulgado (look-ahead); propôs a correção via lucro implícito. Detectou erros de ajuste (ASAI3, GSHP3) | Mitigação de viés de look-ahead e de dados errados no backtest |
| 01/11/2026 | Verificação da limpeza | Claude | Conferiu os parquets antes do backtest e encontrou viés de sobrevivência (sem ações canceladas), quedas falsas não marcadas (PCAR3) e valor de mercado repetido entre classes | Limitações documentadas; universo com uma classe por empresa |
| 01/11/2026 | Backtest (etapas 1 a 3) | Claude | Propôs o roadmap em etapas e escreveu `dados.py`, `universo.py` e `backtest.py` (loop da Aula 2), com teste de sanidade contra o Ibovespa | Motor validado (correlação de 0,93 com o Ibovespa) antes de entrar a lógica dos fatores |
| 02/11/2026 | Comparação com os handouts | Claude | Comparou nosso código com os handouts 2 e 3 e listou as decisões que não estão neles (liquidez sem INEG, uma classe por empresa, buy-and-hold, Ibovespa/CDI) | Lista do que o grupo precisa saber defender na apresentação |
| 02/11/2026 | Estratégia e gráficos (etapas 4 a 9) | Claude | Escreveu `fatores.py`, `estrategia.py`, `metricas.py`, `graficos.py` e o notebook da Entrega 2. Implementou as duas opções de P3 e P12 para comparar. Encontrou e corrigiu o valor de mercado datado em fim de semana, que fazia o rebalanceamento usar o mês anterior | Primeira versão completa do backtest com os gráficos da Aula 2 |
| 13/11/2026 | Correção da Entrega 2 | Claude | Aplicou duas correções do monitor: (1) notas de Quality e Low Vol calculadas sobre o mesmo conjunto elegível (`elegiveis_defensivo` em `estrategia.py`, P14); (2) docstring do `universo.py`, que afirmava não haver viés de sobrevivência. Rodou as 4 combinações de P3 × P12 antes e depois, conferiu que as duas notas cobrem o mesmo conjunto em todos os trimestres e levantou outros pontos para o grupo decidir (Dív/PL de outro balanço que o ROE, mediana de Dív/PL dada a não financeiras) | Ranking do bloco defensivo metodologicamente consistente. Padrão rank/excluir inalterado (CAGR 11,33%); as outras combinações variam até 0,3 p.p. |
| 13/11/2026 | Correção do Quality (P15) | Claude | Fez ROE e Dív/PL virem do mesmo balanço e restringiu a mediana de Dív/PL às financeiras. Ao validar, descobriu que o Economatica nunca calcula ROE com PL negativo, o que desligaria a P3 com a regra pedida; propôs e aplicou a exceção (situação do PL tirada do balanço mais recente). Separou o efeito de cada parte nas 4 combinações e justificou manter o lucro do Value independente | Quality calculado com dados coerentes de um balanço só, sem reabrir a P3. Padrão: CAGR 11,33% → 11,30%, 1 trimestre alterado |
| 13/11/2026 | Custo de transação (P16) | Claude | Implementou no motor o custo proporcional ao giro (peso antigo já andado com os preços, montagem inicial e volta a 65/35 incluídas), testou que custo 0 reproduz o resultado anterior bit a bit, rodou a sensibilidade (0%, 0,1%, 0,2%, 0,5%) e decompôs o giro em troca de nomes e reequilíbrio para comparar com a estimativa do monitor | Resultado principal passa a incluir custos: CAGR da carteira 11,30% → 10,34% com 0,2%; o agressivo paga 1,6% a.a. de custo |
| 13/11/2026 | Base com canceladas (P11) | Claude | Rodou a limpeza na base nova (1.117 tickers, 94 financeiras), conferiu as financeiras que entram no universo, guardou a base antiga e mediu o efeito isolado do viés de sobrevivência nas duas bases, com e sem custo, além do teste de sanidade. Decompôs a causa: peso e retorno das ações canceladas em cada bloco | Viés medido: −1,33 p.p. no CAGR da carteira com custo (10,34% → 9,01%), maior no defensivo em p.p. A hipótese de que pesaria mais em Size/Momentum não se confirmou |
| 13/11/2026 | Identificação da empresa (P17) | Claude | Verificou que AMBV4 e ABEV3 têm o mesmo valor de mercado em todos os meses e que a Ambev é o único par desses no universo; implementou `identificar_empresas()` (4 letras ou mesmo valor de mercado) e testou que a base antiga não muda | Ambev deixa de contar duas vezes em 2011-13. CAGR da carteira com custo 9,01% → 8,96% |
| 13/11/2026 | Diagnóstico do bloco agressivo | Claude | Escreveu `diagnostico.py` (contribuição por ação, Size e Momentum separados no mesmo universo, tamanho em R\$ bi, concentração, subperíodos, momentum crash com estado definido antes de olhar o resultado, custo, papel na carteira) e classificou 11 hipóteses em confirmada/refutada/inconclusiva, sem mudar a estratégia | Causa principal identificada: o Size falha (−1,9% a.a.) e o funil sequencial leva o Momentum (11,1% sozinho) para o pior pedaço do universo. Base para a mudança lógica do bloco, a justificar pela literatura |
| 13/11/2026 | Bloco agressivo interseccional (P18) | Claude | Registrou a P18 no contexto (17:48) antes de rodar a variante; implementou `COMBINACAO_AGRESSIVO` com a regra interseccional (mesmo conjunto elegível da P14, mesma fatia de 30%), mantendo a sequencial para comparação e testando que ela reproduz o resultado anterior bit a bit; adaptou `diagnostico.py` para rodar qualquer combinação sem copiar a regra; comparou as duas versões sem propor ajustes | Carteira com custo 8,96% → 11,06% (acima do CDI); agressivo 1,41% → 7,82%, com 25 ações em vez de 7. O bloco segue abaixo do CDI e mais correlacionado com o defensivo (0,80) |
| 13/11/2026 | Robustez (P19, P20) | Claude | Registrou a P19 (correção 5 não aplicada) e o plano da P20, com a justificativa do piso de volume, antes de rodar. Transformou em parâmetro a janela dos fatores de preço, a frequência de cada bloco e o universo por piso, testando que o padrão fica idêntico bit a bit. Escreveu `robustez.py` (tearsheets do QuantStats, contornando o `rf` fixo do HTML; excesso sobre o CDI; subperíodos; grades; fatias; piso de volume com IPCA; anos de dado), sem recomendar parâmetros | Estratégia robusta a parâmetros (Sharpe de 0,10 a 0,20 em 12 combinações), mas sem significância estatística (t = 0,61; seriam necessários 165 anos) e com o excesso sobre o CDI concentrado em 2017-19 |
| 13/11/2026 | Auditoria independente | Outro modelo de IA (só leitura) | Auditou o repositório sem alterar nada e apontou: defasagem dos balanços de 3 ou 6 meses conforme o calendário (comparação dia × mês), BDRs no universo, P18 apresentada como pré-registrada, contagem de 12 combinações na grade (eram 9), empate contado como vitória nos subperíodos, justificativa do piso da P20 baseada num volume errado, P5 assimétrica, anualização com 252 pregões, sobreposição entre blocos e documentação desatualizada (README, notebook). O grupo conferiu por fora o item da defasagem (30 de 64 trimestres) | Gerou as decisões P21 e P22 e as correções de documentação e de análise abaixo |
| 13/11/2026 | Correções da auditoria (P21, P22) | Claude | Registrou a P21 e a P22 (19:28) antes de medir; implementou a comparação por mês em `Dados.janela` e a exclusão de BDRs em `universo.py`; conferiu que os 10 tickers excluídos são todos BDRs; mediu cada correção sozinha e as duas juntas; acrescentou a nota de exatidão à P18; corrigiu a robustez (9 combinações, empates, intervalo do Sharpe, t do alpha com Newey-West, resultado sem 2017-19); mediu o volume real da 90ª ação e corrigiu a P1 e a P20; registrou as limitações conhecidas; atualizou o README e o notebook e executou o notebook do início ao fim | Novo padrão: carteira 10,98% (Sharpe 0,15). O excesso sobre o CDI desaparece sem 2017-19 (5,92% contra 10,52%), e nenhuma medida é significativa a 95% (t do alpha de 1,42) |
