# Plano v5: modelagem, tese e relatório final

Data: 08/11/2026. Prazo: 23h59 (Brasília). Este plano substitui a estrutura de slides da v4 e mantém todos os resultados anteriores.

## 1. O que aprendemos com as edições anteriores

| Ano | 1º lugar | 2º | 3º |
| --- | --- | --- | --- |
| 2023 | Sentic Crypto: previsibilidade do prêmio de risco com indicadores técnicos e sentimento (finBERT + PCA) | HAS: transformers e movimentos de baleias | CriptoGirls: alocação em BTC e ETH |
| 2024 | Crypto X Quant: volatilidade com GARCH, LSTM, RF e AFTER; estratégia com Sharpe | Polichain: fraude em contratos Ethereum com ML | CearáCoin: gestor de carteira |
| 2025 | Hermes: simulação de investidores com IA | Eurytion (USP, parte desta equipe): carteira com IA em cascata | Out-of-Sample: risco DeFi vs RWA e previsão de spread on-chain |

O padrão dos vencedores é este: uma pergunta ligada a uma literatura citada, um modelo com teste fora da amostra e uma aplicação prática medida por uma métrica de desempenho (Sharpe, drawdown). O rigor estatístico é moderado; as divisões são simples (80/20), e os custos aparecem pouco. O material de abertura de 2026 (citado no repositório público de outra equipe) pede **PDF com no máximo 10 slides**, sugere RWAs e stablecoins entre os temas e avalia relevância, adequação metodológica, qualidade, criatividade e análise das implicações. Mentores, se houver, precisam ser creditados.

O que nos faltava frente a esse padrão: (a) um resultado prático positivo, (b) um modelo que explique o comportamento do desvio, (c) literatura citada no corpo do trabalho e (d) a entrega em até 10 páginas.

## 2. O que mudou na modelagem (já executado e conferido)

| Bloco | Modelo | Resultado | Arquivo |
| --- | --- | --- | --- |
| Duas velocidades | Nível local + AR(1) + ruído (statsmodels UnobservedComponents), dias úteis | Transitório com meia-vida de 3,8 pregões; choque do nível de 55 bps/ano | T15_componentes.json |
| Ajuste ao ouro | Correção de erro diária com erros HAC | PAXG acompanha 94,6% do retorno do ouro no dia; corrige 15% do desvio por dia (meia-vida 4,2 pregões) | T16_correcao_de_erro.json |
| Fim de semana | Gap do ouro na reabertura contra o movimento do PAXG no fim de semana | R² 0,16 no total, 0,66 em 2026; prêmio de fim de semana de +14,2 bps (ep 3,6), mediana +6,1 | T13_* |
| Risco de base | Variação do desvio por horizonte | DP de 81 bps em 12 meses, 8 vezes a taxa anual do GLDM | T14_risco_de_base.csv |
| Rotação GLDM ↔ PAXG | Regra de faixa fixa igual ao custo de um ciclo, sinal diário, execução no pregão seguinte | +130 bps/ano contra o GLDM (IC90 52 a 212), 26 ciclos, 77% positivos; nenhum de 1.000 placebos chegou lá | T12_* |

A tese passa a ser: **o desvio tem um componente rápido, que a arbitragem de horas não paga, e um nível lento, que um investidor que já quer ouro consegue capturar trocando de veículo, sem venda a descoberto.**

## 3. Validação do plano

| Risco | Checagem feita | Resultado |
| --- | --- | --- |
| Dado futuro na rotação | Teste unitário: alterar dados depois do dia 200 não muda nenhuma decisão anterior; execução no pregão seguinte | Passa (tests/test_rotation.py) |
| Ganho vindo de ruído de hora | Comparamos execução na hora seguinte com execução diária | Na hora seguinte o ganho caía para perto de zero com atraso de um dia; por isso a versão final usa média diária de 15 a 20 UTC e execução no pregão seguinte |
| Extremos serem erro de dado | Kraken PAXG/USD nas datas mais extremas | Mar/2024: Kraken −255 a −323 bps contra Binance −230 a −295; jun/2023: −141 a −232 contra −164 a −249 |
| Escolha da faixa depois de ver o dado | Faixa = custo de um ciclo, sem parâmetro estimado; grade de 10 a 50 bps; atraso de 2 pregões; variante com nível móvel de 60 dias; placebo; duas metades | Positiva em todas as faixas ≥ custo nos dois cenários; mais fraca com custos originais e nível móvel (+12 a +25 bps/ano) |
| Benefício só de um episódio | Resultado por ano | 2022 +93, 2023 +166, 2024 +375, 2025 +127, 2026 +42 bps; 2020–2021 sem operação |
| ETF fora do horário | Sinal e execução só em 15–20 UTC de dias úteis da NYSE; feriados da NYSE excluídos | Feito |
| ETF diferente do ouro | Conferência ouro × GLD/onças | Diferença mediana de 1,5 bps |
| Capacidade | 5% do volume diário da Binance nas horas de pregão | US$ 32 mil (2023) a US$ 310 mil (2026) por pregão |
| Impostos | Não modelados | Declarado: cada troca realiza ganho de capital |
| Pior momento | Queda relativa marcada a mercado | −298 bps em mar/2024 (desconto confirmado na Kraken) |

