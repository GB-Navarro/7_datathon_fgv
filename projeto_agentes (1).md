# Especificação de implementação: O preço da promessa

**Revisão v3 implementada:** o núcleo descrito abaixo foi preservado. A extensão retrospectiva acrescenta contrastes pareados, cinco previsões temporais e sensibilidade de cobertura cambial, documentadas em [MODELAGEM_REVISAO.md](auditoria/MODELAGEM_REVISAO.md), [REFINAMENTO.md](results/REFINAMENTO.md) e [config/refinement.json](config/refinement.json). A tese distingue ajuste observado, previsibilidade e captura econômica; os modelos lineares não demonstraram melhora sobre a persistência. A apresentação científica final usa Áureo v2, com dez slides principais e três anexos, em [HTML](slides/entrega.html) e [PDF](slides/entrega.pdf).

Versão 2.1, implementada em 08/11/2026 para a equipe BitFlow. Documento canônico, subordinado ao escopo do [plano da equipe](<projeto_humanos (1).md>). Os parâmetros estão em [config/params.json](config/params.json), com hash e instante de congelamento em [config_frozen.json](results/config_frozen.json). Código, dados processados locais, tabelas e apresentação foram executados; [README](README.md) e [interpretação](results/INTERPRETACAO.md) registram a reprodução e os resultados efetivos.

Os ajustes necessários de execução foram: volume/atividade no ouro; Bitfinex como referência USD primária; sinal de minuto antes da entrada; amostra pareada na figura de reabertura; coleta de minutos em blocos limitados por memória. Limiares de amostra e regras econômicas não foram relaxados após observar o P&L. A sensibilidade determinística foi acionada porque houve 55 trajetórias conjuntas válidas, abaixo das 78 exigidas para o cenário anual. Essa redução estava prevista no plano.

## 1. Objetivo e alcance da evidência

Pergunta: quão fiel é o PAXG ao ouro quando ambos negociam, o que acontece quando a referência reabre e quanto o acesso 24/7 custa sob diferentes condições de negociação?

O estudo mede fidelidade ao XAUUSD de um provedor, distribuição de desalinhamentos, convergência, custos de manutenção contra GLD/GLDM e sensibilidade. Generalizações sobre outros tokens, todo o mercado de ouro ou todos os RWAs exigem dados adicionais.

“Desalinhamento” é uma diferença observada contra uma referência, sem pressupor preço eficiente de um dos lados. “Simulação condicional” depende de acesso, instrumento e custos documentados ou supostos. Não chamar spread estimado de spread efetivo observado. Não chamar lucro de convergência de arbitragem sem risco.

Retirados do núcleo: H0 de competição versus infraestrutura; M5 trimestral como teste de competição; mesa profissional; soma de poças A/B/C; efeitos causais de eventos; carteira BTC/ETH; ranking de reserva de valor; extrapolação da data de maturidade; adoção produtiva DeFi. As condições de extensão estão na seção 13.

## 2. Regras de implementação

1. UTC em todos os dados. Calendários locais usam identificadores IANA, incluindo `America/New_York`; instalar `tzdata` quando necessário no Windows.
2. Janela semiaberta: `2020-08-28T12:00:00Z <= ts < 2026-11-08T00:00:00Z`. Remover candles cujo fim ultrapasse o corte. Não incluir a reabertura de 08/11/2026 na amostra principal.
3. Preços positivos, valores finitos, unidades USD por onça troy fina quando houver conversão observada. Volume da Binance vem em moeda de cotação; só chamar de USD após conversão por `q`.
4. Distinguir `event_time`, `bar_start`, `bar_end`, `available_at` e resolução. O horário nominal do candle não é o timestamp do último negócio.
5. Nenhuma variável de sinal ou tamanho em t usa dados publicados depois de t. Desfechos futuros podem ser usados somente para avaliar a operação já definida.
6. Parâmetros serão congelados antes de executar as análises, com hash e log. Esta é uma especificação prospectiva de implementação, não um pré-registro independente da pesquisa: exemplos e hipóteses já foram discutidos. Registrar todas as variantes e sua função.
7. Não preencher preços através do fechamento do ouro, buracos de fonte ou ausência de conversão monetária. Usar flags, não zeros ou interpolação silenciosa.
8. Nunca inferir disponibilidade de empréstimo, taxas institucionais ou profundidade de livro a partir de candles. Campos desconhecidos continuam desconhecidos.
9. Registrar URL, parâmetros, instante de acesso, hash, versão do schema e intervalo solicitado em cada download. Não registrar chaves de API.
10. Conservar outliers economicamente possíveis. Corrigir ou excluir apenas com evidência de problema de dado e uma razão documentada. Mostrar robustez com e sem observações contestadas.
11. Não publicar dados brutos do provedor sem licença compatível. Código aberto do downloader não concede licença dos dados.
12. Não citar testes, simulações, poder estatístico ou resultados que não foram realmente produzidos e preservados.

## 3. Estrutura e dependências

```text
config/params.json                  # premissas; snapshot e hash em results/config_frozen.json
config/sources.json                 # URLs e versões efetivamente utilizadas
data/raw/                          # fora do versionamento
data/interim/                      # fontes padronizadas
data/panel/                        # painéis e flags
src/common.py, fetch.py, panel.py, trades.py, statistics.py, analysis.py, quality.py, report.py
tests/                             # testes sem rede e casos sintéticos declarados
results/coverage.csv
results/exclusions.csv
results/variants.csv
results/RESULTS.md                  # gerado de resultados reais
results/claims.csv                  # número/afirmação, unidade, amostra, arquivo e hipótese
results/*.csv, *.png
slides/entrega.pdf
scripts_txt/
run_all.py, requirements.txt, README.md
```

