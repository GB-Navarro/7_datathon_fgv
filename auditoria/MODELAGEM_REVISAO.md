# Revisão crítica e modelagem — extensão v3

## Pergunta e decisão

O problema é a diferença entre acesso contínuo e captura econômica. O estudo original descreve o desalinhamento e encontra médias negativas nas condições simuladas. Melhorar a pesquisa significa testar a persistência do desvio, comparar previsões com referências simples e explicitar o quanto a conclusão depende de custos e informação incompleta.

Esta extensão foi definida depois de conhecidos os resultados originais. A separação temporal das previsões evita usar o alvo futuro no ajuste de cada modelo, mas não transforma o histórico já examinado em uma validação prospectiva inédita. O snapshot da execução v2 está em `historico/execucao_v2/`. Os parâmetros originais continuam congelados; os novos estão em `config/refinement.json`, com snapshot próprio antes da execução.

## Fontes primárias pesquisadas

1. Hyndman e Athanasopoulos, [Forecasting: Principles and Practice, validação temporal](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation). A avaliação por origens sucessivas estima o modelo com observações anteriores ao teste e compara erros de previsão. Aplicação: janela de treino expansiva, sem divisão aleatória, com persistência, zero e média histórica como referências. Não presumimos que um modelo ajustado vence uma referência simples.
2. Bailey, Borwein, López de Prado e Zhu, [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). A escolha da melhor variante após examinar muitas simulações pode produzir desempenho aparente. Aplicação: registrar todos os modelos e a grade econômica, sem escolher taxas ou horizontes para obter lucro. O método CSCV do artigo não foi implementado nem necessário para a pergunta delimitada desta extensão.
3. Lo e MacKinlay, [An Econometric Analysis of Nonsynchronous Trading](https://www.nber.org/papers/w2960). Negociação infrequente e observações não simultâneas alteram propriedades temporais de retornos. Aplicação: separar previsibilidade de executabilidade; auditar relógios e repetir a simulação com tolerância cambial explícita. O artigo não determina uma tolerância universal de cinco minutos. O valor 5 já constava das sensibilidades do projeto e permanece uma hipótese de alinhamento, não preço garantido de execução.
4. Documentação oficial [pandas.merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html). A busca backward associa a última observação anterior, com tolerância explícita. Aplicação: usar apenas closes cambiais concluídos, registrar o timestamp e idade, sem buscar uma cotação futura ou carregar ouro pelo fechamento do mercado.
5. Documentação oficial [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) e [cointegração](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html). Uma regressão direta é suficiente para comparar previsões de curto prazo do desvio. Testes de cointegração pressupõem condições sobre as séries. Não chamamos o modelo de VECM, não estimamos uma relação causal e não inferimos eficiência de mercado a partir de uma regressão.

## Ajustes efetivamente justificados

- Comparação pareada: mudanças em `|basis|` dentro dos mesmos fins de semana, em vez de interpretar uma diferença de medianas de grupos como um efeito individual. Intervalos exploratórios usam blocos do calendário, preservando semanas ausentes.
- Modelo linear de ajuste: prever o desvio em +7h a partir de +1h. A alternativa com contexto acrescenta o salto do ouro na reabertura e volatilidade calculada exclusivamente antes dela. Os primeiros 104 fins de semana de calendário formam a janela inicial; exigem-se pelo menos 78 observações de treino. Cada alvo de treino precisa estar concluído antes da previsão.
- Cinco referências/modelos, todos reportados: persistência, desvio zero, média histórica, ajuste linear e ajuste linear com contexto. Métricas: MAE, RMSE e diferença pareada de perdas contra persistência. Não se converte erro menor em uma promessa de lucro.
- Dados ausentes: calcular a média que os sinais não avaliados precisariam apresentar para zerar o resultado agregado. A tabela de sensibilidades não imputa esses valores como observados.
- Câmbio: comparar tolerâncias de 1 e 5 minutos, mantendo entrada/saída de token e ouro no minuto exato e ativo. Sinais e cotações disponíveis antes da decisão são obrigatórios. O cenário de cinco minutos não substitui o primário nem desbloqueia o ramo anual cuja amostra original foi insuficiente.
- Economia: mostrar o orçamento de custo dado pelo ganho bruto, a grade completa de custos e a dependência dos horizontes de manutenção em relação a armazenamento e rota de acesso.

## O que não acrescentar

Redes neurais e buscas extensas de hiperparâmetros não resolvem poucos episódios independentes, custos desconhecidos e ausência de livro histórico. Um modelo pode melhorar a previsão de preços e continuar incapaz de identificar arbitragem executável. A tendência trimestral original não será reespecificada para tentar obter significância. Os multiplicadores dos cenários continuam hipóteses.

## Comunicação final

Dez slides principais seguem problema → método → evidência → modelagem → economia → decisão. Três anexos mostram grade econômica, comparação completa dos modelos e fontes/reprodução. O Áureo v2 é aplicado ao conteúdo científico; as lâminas de paleta e tipografia pertencem ao estudo de identidade e não entram na apresentação de entrega.