Conclusão da validação: os resultados se sustentam com custos, atraso, placebo e checagem em outra corretora. O ponto fraco é que a regra foi desenhada depois da análise original; isso fica escrito no slide e mitigado pela grade, pelo placebo e pela regra fixada pelo custo.

## 4. Relatório (versão final)

- 8 páginas principais e 5 de material suplementar em PDF separado (o material de abertura pede até 10 slides).
- Identidade visual da equipe (sistema Áureo: carvão, marfim, ouro, DM Serif Display, Manrope, IBM Plex Mono e o símbolo das duas barras). Do relatório de referência veio só a forma de ler: páginas densas, parágrafos explicativos, legendas "Fig. N" e uma régua de passos para cada operação.
- Sem frases de efeito e sem página de uso de IA; a última página é a conclusão, que responde às três perguntas da página 1.
- Roteiro na página 1 com o número-chave de cada página; cada página termina com uma frase que leva à próxima.
- Todos os números vêm de results/; o gerador é src/report_v5_build.py.

## 5. Validação final do conteúdo

| Checagem | Resultado |
| --- | --- |
| Faixa do nível na conclusão | Corrigida: nível estimado de −79 a +94 bps; −308 bps é o pior dia, não o nível |
| De onde vem o ganho da rotação | 86% de ciclos com mais de uma semana; texto diz "viradas do nível", não só "nível" |
| "A reabertura herda a sexta" | R² de 0,54 (reabertura) e 0,64 (7 h) contra o desvio de sexta; mesmo sinal em 83% |
| Custo de criar e resgatar PAXG | Corrigido: só o resgate custa 0,125% a 0,5%; criação isenta até 2027 |
| Token compensa contra ETF? | Coerente entre páginas 7 e 8: compensa em custo após 3,9/15,6 meses, mas o risco de base de 12 meses é maior que a economia |
| Números iguais em todas as páginas | +130, 52 a 212, −22,0, 3,9, 15,6, 81, 14,2, 74%, −79/+94 e 1.458 conferidos por extração do PDF |
| Linguagem | Sem "não é X, é Y", sem palavras de efeito; travessão só nas legendas |
| Layout | Nenhum elemento abaixo de 850 px ou fora da margem (QA automático) e revisão visual das 13 páginas |

## 6. Versão de 10 slides (pedido da equipe)

| Slide | Conteúdo | Mudança |
| --- | --- | --- |
| 1 | Capa | Layout da capa Áureo; título "PAXG contra o ouro." e a pergunta de pesquisa no lugar de frase de efeito |
| 2 | Problema, três perguntas e tese | Novo desenho em marfim; cada pergunta indica os slides que a respondem |
| 3 | Dados e medida | Texto mais curto; seis cartões de amostra e checagens |
| 4 | O desvio tem dois ritmos | Texto mais curto |
| 5 | Fim de semana | Cartão de previsão resumido em uma frase |
| 6 | Arbitragem em horas | Sem mudança de conteúdo |
| 7 | Rotação: regra e resultado | Primeira metade da antiga página de rotação |
| 8 | Rotação: robustez | Novo: tabela de configurações, placebo e riscos |
| 9 | Quem só carrega | Linha de emissor e corretoras de volta à tabela |
| 10 | Conclusão | Novo desenho: faixa com a resposta e uma resposta numerada por pergunta |

Validação: as referências cruzadas (slides 3 a 5, 6 a 8 e 9) batem com a estrutura; a conclusão responde às três perguntas do slide 2; nenhum elemento passa de 850 px; números conferidos por extração do PDF.