Python 3.11, pandas, numpy, requests/httpx, pyarrow, scipy, statsmodels e matplotlib. `openpyxl` somente se a planilha do ETF for usada; `python-pptx` e conversor PDF se escolhidos. Fixar versões após um teste do ambiente. Node >=20 para `dukascopy-node`; no PowerShell usar `npx.cmd` quando `npx.ps1` for bloqueado. Não é necessário alterar a política de execução.

Aquisição, construção, análise e exportação estão separadas. `run_all.py` aceita `--all`, `--fetch`, `--build`, `--minutes`, `--analyze`, `--figures`, `--package` e `--offline`. O pacote exige testes e integridade aprovados. Não há pedidos de rede implícitos nos testes unitários.

## 4. Fontes, testes iniciais e alternativas

Evidências e links estão em [fontes verificadas](auditoria/fontes_verificadas.md). Uma resposta HTTP 200 de uma amostra não garante toda a série.

### 4.1 Binance

Fonte principal de PAXGUSDT horário: `https://data.binance.vision/`.

```text
data/spot/monthly/klines/PAXGUSDT/1h/PAXGUSDT-1h-YYYY-MM.zip
data/spot/daily/klines/PAXGUSDT/1h/PAXGUSDT-1h-YYYY-MM-DD.zip
GET https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1h&startTime=...&limit=1000
```

Validar checksums quando publicados. Agosto/2020 foi aberto nesta revisão: primeiro candle em 28/08/2020 às 12:00 UTC. Para arquivos spot desde 2025, esperar microssegundos; arquivos mais antigos usam milissegundos. Validar unidade por fonte/arquivo e intervalo plausível, não apenas por magnitude. APIs podem usar outra convenção. Arquivos mensais recentes podem ainda não ter sido publicados: completar com diários/API sem duplicar bordas.

Klines: `open_time,open,high,low,close,volume,close_time,quote_volume,trades,taker_buy_base,taker_buy_quote,ignore`. Preservar `trades` e `volume`. Candles planos sem negócio não viram preço fresco.

O painel de minutos é restrito às janelas necessárias dos últimos 104 fins de semana de calendário anteriores ao corte. As fontes agrupam arquivos por mês; a aquisição bruta usa esses agrupamentos e limita memória em blocos de ouro de até seis meses. Os brutos ampliados não entram na análise fora das janelas. Candles de minuto permanecem proxies de execução.

### 4.2 Conversão e segunda corretora

Referência primária implementada: `GET https://api-pub.bitfinex.com/v2/candles/trade:1h:tUSTUSD/hist?start=...&end=...&limit=10000&sort=1`, com `1m` nas janelas de convergência. O mapa da API confirma UST=Tether USDt. A sobreposição Coinbase é uma validação sistemática dos dois primeiros dias de cada mês disponível; seus resultados são publicados e não substituem silenciosamente a série primária.

```text
GET https://api.exchange.coinbase.com/products/USDT-USD/candles?granularity=3600&start=...&end=...
GET https://api.exchange.coinbase.com/products/PAXG-USD/candles?granularity=3600&start=...&end=...
```

Paginar em até 300 intervalos, tratar rate limits e filtrar localmente `[start,end)`. Resposta `[time,low,high,open,close,volume]`, em geral reversa; ordenar e deduplicar. Uma resposta vazia válida não é uma falha a ser preenchida com o último preço.

Descobrir a primeira/última observação e a cobertura em cada período. Os pares existem atualmente, mas ambos retornaram vazio em 28–29/08/2020. Não fixar início histórico sem baixar e inspecionar.

Definir `q(t)=USD por USDT`. O painel primário usa `q` observado, com timestamps compatíveis. Ausência de q exclui a observação desse painel. Uma extensão separada pode usar `q=1`, com `currency_method=assumed_usdt_usd_parity`. Não misturar suas estatísticas às da amostra USD.

Não usar `1/USDCUSDT` como USD observado. Outra fonte de USDT/USD é permitida após testar cobertura e compatibilidade; registrar a troca, fazer comparação na sobreposição e não colar fontes com descontinuidades silenciosas.

### 4.3 Ouro de referência

Usar XAUUSD bid e ask da Dukascopy. A revisão testou a CLI 1.51.1 com sucesso em 30/10–03/11/2026. Antes da aquisição completa, repetir teste em um mês antigo e um recente e inspecionar feriados e horário de verão.

```powershell
npx.cmd --yes dukascopy-node@1.51.1 -i xauusd -from 2020-08-28 -to 2026-11-08 -t h1 -p bid -v -fl -f csv -dir data/raw/dukascopy
npx.cmd --yes dukascopy-node@1.51.1 -i xauusd -from 2020-08-28 -to 2026-11-08 -t h1 -p ask -v -fl -f csv -dir data/raw/dukascopy
```

Conferir a convenção inclusiva/exclusiva da CLI e sempre reaplicar o corte local. O download bid e ask pode ser particionado por ano, com concorrência moderada e respeito ao limite do provedor. Checar candles em ambos os lados antes de calcular midpoint. `mid_high=(bid_high+ask_high)/2` não é máximo de midpoint sincronizado: usar somente open/close ou ticks para spread/ponto de referência.

