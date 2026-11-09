# Refinamento da tese e resultados v3

Extensão retrospectiva: os resultados originais já haviam sido examinados. Os parâmetros próprios foram congelados antes desta execução. A validação temporal não é um holdout prospectivo intocado. Ver auditoria/MODELAGEM_REVISAO.md.

## Problema e tese

O acesso 24/7 separa a possibilidade de negociar do custo de acompanhar e capturar uma referência. Medimos fidelidade, ajuste após a reabertura, previsibilidade temporal e condições econômicas. Previsibilidade não comprova execução, arbitragem sem risco ou a causa do comportamento dos preços.

## Contrastes dentro dos mesmos fins de semana

Valores negativos indicam queda do desvio absoluto. São médias de diferenças dentro de cada semana, não diferenças entre medianas independentes. Intervalos de 95% são exploratórios, em blocos de semanas do calendário, e não cobrem seleção por dados faltantes ou erro de mensuração.

```text
 comparison  paired_n  mean_abs_change_bps    mean_lo    mean_hi
 b_c_to_b_0       301            20.151430  14.017348  27.157648
b_0_to_b_1h       301           -11.001850 -15.208877  -7.165837
b_0_to_b_7h       301           -15.347091 -20.239739 -10.675969
```

## Modelo e validação

O alvo é o desvio em +7h, observado após a decisão em +1h. O treino começa com 104 semanas de calendário e cresce usando apenas alvos já concluídos. O modelo principal é um ajuste linear com b_1h; a alternativa com contexto acrescenta o salto do ouro e volatilidade anterior. Todas as cinco previsões usam a mesma amostra de teste. Resultado principal: ausência de melhora de MAE frente à persistência. Uma diferença de MAE abaixo de zero favorece o modelo; o intervalo e as referências simples devem ser considerados em conjunto.

```text
                    model  n_test   mae_bps  rmse_bps  mae_skill_vs_persistence  difference_lo  difference_hi
              persistence     204 16.456693 24.642060             -2.220446e-16       0.000000       0.000000
               zero_basis     204 51.786208 68.328948             -2.146817e+00      27.607114      43.702180
          historical_mean     204 56.373851 74.292315             -2.425588e+00      30.550027      50.066533
        linear_adjustment     204 17.721783 26.050482             -7.687390e-02      -0.350822       3.014158
linear_adjustment_context     204 18.208884 26.438847             -1.064728e-01      -0.018582       3.568369
```

## Alinhamento cambial e amostra

Janelas de busca de 1 e 5 minutos usam closes observados de câmbio já concluídos. A janela de cinco permite carregar um close concluído por até quatro minutos. Token e ouro permanecem no minuto exato de execução e com atividade. A janela de um minuto reproduz numericamente o resultado original. A alternativa não substitui o primário nem habilita cenários anuais. T9_fx_common_sample.csv separa o efeito sobre a mesma amostra do efeito de incluir novas trajetórias.

```text
 fx_window_minutes  valid_paths  evaluated_trades  unassessed_signals  mean_model_bps
                 1           55                44                  16      -40.012539
                 5           86                66                   2      -39.757042
```

## Ausências e economia

Para zerar a média agregada dos 60 sinais observados elegíveis em 6h, os 16 não avaliados precisariam ter saldo médio de 110.03 bps. Não atribuímos esse saldo a eles. Esse exercício não cobre as semanas sem sinal observável, nem identifica o mecanismo das ausências.

A grade original tem 1458 combinações e 0 médias positivas. A melhor média é -2.88 bps, escolhida retrospectivamente da grade, e não uma estratégia validada para uso futuro. Orçamento de custo e reduções necessárias são identidades contábeis da média amostral; não previsões. Custos financeiros e acesso a empréstimo continuam desconhecidos.

## O que a extensão muda

O trabalho passa a distinguir ajuste observado, capacidade de prever e capacidade de executar. O modelo acrescenta uma comparação temporal verificável, inclusive quando não supera uma referência. O estudo permanece específico a PAXG e às fontes disponíveis. Não há conclusão causal sobre infraestrutura/competição, auditoria de reservas ou previsão de amadurecimento. Custos de manutenção e horizontes contra ETFs continuam condicionais à rota, às taxas e ao armazenamento.
