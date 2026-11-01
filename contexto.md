# Contexto do projeto — Estratégia de Factor Investing (IQF / Desafio Quant AI 2026)

Este arquivo registra **o que decidimos e por quê**. Leia antes de mexer no código.
Atualize sempre que uma decisão mudar (com data).

_Última atualização: 01/11/2026_

---

## 1. A estratégia (Entrega 1)

Carteira de **risco moderado**: a maior parte protege, a menor busca crescimento.
**Meta:** no backtest, superar o Ibovespa com quedas (drawdowns) menores que as do mercado.

**Universo:** ações do Ibovespa. **Benchmark:** Ibovespa.

### Bloco defensivo: 65% da carteira, rebalanceado a cada 3 meses
1. **Quality + Low Vol (interseccional):** nota combinada = Quality (ROE alto, dívida baixa) + Low Vol (baixa volatilidade). As duas notas são somadas para nenhuma dominar.
2. Ficam as **30% melhores** pela nota combinada.
3. **Value (sequencial):** entre elas, ficam as **50% mais baratas** pelo P/L.
4. Peso igual entre as ações selecionadas.

### Bloco agressivo: 35% da carteira, rebalanceado todo mês
1. **Size:** as **30% menores** por valor de mercado.
2. **Momentum (sequencial):** entre elas, ficam as **30% com maior retorno em 12 meses, ignorando o último mês** (12-1).
3. Peso igual entre as ações selecionadas.

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

Baixado em **01/11/2026** pelo Felipe (só funciona no Wi-Fi do Insper).

**Universo bruto:** Screening → Ações → "Básico: Ações negociadas na Bovespa" (475 tickers, **incluindo ações canceladas**, o que evita viés de sobrevivência).

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

| # | Tratamento | Motivo | Números (rodada de 01/11/2026) |
|---|---|---|---|
| 1 | Remove as 3 linhas de lixo do topo e extrai o ticker do cabeçalho multilinha | Formato do export do Economatica | — |
| 2 | `"-"` → vazio (NaN) | É como o Economatica marca ausência de dado | — |
| 3 | Remove tickers sem nenhum preço desde 2000 | Inúteis para o backtest | 49 removidos, **426 mantidos** |
| 4 | Remove linhas inteiramente vazias da base diária | Feriados / dias sem pregão | 349 dias |
| 5 | Remove preço com volume zero ou ausente | Não é negócio real. Ex.: ASAI3 tinha um "preço" em 26/02/2021, antes da estreia, que gerava um falso +386% | 154 linhas |
| 6 | `retorno` = variação sobre o último preço disponível da mesma ação | Como o preço é ajustado, já é o retorno total (com dividendos) | — |
| 7 | Marca `retorno_suspeito` quando o retorno diário passa de 100% (**não remove**) | Erros de ajuste no Economatica. Ex.: GSHP3 +13.900% em 27/03/2019, grupamento não ajustado | 249 casos, 43 com volume > R\$ 1 mi |
| 8 | Valor de mercado: carrega o valor do mês anterior por até 2 meses (`preenchido = True`) | Ação sem negócio no último dia do mês | 2.945 valores |
| 9 | Descarta trimestres que ainda não terminaram | A linha 4T2026 do P/L é só o P/L de hoje | — |
| 10 | `data_disponivel = fim do trimestre + 3 meses` | **Defasagem de divulgação** (prazos da CVM: ITR em 45 dias, DFP anual em 3 meses). Evita look-ahead bias | — |
| 11 | `lucro_12m_mil` = valor de mercado no fim do trimestre ÷ P/L | Ver "Descoberta sobre o P/L" abaixo | — |
| 12 | Flags `pl_negativo`, `patrimonio_negativo`, `provavel_financeira` | Armadilhas de ranking (ver pendências) | P/L < 0 em 18,3% das obs.; Dív/PL < 0 em 3.079 obs.; 35 financeiras |

### Descoberta sobre o P/L (importante para o backtest)
Testamos de onde vem o lucro do P/L trimestral do Economatica comparando o lucro implícito (valor de mercado ÷ P/L) entre linhas. Nas empresas que já tinham divulgado o 3T2026, a linha "3T2026" já usa o lucro do 3T2026, que não era conhecido em 30/09. Ou seja, o teste indica que a linha do trimestre *q* usa o **lucro do próprio trimestre *q***, divulgado semanas ou meses depois. Vale confirmar com a mentoria. Usar o P/L "de 30/09" no rebalanceamento de 30/09 seria usar informação do futuro.

**Solução:** extraímos o lucro implícito (`lucro_12m_mil = valor de mercado / P/L`) e, no backtest, recalculamos o indicador de Value com informação disponível na data:

$$
L/P_{i,t} = \frac{\text{lucro\_12m}_{i}\ \text{(último com data\_disponivel} \le t)}{\text{valor de mercado}_{i,t}}
$$

