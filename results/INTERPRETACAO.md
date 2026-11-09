# Interpretação dos resultados

Este texto é gerado das tabelas e de claims.csv; não é uma previsão nem recomendação individual.

## Amostra e qualidade

Foram analisadas 36.572 horas válidas e 301 dos 323 fins de semana candidatos. O primário usa preços em USD observados, sem preencher câmbio ausente nem barras de ouro inativas. Exceções de calendário não confirmadas ficam fora do primário, registradas em exclusions.csv.

A sobreposição sistemática das fontes de câmbio teve diferença absoluta mediana de 6,50 bps, em 3.168 horas. QA_currency_robustness.csv compara a fidelidade na mesma subamostra com as duas fontes e identifica separadamente a hipótese USDT=USD. A checagem independente do ouro contra preço GLD/onças por cota está em QA_gold_reference_summary.json; o proxy do ETF não equivale a uma cotação física executável.

## Fidelidade e reabertura

Em horários comuns, a mediana absoluta foi 36,38 bps log e o p95 foi 120,12 bps log. Na reabertura, os valores foram 48,44 e 164,18 bps log. O desvio absoluto superou 50 bps em 48.50% dos fins de semana válidos.

A mediana após uma hora foi 37,14 bps log; após sete horas, 37,99 bps log. A trajetória não deve ser confundida com lucro de convergência: o P&L usa preços e quantidades fixas nas duas pernas. A figura de trajetória usa somente fins de semana com os três instantes válidos, e os intervalos são exploratórios em blocos semanais.

## Convergência condicional

Nos últimos 104 fins de semana de calendário, houve 55 trajetórias completas e 44 operações sinalizadas avaliadas. Outros 16 sinais não tiveram avaliação completa; não foram contabilizados como zero nem declarados sem oportunidade.

O ganho bruto médio por operação foi 4,53 bps por perna de ouro, contra 44,54 bps de custo total modelado. Após esses custos da hipótese-base, mas antes de empréstimo/financiamento não observados, a média foi -40,01 bps e a pior operação foi -115,27 bps. A fração positiva nesse cenário foi 0.00%.

Esses valores são condicionais a taxa de token 10,00 bps por execução, spread cheio suposto 10,00 bps, comissão de ouro 1,00 bps por execução, conversão total 2,00 bps e slippage 2,00 bps por execução. A grade completa está em T2_convergencia.csv. Não se conclui inexistência de arbitragem em outros venues, custos, horizontes ou situações sem dados de saída.

## Token versus ETF

Na hipótese-base de custo, o token tem 32,00 bps de ida e volta. Os cruzamentos são 9,30 meses contra GLD e 37,20 meses contra GLDM. Taxas e spread mediano corrente dos ETFs são documentados; taxas, spread do token e conversão são hipóteses. O cálculo pressupõe USD, antes de impostos, mesma possibilidade de acesso e ausência de retirada na rota-base. O arquivo T3_custos_etfs.csv inclui mudanças de tamanho, custos fixos, taxas, spreads, armazenamento e casos sem cruzamento ou com reversão da vantagem.

## Evolução e cenários

A tendência foi estimada em 24 trimestres completos. A inclinação no log da mediana absoluta por ano foi -0,09, com intervalo de -0,25 a 0,07. O intervalo inclui zero; não há demonstração estatística de melhora nesse desenho. Isso não é prova de ausência de melhora nem identifica competição ou infraestrutura como causas.

O método efetivamente aplicado aos cenários foi `deterministic_sensitivity_insufficient_joint_paths`. O mínimo pré-definido de trajetórias conjuntas para reamostragem anual não foi reduzido para produzir um resultado mais atraente. Quando o gate falha, a saída é sensibilidade determinística; o ramo estocástico permanece implementado e testado com dados sintéticos de teste, que não aparecem como resultados de mercado.

Menor atrito mantém os caminhos de preço e reduz custos modelados, levando a média condicional a -17,74 bps. O estresse hipotético altera preços e atritos e produz -84,06 bps. Esses cenários não são trajetórias prováveis ou datas previstas de maturidade.

## Limites que permanecem

OHLC de minuto não reconstrói livro, impacto ou latência real. Dados faltantes podem selecionar uma amostra diferente dos momentos mais difíceis de operar. Intervalos de reamostragem não cobrem custos omitidos ou erros de modelo. Custódia, resgate, elegibilidade e empréstimo são restrições documentais e específicas do participante. O trabalho informa uma decisão sob condições explícitas e não atribui causalidade à maturidade do mercado.