Obrigatório: preservar volume, marcar barras inativas e validar calendário antes de detectar gaps. O downloader pode incluir preços repetidos nos fechamentos quando volume não é solicitado. `-v -fl` mantém essa distinção explícita, com atividade positiva nos dois lados para os pontos primários. O volume do provedor não é volume mundial de ouro.

Para minutos recentes usar `-t m1` nas janelas do estudo, após validação de acesso. Se houver 403 sem recuperação suportada, interromper tentativas automáticas excessivas. A CLI oferece instalação de navegador quando necessária; o teste desta revisão não precisou dela.

Se faltar ouro intradiário confiável, cortar o componente de reabertura e executar a versão diária em horários comuns, após validar outra fonte. `GC=F` é futuro e pode incluir rolagem; não substitui silenciosamente ouro à vista. Sem intradiário, não publicar P&L de reabertura como se a pergunta tivesse sido respondida.

### 4.4 ETFs e documentos de acesso

Usar GLD e GLDM, com custos anuais atuais de 40 e 10 bps. As páginas dos emissores são referências de taxa, não fontes automáticas de custos individuais de negociação. O endpoint do arquivo histórico GLD foi localizado e responde XLSX; ele é opcional para o núcleo.

Spread do ETF: obter bid/ask de bolsa ou uma medida oficial documentada, registrando horário/período, ou usar a grade de hipóteses. Não transformar cotação de broker em livro oficial nem usar `NAV / ouro às 15h de Londres` para fabricar prêmio comparável. Taxa anual atual é usada na decisão prospectiva; um backtest histórico demandaria tabela por vigência.

A página consolidada atual da Paxos substitui o endereço antigo de taxas. Registrar o estado atual e sua data; não aplicar condições atuais retrospectivamente. Acesso primário, cotação StoneX e resgate físico são conceitos distintos de negociação do token em corretora.

## 5. Painéis e rastreabilidade

Todos os schemas incluem `source`, `resolution`, `download_id` e flags de validade.

| Arquivo | Conteúdo mínimo |
| --- | --- |
| `token_1h.parquet` | `bar_start,bar_end,symbol,open,high,low,close,base_volume,quote_volume_quote_ccy,trades,has_trade` |
| `gold_1h.parquet` | `bar_start,bar_end,bid_open,bid_close,ask_open,ask_close,mid_open,mid_close,spread_open_bps,spread_close_bps` |
| `fx_1h.parquet` | `bar_start,bar_end,q_usdt_usd,has_trade,currency_method` |
| `coverage.csv` | fonte, mês, esperados quando definido, recebidos, válidos, vazios e gaps |
| `exclusions.csv` | `row_id,analysis,reason,source,manual_evidence` |
| `panel_hourly.parquet` | `t,p_usdt,q,p_usd,S,basis_log_bps,currency_method,alignment_gap_seconds,price_age_status,valid` |
| `panel_weekends.parquet` | `id,t_c,t_0,t_e,S_c,S_0,p_c,p_0,q_c,q_0,b_c,b_0,m,g,b_1h,b_7h,stress_threshold,stress_flag,validity_flags` |
| `panel_minutes.parquet` | fonte, minuto, preços open/close ou quotes/ticks, bid/ask, volume, contagem de negócios, timestamp real quando disponível |
| `trades_A.parquet` | sinal, decisão, entrada/saída previstas, observadas, acesso, hipótese de custo, P&L por componente, validade e razão de ausência |

Não dar nome USD ao volume de PAXGUSDT antes de multiplicar por q. Não exigir preenchimento on-chain para liberar os painéis principais. Componentes opcionais são unidos depois, sem bloquear o núcleo.

## 6. Alinhamento e medidas de preço

### 6.1 Fechamento e reabertura

Detectar candidatos por gap entre inícios de candles de ouro maior que 36h e até 84h, atravessando um sábado. Isso apenas gera candidatos. Validar cada caso com calendário de negociação do provedor/mercado, horário de verão, bid e ask e observações vizinhas. Feriados prolongados são estrato separado; gaps internos sem explicação não são fins de semana.

`t_c` é o fim da última vela válida antes do fechamento; `t_0`, o início da primeira vela válida após o fechamento. Se a fonte omitiu a primeira hora, marcar reabertura incompleta em vez de deslocar o relógio silenciosamente. Não usar contagem esperada como imposição sobre os dados: são 323 candidatos de calendário até 01/11/2026, e o total válido pode ser menor.

### 6.2 Preços e antiguidade

Em hora comum t, usar closes das velas `[t-1h,t)` nos três mercados. Em `t_0`, usar close anterior do token e de q, disponíveis até `t_0`, contra `mid_open` do ouro após a reabertura. Em `t_c`, usar closes anteriores dos três. Definir `t_e=t_0+1h`, e medir novamente em `t_e` e `t_0+7h` com closes de velas completas.

Essa medida é `hourly_proxy`, não observação perfeitamente simultânea. Mesmo com barras alinhadas, o último negócio pode ser antigo. Volume positivo reduz a ambiguidade para dentro do intervalo, mas não dá timestamp exato. Não confundir tolerância nominal de timestamp com frescor comprovado.

Robustez obrigatória quando disponível: últimos 26 fins de semana válidos, usando minutos ao redor de `t_0` e de `t_e`, com tolerância principal de 1 minuto e sensibilidade de 5 minutos. Separar preço anterior à reabertura do preço posterior. Comparar sinal, nível, mediana e p95 com o painel horário. Para afirmar execução simultânea, exigir quotes/ticks com timestamps e acesso demonstrado; minutos OHLC isolados não bastam.

