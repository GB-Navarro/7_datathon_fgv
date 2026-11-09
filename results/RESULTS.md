# Resultados do projeto

Resultados empíricos e cenários condicionais. Cada linha abaixo possui origem em claims.csv.

| ID | Valor | Unidade | Arquivo | Condição |
| --- | --- | --- | --- | --- |
| candidate_weekends | 323 | weekends | results/panel_status.json |  |
| valid_weekends | 301 | weekends | results/panel_status.json |  |
| valid_hours | 36572 | hours | results/panel_status.json |  |
| common_hours_median_abs_bps | 36.3794333401257 | log_bps | results/T1_fidelidade.csv |  |
| common_hours_p95_abs_bps | 120.11527962726629 | log_bps | results/T1_fidelidade.csv |  |
| common_hours_above_50_fraction | 0.35622880892486053 | fraction | results/T1_fidelidade.csv |  |
| common_hours_mean_signed_bps | 6.997041583347956 | log_bps | results/T1_fidelidade.csv |  |
| common_hours_n | 36572 | count | results/T1_fidelidade.csv |  |
| reopen_median_abs_bps | 48.43799791326794 | log_bps | results/T1_fidelidade.csv |  |
| reopen_p95_abs_bps | 164.18372967594095 | log_bps | results/T1_fidelidade.csv |  |
| reopen_above_50_fraction | 0.4850498338870432 | fraction | results/T1_fidelidade.csv |  |
| reopen_mean_signed_bps | 15.666068395120933 | log_bps | results/T1_fidelidade.csv |  |
| reopen_n | 301 | count | results/T1_fidelidade.csv |  |
| one_hour_median_abs_bps | 37.13533247481308 | log_bps | results/T1_fidelidade.csv |  |
| one_hour_p95_abs_bps | 134.7342357878156 | log_bps | results/T1_fidelidade.csv |  |
| one_hour_above_50_fraction | 0.39867109634551495 | fraction | results/T1_fidelidade.csv |  |
| one_hour_mean_signed_bps | 11.310660503205604 | log_bps | results/T1_fidelidade.csv |  |
| one_hour_n | 301 | count | results/T1_fidelidade.csv |  |
| seven_hours_median_abs_bps | 37.99323972715562 | log_bps | results/T1_fidelidade.csv |  |
| seven_hours_p95_abs_bps | 115.76489472304361 | log_bps | results/T1_fidelidade.csv |  |
| seven_hours_above_50_fraction | 0.38205980066445183 | fraction | results/T1_fidelidade.csv |  |
| seven_hours_mean_signed_bps | 8.553673910475206 | log_bps | results/T1_fidelidade.csv |  |
| seven_hours_n | 301 | count | results/T1_fidelidade.csv |  |
| GLD_crossing_months | 9.3 | months | results/T3_baseline.csv | token costs assumed; ETF current official fee/spread; USD pretax |
| GLD_status | token_cheaper_after_crossing | classification | results/T3_baseline.csv |  |
| GLD_rt_bps | 1.0 | bps | results/T3_baseline.csv |  |
| GLDM_crossing_months | 37.2 | months | results/T3_baseline.csv | token costs assumed; ETF current official fee/spread; USD pretax |
| GLDM_status | token_cheaper_after_crossing | classification | results/T3_baseline.csv |  |
| GLDM_rt_bps | 1.0 | bps | results/T3_baseline.csv |  |
| token_rt_bps | 32.0 | bps | results/T3_baseline.csv | assumed token fees/spread/conversion |
| trade_calendar_weeks | 104 | weeks | results/T2_baseline_inference.csv |  |
| trade_valid_paths | 55 | weeks | results/T2_baseline_inference.csv |  |
| trade_signals | 60 | signals | results/T2_baseline_inference.csv |  |
| evaluated_trades | 44 | count | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| signals_unassessed | 16 | count | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| mean_gross_mid_bps | 4.526334653643858 | bps | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| mean_total_modeled_cost_bps | 44.53887317985197 | bps | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| positive_gross_fraction | 0.6136363636363636 | fraction | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| mean_trade_model_bps | -40.01253852620811 | bps | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| median_trade_model_bps | -40.688245901482375 | bps | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| worst_trade_model_bps | -115.26719892350528 | bps | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| positive_trade_fraction | 0.0 | fraction | results/T2_baseline_inference.csv | conditional cost assumptions; before unknown borrowing/financing; execution not verified |
| trend_status | exploratory_association | classification | results/T4_trend.csv | exploratory HAC; association not causality |
| trend_n_quarters | 24 | value | results/T4_trend.csv | exploratory HAC; association not causality |
| trend_beta_per_year | -0.08657130034329091 | value | results/T4_trend.csv | exploratory HAC; association not causality |
| trend_beta_lo | -0.24699183264985228 | value | results/T4_trend.csv | exploratory HAC; association not causality |
| trend_beta_hi | 0.07384923196327045 | value | results/T4_trend.csv | exploratory HAC; association not causality |
| baseline_median_abs_bps | 35.45393763529184 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| baseline_p95_abs_bps | 129.65517588688735 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| baseline_mean_trade_model_before_unknown_carry_bps | -40.01253852620811 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| baseline_method | deterministic_sensitivity_insufficient_joint_paths | classification | results/T5_sensibilidade.csv | conditional scenario not forecast |
| lower_friction_median_abs_bps | 35.45393763529184 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| lower_friction_p95_abs_bps | 129.65517588688735 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| lower_friction_mean_trade_model_before_unknown_carry_bps | -17.7430772860044 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| lower_friction_method | deterministic_sensitivity_insufficient_joint_paths | classification | results/T5_sensibilidade.csv | conditional scenario not forecast |
| stress_median_abs_bps | 70.90787527058367 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| stress_p95_abs_bps | 259.3103517737747 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| stress_mean_trade_model_before_unknown_carry_bps | -84.06037846864317 | bps | results/T5_sensibilidade.csv | conditional scenario not forecast |
| stress_method | deterministic_sensitivity_insufficient_joint_paths | classification | results/T5_sensibilidade.csv | conditional scenario not forecast |
| cutoff_utc | 2026-11-08T00:00:00Z | timestamp | config/params.json |  |
| short_access_verified | False | boolean | config/params.json |  |
| fx_source_median_abs_difference_bps | 6.4992528251239055 | log_bps | results/panel_status.json |  |
| fx_source_comparison_hours | 3168 | hours | results/panel_status.json |  |
| assumption_token_fee_bps_per_fill | 10 | bps | config/params.json | hypothesis not observed |
| assumption_token_full_spread_bps | 10 | bps | config/params.json | hypothesis not observed |
| assumption_gold_commission_bps_per_fill | 1 | bps | config/params.json | hypothesis not observed |
| assumption_conversion_roundtrip_bps | 2 | bps | config/params.json | hypothesis not observed |
| assumption_slippage_bps_per_fill | 2 | bps | config/params.json | hypothesis not observed |
| exit_hours | 6 | hours | config/params.json |  |
| signal_delay_minutes | 60 | minutes | config/params.json |  |
| bootstrap_replicates | 2000 | replicates | config/params.json |  |

## Limitações

Preços horários e de minuto são proxies, não quotes simultâneas garantidas. Custos de token e execução dependem das hipóteses declaradas. Empréstimo e financiamento permanecem desconhecidos. Sem conclusão causal sobre competição ou infraestrutura. Dados brutos dos provedores não acompanham o pacote público.