Isso combina o preço atual com o último lucro já divulgado, que é o que um investidor de verdade teria. Também resolve o P/L negativo (ver pendências).

Conferência: WEGE3 tem lucro 12m implícito de cerca de R\$ 6,3 bi, coerente com o lucro reportado.

---

## 4. Decisões pendentes (discutir com o grupo)

| # | Questão | Recomendação |
|---|---|---|
| P1 | **Universo:** não temos a composição histórica do Ibovespa | A cada rebalanceamento, usar as ~90 ações com maior volume financeiro médio nos últimos 3 meses e negociadas em ≥ 90% dos pregões. Imita os critérios do Ibovespa, sem viés de sobrevivência |
| P2 | **Financeiras sem Dív/PL** (35 tickers, ex.: ITUB4, BBDC4, BBAS3, BPAC11, BBSE3) | Nota neutra (mediana) no componente de dívida do Quality. ROE e L/P valem normalmente |
| P3 | **Patrimônio líquido negativo** (Dív/PL < 0) | Pior nota em Quality ou excluir. Num ranking ingênuo de "menor dívida", essas empresas apareceriam como as melhores |
| P4 | **P/L negativo** (prejuízo) | Ranquear por L/P (lucro ÷ preço). Prejuízo vira L/P negativo e vai para o fim da fila automaticamente |
| P5 | **`retorno_suspeito`** | Tratar o retorno marcado como 0 (no retorno da carteira e no Momentum). É conservador: pode cortar um ganho real raro, mas impede ganhos falsos. A maioria está em ações ilíquidas que o filtro P1 já remove |
| P6 | **Início do backtest** | Jan/2011. Dados a partir de 2010 servem de histórico para Momentum/Low Vol de 12 meses, e o IFRS (contabilidade comparável) vale desde 2010. Pega a crise de 2015-16, a Covid e o ciclo de juros de 2021-22. Justificar no relatório (critério "escolha não oportunista de período") |
| P7 | **Datas de rebalanceamento** | Último pregão de cada mês (agressivo) e de mar/jun/set/dez (defensivo) |
| P8 | **"Small caps" dentro do Ibovespa** | As 30% menores do Ibovespa são, na prática, mid caps. Reconhecer essa limitação no relatório |
| P9 | **Custos de transação** | Começar sem custo. Depois testar algo como 0,1% por operação para ver a sensibilidade, já que o bloco mensal gira bastante |

---

## 5. Estrutura do repositório

```
iqf-factor-strategy/
├── contexto.md          ← este arquivo
├── README.md
├── requirements.txt
├── data/
│   ├── raw/             ← xlsx do Economatica (fora do Git: ver .gitignore)
│   └── processed/       ← parquets limpos + relatorio_limpeza.md
├── src/
│   ├── limpeza.py       ← feito
│   ├── fatores.py       ← próximo: notas de cada fator por data
│   ├── backtest.py      ← loop da Aula 2
│   └── metricas.py      ← CAGR, Sharpe, drawdown, alpha/beta
└── notebooks/           ← exploração e gráficos
```

⚠️ **Repositório privado.** Os dados do Economatica são licenciados para o Insper e não podem ficar públicos.

---

## 6. Cronograma

| Data | Entrega |
|---|---|
| 25/10 | Entrega 1: metodologia (feita) |
| 02/11 | Entrega 2: primeira versão do backtest |
| Semana de 03/11 | Aula de limpeza de dados (levar os dados baixados) |

---

## 7. Registro de uso de IA generativa

O uso de GenAI é **obrigatório** e vale **15% da nota** no Desafio (critério 4.7). Registrar aqui cada uso concreto: etapa, o que a IA fez, impacto.

| Data | Etapa | Ferramenta | O que foi feito | Impacto |
|---|---|---|---|---|
| 01/11/2026 | Coleta de dados | Claude | A partir dos slides, da Entrega 1 e da transcrição da aula, mapeou quais indicadores do Economatica medem cada fator e com quais parâmetros (ajuste por proventos, 12 meses, PL fim, frequência por base) | Reduziu as bases de 9 para 6 e evitou baixar dado diário desnecessário |
| 01/11/2026 | Validação dos dados | Claude | Conferiu as 6 planilhas (tickers, datas, unidades, coerência dos valores) e identificou bancos sem Dív/PL, patrimônio negativo, P/L negativo e a defasagem dos balanços | Armadilhas de ranking documentadas antes do backtest |
| 01/11/2026 | Limpeza | Claude | Escreveu o `limpeza.py`. Teste empírico mostrou que o P/L trimestral do Economatica usa lucro ainda não divulgado (look-ahead); propôs a correção via lucro implícito. Detectou erros de ajuste (ASAI3, GSHP3) | Mitigação de viés de look-ahead e de dados errados no backtest |