### 6.3 Bases logarítmicas e identidade exata

```text
P(t) = p_usdt(t) * q(t)
b(t) = 10000 * ln(P(t) / S(t))
g_w  = 10000 * ln(S_0 / S_c)
m_w  = 10000 * ln(P_0 / P_c)
b_0 - b_c = m_w - g_w
```

Todos esses resultados usam bps logarítmicos; para desvio percentual simples usar `100*(exp(b/10000)-1)`. Não misturar retorno simples e log na mesma identidade. A relação é exata salvo arredondamento numérico e exige os mesmos preços nas duas contas.

`b_0` é desalinhamento contra a referência ao reabrir; `b_1h` e `b_7h` medem sua trajetória. Reportar diferenças assinadas e absolutas. A queda de `abs(b)` não é, por si, P&L: atravessar zero ou o ouro se mover pode alterar o resultado de uma posição com quantidades fixas.

### 6.4 Estatísticas, cauda e estresse

Reportar mediana, p95 de `abs(b)`, frequências de `abs(b)>25,50,100` bps e os cinco maiores casos com datas e flags. Máximo é estatística histórica, sem intervalo que prometa limite de risco futuro. Não usar p99 de uma subamostra curta como estimativa precisa.

Regime w: `stress_flag=abs(g_w)>p90(abs(g))` calculado nas observações válidas dos 104 fins de semana de calendário anteriores, exigindo pelo menos 52 válidas. Sem história suficiente, regime desconhecido. É um estrato ex post após observar o salto; não é um sinal de negociação conhecido na sexta. Usá-lo para descrever condições e nunca para escolher retrospectivamente uma operação.

Separar contribuição de stablecoin por `ln(P/S)=ln(p_usdt/S)+ln(q)`. Os termos são uma decomposição contábil; o primeiro não é um desvio USD independente da moeda. Riscos de emissor, contraparte e resgate permanecem documentais.

## 7. Convergência: sinal, preços e custos

### 7.1 Regra principal e amostra

Simular nos últimos 104 fins de semana de calendário anteriores ao corte, conservando flags de semanas inválidas. Exigir pelo menos 52 trajetórias válidas em USD para inferência agregada; abaixo disso, apenas estatísticas identificadas como pequenas amostras ou suprimir o componente. Não comprimir lacunas até obter 104 observações nem extrapolar o comportamento desses dois anos para todo o histórico.

```text
t_signal = t_0 + 60 min
s = sign(b(t_signal))                       # +1: vender token/comprar ouro
signal_eligible = abs(b(t_signal)) >= 10 bps
t_in = t_signal + 1 min
t_out = t_in + 6h
```

O sinal usa closes de minuto concluídos, disponíveis em `t_signal`; isso reduz a ambiguidade da antiguidade intrahorária. Preço de entrada: primeira observação dentro do minuto de `t_in`, com escolha fixa de open do minuto como proxy quando só houver candles. Usar o mesmo procedimento em `t_out`; não escolher a melhor cotação da janela. Se houver negócios/quotes efetivos, conservar os timestamps. Registrar a atualização de q usada na conversão, sempre disponível até o instante de cálculo.

Horários de 1h e 24h após entrada são sensibilidade secundária, não variantes para escolher o melhor desempenho. Manter tabela de todas as tentativas. Sizing só pode usar dados anteriores à entrada; volumes futuros servem à verificação de capacidade ex post, nunca à posição escolhida em t.

### 7.2 P&L exato por onça

Para preços de referência e quantidades fixas de uma unidade em cada perna:

```text
pnl_mid_usd = s * [(P_in - P_out) + (S_out - S_in)]
pnl_mid_bps_on_gold_leg = 10000 * pnl_mid_usd / S_in
```

Essa normalização não é retorno sobre capital total ou margem. Não substituir pelo simples decréscimo de `abs(b)`.

Quando houver bid/ask ou proxies construídas com spread declarado:

```text
s=+1: pnl_before_fees = P_bid_in - P_ask_out + S_bid_out - S_ask_in
s=-1: pnl_before_fees = P_bid_out - P_ask_in + S_bid_in - S_ask_out
```

Spreads já entraram nos preços dessas fórmulas. Não subtrair novamente um spread cheio. Aplicar taxas por execução sobre seu valor financeiro, slippage desfavorável por execução e carregamento/empréstimo sobre o notional e o tempo apropriados. Se um preço for last-trade com spread suposto, identificar ambos os componentes como proxies; não chamar bid/ask de observados.

### 7.3 Livro de custos

Para a aproximação em bps, com spreads cheios `s` e taxas por execução `f`:

```text
C_A ≈ 2*f_token + 2*f_gold
      + (s_token_in+s_token_out)/2
      + (s_gold_in+s_gold_out)/2
      + conversion_rt + slippage_4_fills + carry + borrow
```

Taxa do token: hipóteses de 2, 5 e 10 bps por fill; 10 é base editorial, sem alegar acesso real a um tier. Spread do token não observado: grade de 2/10/25 bps cheios. Comissão do ouro: grade de 1/2 bps por fill. Conversão: grade de 0/2/10 bps de ida e volta. Slippage: 0/2/5 bps por fill, somando as quatro execuções.

Empréstimo de token e financiamento do ouro começam como desconhecidos no config. O código não pode converter `null` em zero. Produzir saldo após custos modelados e **antes dos custos desconhecidos**, além de sensibilidade de carregamento residual de 0/5/25 bps por operação. Zero é cenário explicitamente otimista, não observação. Sem acesso e custos completos, nenhum resultado recebe o rótulo executável.

Corwin-Schultz, se implementado, fica apenas como diagnóstico. Foi desenvolvido sob hipóteses que não validam automaticamente seu uso em barras horárias de PAXG. Uma estimativa baseada nas velas t e t+1 não está disponível em t. Não usar esse valor para decidir entradas ou custos ex ante; versões usadas em sinais precisam estar inteiramente defasadas. Também não substituir automaticamente por Roll sem testar suas hipóteses.

### 7.4 Perdas, dados ausentes e capacidade

Preservar o P&L assinado de todas as operações sinalizadas. Fração lucrativa é desfecho, nunca filtro retrospectivo. Somar `max(pnl,0)` é rendimento com escolha perfeita do futuro: só pode aparecer como diagnóstico explicitamente irrealista, sem sustentar conclusão econômica.

Registrar `signal_eligible`, `entry_observed`, `exit_observed`, `short_access_status`, `cost_completeness` e `pnl_status`. Falta de preço de saída não é operação zero nem perda apagada: contabilizar como desfecho não avaliado e mostrar cobertura, concentração de ausências em estresse e sensibilidade. Taxa de acerto e média usam apenas avaliados com seu denominador declarado; não afirmar ausência de oportunidades no restante.

Métricas: N sinalizado/avaliado, cobertura, média/mediana líquida por hipótese, IC em blocos, taxa de acerto, pior perda e custo residual de equilíbrio. Sem custo de empréstimo, mostrar quantos bps adicionais anulariam o resultado.

Capacidade opcional: 1% e 5% do volume USD da hora anterior à entrada, limitada também pela disponibilidade da outra perna quando observada. São hipóteses de participação, não capacidade demonstrada. A análise com volume de saída é um limite ex post separado. Não somar horas da mesma oportunidade nem rotas diferentes.

## 8. Custo de manutenção contra GLD e GLDM

Escopo: investidor já com USD, contas de caixa financiadas, comparação antes de impostos, mesmas possibilidades de acesso. Custódia e direitos de resgate diferem entre produtos. Estimar custo não equivale a recomendar produto ou a quantificar seu risco jurídico.

Para notional N e horizonte h em meses:

```text
C_token(h,N) = C_token_rt(N) + r_token * h/12
C_etf(h,N)   = C_etf_rt(N)   + r_etf * h/12
C_token_rt  ≈ 2*f_token + spread_token_rt + conversion_rt
              + 10000*network_withdrawal_rt_usd/N
C_etf_rt    ≈ 2*f_etf + spread_etf_rt + other_broker_costs_bps
DeltaC(h)   = C_token(h,N) - C_etf(h,N)
```

Taxas de administração/armazenamento em bps por ano; custos de ida e volta em bps. `spread_rt` significa metade do spread cheio na entrada mais metade na saída; com spread constante, equivale a um spread cheio. Não usar um spread inteiro por fill.

Usar `r_etf=40` para GLD e `10` para GLDM, segundo condições atuais. `r_token=0` no cenário atual de armazenamento; taxas de custódia próprias de cada rota são adicionais quando aplicáveis. Isenção de armazenamento não significa risco/custo de custódia universalmente zero.

Notionais USD 1.000/10.000/100.000; horizontes 1/3/6/12/24/36 meses. Custos fixos de rede/retirada de USD 0/10/50 são hipóteses de ida e volta, dependentes da rota. Usar zero quando nenhuma transferência for feita na rota, sem apresentá-lo como custo observado de autocustódia.

Publicar grade de cenários em vez de falsa precisão: os spreads e taxas ainda não medidos são parâmetros, não uma amostra aleatória. Um IC de bootstrap dos preços não cobre erro de modelo ou custo não observado.

### 8.1 Cruzamentos de custo

```text
A = C_token_rt - C_etf_rt
B = r_token - r_etf
DeltaC(h) = A + B*h/12
h_star = -12*A/B, quando B != 0
```

Classificar pelo sinal de `DeltaC`, não apenas por h_star:

- B<0 e A>0: token passa a custar menos após h_star positivo.
- B<0 e A<=0: token já custa menos desde o início, com igualdade inicial quando A=0.
- B=0: custo relativo constante; igualdade em todos os horizontes quando A=0.
- B>0 e A<0: token custa menos inicialmente e perde a vantagem após h_star.
- B>0 e A>=0: token não fica mais barato em horizonte positivo.

Quando não houver cruzamento positivo, produzir status legível; não truncar denominadores ou impor um equilíbrio artificial. Testar armazenamento hipotético de 0/10/20/40 bps/ano contra ambos os ETFs. A cobrança de 20 bps pode eliminar a vantagem de carregamento contra GLDM sem eliminá-la contra GLD.

Cheque algébrico, **não resultado**: A=25-3=22 e r_token=0 implicam 6,6 meses com GLD e 26,4 com GLDM. A referência anterior a “cerca de seis meses” era aceitável como arredondamento, mas não como estimativa medida.

## 9. Evolução temporal e inferência

### 9.1 Análise principal descritiva

Mediana e p95 trimestrais de `abs(b_t)` em horários comuns, por amostra monetária. Excluir trimestres incompletos da regressão principal; mostrar sua descrição separadamente. Publicar cobertura de horas previstas, contando apenas horários em que os mercados deveriam funcionar.

Trimestre com menos de 80% de cobertura válida não entra na inferência de tendência, mas permanece no gráfico com flag. Fazer robustez em horários comparáveis e na subamostra recente. Desvios altos de mercados ilíquidos não são eliminados automaticamente como erros: verificar trades e qualidade.

Regressão de tendência opcional, com pelo menos 12 trimestres completos:

```text
y_q = ln(max(mediana_q(abs(b)), 1 bp))
y_q = a + beta*tempo_em_anos_q + gamma*ln(volatilidade_ouro_q) + u_q
```

Calcular volatilidade de retornos intradiários comuns com tratamento de gaps; não incluir retorno atravessando fechamento como retorno de 1h. Erros HAC com 2 lags trimestrais, reportando efeito e intervalo, com ressalva de amostra curta. Sensibilidade ao piso de 0,5/2 bps. Se a robustez mudar o sinal, a conclusão é inconclusiva.

Não dizer que muitas horas resolvem baixa potência: observações têm dependência e mudanças de composição. Não usar AR(1) sem intercepto e sem tratar fechamentos para reportar meia-vida. Essa extensão não é necessária ao núcleo.

### 9.2 Intervalos e comparações

Bootstrap de 2.000 réplicas, seed 20261108, blocos de quatro semanas e robustez de duas/oito. Para painel horário, reamostrar semanas inteiras preservando suas horas. Para fins de semana, reamostrar blocos de unidades semanais em ordem, conservando flags e ausência de dados.

Para estratos de estresse com menos de 30 fins de semana, mostrar contagens e valores, sem manchete sobre diferença estatisticamente estabelecida de p95. Mesmo acima disso, o p95 pode depender de poucos extremos: publicar número de observações na cauda e sensibilidade aos cinco maiores casos. Não remover extremos para melhorar significância.

O núcleo não depende de testes de p-valor. Intervalos e variantes são exploratórios, sem seleção de métrica favorável. Se forem adicionados testes confirmatórios, definir família, direção e correção de múltiplos testes antes de executá-los; não chamar a antiga regra H0 de teste estatístico.

## 10. Simulação de sensibilidade

A implementação está em `src/analysis.py`, função `scenarios`, executada depois dos resultados centrais. Os ramos estocástico e determinístico são testados. Na amostra desta execução, o critério de trajetórias completas exigiu a saída determinística. Não existe obrigação de criar um segundo script homônimo de um simulador que não havia sido fornecido.

Usar os 104 fins de semana de calendário mais recentes anteriores ao corte, exigindo pelo menos 78 semanas conjuntas válidas. Se não cumprir, substituir por grade determinística de custo/desalinhamento, sem números anuais estocásticos.

Cada observação conjunta contém pelo menos: bases de fechamento, reabertura, sinal, entrada e saída; retorno do ouro entre entrada e saída; q; volumes; spreads disponíveis; flags de qualidade; e componentes de custo. Não usar sorteios independentes para erro, convergência e volume.

Procedimento:

1. Reamostrar blocos conjuntos de quatro semanas para horizontes de 52 semanas. Manter ordem dentro de blocos e reutilizar os mesmos sorteios nas comparações pareadas entre cenários.
2. No cenário de referência, conservar os caminhos observados. Recalcular a regra de sinal e todas as métricas sem usar ganho futuro como filtro.
3. Em menor atrito, manter preços e quantidades da referência e multiplicar por 0,5 os custos variáveis de negociação modelados. Custos fixos em USD e custos desconhecidos não se tornam zero.
4. No estresse hipotético, multiplicar por 2 as bases logarítmicas em todos os instantes do caminho, por 2 os custos variáveis e por 0,5 os volumes; armazenamento hipotético de 20 bps/ano entra apenas na comparação de carregamento. Não dobrar a volatilidade do ouro implicitamente: seus retornos são reamostrados da amostra.
5. Recalcular sinal, elegibilidade, preços sintéticos e P&L por quantidades fixas depois de cada transformação. Bases assinadas permitem atravessar zero e gerar perdas. Não impor convergência positiva.
6. Apresentar mediana e intervalos de reamostragem junto às hipóteses. Incerteza de amostragem e sensibilidade às hipóteses são painéis distintos.

Reconstrução consistente dos preços sob bases transformadas:

```text
P_in/S_in = exp(b_in/10000)
S_out/S_in = 1 + R_gold
P_out/S_in = (1 + R_gold)*exp(b_out/10000)
pnl_mid/S_in = s*[exp(b_in/10000) - (1+R_gold)*exp(b_out/10000) + R_gold]
```

Após reconstruir, refazer bid/ask supostos e custos sem dupla contagem. Se custos forem calculados diretamente nas cotações, não descontar de novo a parcela de spread escalada. Financiamento/despesas não medidos continuam identificados em todas as saídas.

Saídas principais: mediana/p95 do desalinhamento, custo residual de equilíbrio e custo total GLD/GLDM por horizonte. P&L por onça de cada percurso entra somente quando os caminhos e custos necessários estiverem disponíveis. Não publicar “poça anual de lucro” do mercado, retorno de mesa ou efeito atribuído à infraestrutura. A escolha de multiplicadores é normativa e não calibrada como efeito causal.

O estresse inverso do núcleo responde **qual custo adicional zera o resultado modelado ou qual custo de armazenamento muda a escolha**, sem exigir um custo fixo suposto de mesa. Riscos de margem, empréstimo e contraparte precisam continuar no texto, mesmo em um cenário com média favorável.

## 11. Outputs e matriz de decisão

| ID | Arquivo a gerar | Conteúdo |
| --- | --- | --- |
| T0 | `coverage.csv`, `exclusions.csv` | Cobertura, moeda, flags e razões de exclusão |
| T1 | `T1_fidelidade.csv` | Mediana/p95/frequências em horários comuns e reabertura |
| T2 | `T2_convergencia.csv` | Desvio em t0/1h/7h; P&L condicional quando validado; N e custos |
| T3 | `T3_custos_etfs.csv` | GLD/GLDM, notional, horizonte, parâmetros, cruzamentos e status |
| T4 | `T4_evolucao.csv` | Séries trimestrais, cobertura e tendência opcional |
| T5 | `T5_sensibilidade.csv` | Hipóteses, métricas e incerteza, ou grade determinística |
| T6 | `T6_decisao.csv` | Necessidade do usuário, evidência, custo, acesso e limite |
| F1 | `F1_fidelidade.png` | Distribuição e evolução em horários comuns |
| F2 | `F2_reabertura.png` | Trajetória t0/1h/7h e casos de cauda |
| F3 | `F3_convergencia_custos.png` | Resultado por hipótese ou custo que anula ganho aparente |
| F4 | `F4_token_gld_gldm.png` | Custo total por prazo e tamanho |
| F5 | `F5_sensibilidade.png` | Cenários e limites; identificar suposições no próprio gráfico |

Não classificar reserva de valor secular por beta diário ou poucas semanas de estresse. A matriz inclui: necessidade de negociar fora do horário; diferença de custo em um horizonte especificado; fidelidade observada; exigência de short/resgate; limites jurídicos e de contraparte. Usar “atende à necessidade sob estas condições”, “depende do acesso” ou “evidência insuficiente”, sem um selo universal de melhor ativo.

Toda afirmação do PDF sai de `claims.csv` e `RESULTS.md`, com unidade, janela, denominador, fonte e hipótese. Títulos acompanham os resultados. O gráfico de maior desvio de preço não pode virar conclusão sobre maior risco total.

## 12. Trabalho, dependências e critérios de aceite

| Pacote | Entrega | Dependências |
| --- | --- | --- |
| WP0 | Ambiente, parâmetros congelados, schemas, manifestos | Plano revisado |
| WP1 | Binance, q e cobertura | WP0 |
| WP2 | Ouro bid/ask, calendário e cobertura | WP0 |
| WP3 | Painéis horários/semanas, exclusões e auditoria manual | WP1 e WP2 |
| WP4 | Fidelidade, riscos e GLD/GLDM | WP3; ETF documental pode começar antes |
| WP5 | Minutos e simulação condicional, tendência e sensibilidade | Núcleo WP4 validado |
| WP6 | Matriz, figuras, números rastreáveis e PDF | WP4; WP5 somente se aprovado |
| QA | Conferência de dados, fórmulas, claims e PDF | Contínuo; revisão final independente |

Pacotes de aquisição podem ser executados em paralelo por integrantes/agentes autorizados. Cada um escreve arquivos próprios e um manifesto; integração só após fechar o arquivo. Evitar agentes escrevendo no mesmo CSV ou documento. On-chain não é dependência de WP3.

Critérios de avanço:

- Em 30 minutos: amostras de token/ouro acessíveis e teste de conversão definido. Se ouro intradiário não estiver acessível após até 45 minutos de tentativas, acionar versão diária de escopo reduzido.
- Em 3h: três fins de semana reconciliados à mão, incluindo um próximo a mudança de horário de verão, um de movimento grande e um escolhido por seed. Se falhar, pausar inferências e corrigir painel.
- Antes de WP5: T0/T1/T3 disponíveis; nenhum simulador pode bloquear o PDF mínimo.
- Antes de exportar: não há lucro publicado sem custo/acesso identificado, mistura silenciosa USD/USDT ou resultado ilustrativo apresentado como medição.

Orçamento relativo de oito horas conforme guia da equipe; prevalecem congelamento de análises às 19h, PDF preliminar 20h30, pacote 21h30 e meta de submissão 22h em Brasília. Se houver menos tempo, produzir oito slides e cortar extensões, bootstrap de cenários, inferência de tendência e simulação de execução, nessa ordem. Dados e correção das medidas continuam obrigatórios.

## 13. Extensões com condições adicionais

### Mercado primário B

Sem cotação efetiva da Paxos, calcular apenas prêmio aparente contra a referência e distância a uma tabela de taxas vigente. Não chamar isso de lucro observado ou limite superior matemático garantido: o preço de emissão pode diferir da referência. Um limite superior exige premissas explícitas sobre os preços e fricções omitidas.

Uso histórico demanda tabelas por vigência, horários de operação, mínimos, spreads, prazo de liquidação e elegibilidade. Sem isso, manter apenas contexto atual, sem backtest B ou capacidade inferida por mint/burn.

### Dispersão entre corretoras C

Uma troca de inventários pré-posicionados usa duas execuções. O custo aproximado é `f_B+f_C+s_B/2+s_C/2+rebalanceamento+conversão`. Se f_B=f_C=f, a parcela de execução do plano anterior `2*f+(s_B+s_C)/2` era correta para essa operação pontual. As taxas dos venues não precisam ser iguais.

Um ciclo completo para devolver os dois inventários ao estado inicial pode exigir duas execuções adicionais. Nesse caso, modelar quatro fills e a trajetória dos preços, sem contar o primeiro ganho duas vezes. Cálculo por candles não sincronizados é dispersão indicativa; não equivale a ganho capturável a cada hora. Exigir cobertura válida dos dois venues, quotes e premissas de estoque para simular execução. Sem isso, não somar oportunidades horárias em USD anuais.

### On-chain

Carteira de controlador de oferta não é identificador universal e imutável de estoque de clientes. Identificar histórico de controladores, upgrades, endereços de estoque e transferências internas antes de atribuir fluxos. Separar cunhagem/queima, transferências para clientes e gestão interna, sem duplicar eventos.

Reconciliar `supply_inicio + mints - burns = supply_fim` nos mesmos blocos da amostra e na mesma rede. Não comparar fluxos truncados em junho com `totalSupply(latest)` de novembro. Tratar mudanças de contrato e expansão multichain; o lançamento Solana de 25/06/2026 motiva corte conservador ou reconciliação adicional, não prova de subestimação automática de toda emissão.

Uma associação entre fluxos e desvio não identifica arbitradores nem competição. Regressão trimestral com cerca de duas dezenas de observações não deve decidir a tese. Se a extensão ficar pronta, apresentar apenas evidência descritiva validada.

### Eventos, descoberta de preço e perpétuos

Datas verificadas podem contextualizar gráficos. Dois eventos no mesmo ano, tendências, choques simultâneos e poucas observações posteriores impedem atribuição causal simples. Disponibilidade de um contrato não mede adesão ou liquidez. Não inferir que o salto spot encolhe por identidade só porque outro instrumento abriu 24/7: isso seria um possível efeito econômico a medir.

Se houver previsão de salto, usar informação estritamente anterior à reabertura, benchmark de previsão zero e validação temporal expansiva. É extensão com teste retrospectivo, sem claim de causalidade ou informação exclusiva do token. Nenhuma parte do núcleo promete comprovar descoberta de preço.

Perpétuo exige regras de índice, mark/index prices, funding, margem, risco de liquidação, frequência e custos próprios. Não aplicar automaticamente taxa spot ao futuro. Sem esses dados, cortar a estratégia D. ML e carteiras ficam fora da entrega atual.

## 14. Verificações e requisitos do pipeline

- UTC/unidade: casos sintéticos em segundos, milissegundos e microssegundos, incluindo a transição de arquivos spot em 2025.
- Bordas: paginação inclusiva, duplicatas e candles que ultrapassam o corte não entram duas vezes.
- Calendário: fim de semana comum, DST, feriado e lacuna de fonte retornam flags distintas; não promover falha da fonte a reabertura.
- Moeda: q ausente não vira 1; proxy USDC não vira USD observado; extensão q=1 não entra na amostra principal.
- Identidade logarítmica: preços sintéticos inclusive com movimentos grandes satisfazem `b0-bc=m-g` à precisão de máquina.
- Sinal: apagar dados posteriores ao sinal não altera posição, filtro, instante ou tamanho escolhido.
- P&L: token caro converge, token barato converge, cruzamento de zero e divergência; perdas permanecem; validar preço exato e normalização.
- Custos: quatro fills em A, dois em troca de inventários C e quatro no ciclo completo; spread embutido em bid/ask não é descontado novamente.
- Dados ausentes: saída faltante é não avaliada e não zero; custo financeiro null não vira financiamento gratuito.
- Capacidade: adicionar volume futuro não aumenta posição histórica escolhida.
- Equilíbrio: GLD/GLDM, custo fixo por notional e todos os casos A/B de sinal, inclusive ausência de cruzamento e reversão da vantagem.
- Bootstrap: reamostragem conjunta, preservação da ordem dentro do bloco e sementes reproduzíveis; não afirmar invariância de distribuição a outra seed sem medir erro Monte Carlo.
- Cenários: cenário com fatores 1 reproduz cálculos da base no mesmo caminho; taxas maiores reduzem P&L para posições fixas; fator de volume não altera retorno unitário. Seleção pode mudar agregados: não impor monotonicidade artificial de p95 ou taxa de acerto.
- Exportação: todo número do PDF tem uma claim, unidade, amostra e arquivo de origem; abrir o PDF e conferir corte de textos.

As verificações algébricas da revisão estão no utilitário de auditoria. Os testes implementados ficam em `tests/`; a execução registrada está em `results/pytest.xml`, e a integridade dos resultados em `results/QA_integrity.json`. A lista acima continua sendo o contrato de qualidade, sem substituir a leitura desses registros.

## 15. Entrega e condição de solidez

PDF de até 10 slides por escolha editorial, fontes citadas e scripts em TXT quando houver scripts, conforme o regulamento e eventuais instruções complementares. O número de slides e a duração de defesa não foram confirmados como exigências no PDF oficial. Registrar ferramentas usadas e ler eventuais instruções de autoria fornecidas à equipe; não inferir proibição ou permissão específica de IA a partir do silêncio do texto.

O desenho revisado é metodologicamente defensável porque as perguntas principais dependem de medidas observáveis, as hipóteses de custo ficam expostas e a conclusão não depende de um resultado específico. A evidência empírica ainda exige aquisição completa, QA e execução. Se os gates falharem, reduzir expressamente o alcance e aplicar os cortes; não preencher lacunas com números ilustrativos.
