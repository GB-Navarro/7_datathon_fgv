# Viabilidade dos dados e da implementação

Pesquisa e testes realizados em 08/11/2026, antes da implementação. Este registro histórico verifica acesso, formato, cobertura e ambiente. A execução posterior do estudo está no [README](../README.md) e na [interpretação](../results/INTERPRETACAO.md). As consultas de mercado foram públicas e não exigiram chave paga. Os arquivos de teste desta etapa ficaram em diretórios temporários, fora do repositório.

## Parecer

É viável implementar ponta a ponta o núcleo revisado: aquisição, limpeza, painéis, fidelidade, risco de preço, simulação condicional de convergência, custos GLD/GLDM, sensibilidade, figuras, PDF e código reproduzível.

Não está disponível gratuitamente uma reconstrução integral comprovada de todos os custos e condições de execução. Livro histórico completo, empréstimo de PAXG, acesso individual a short e cotações executáveis da Paxos continuam limitando uma afirmação sobre lucro de arbitragem efetivamente capturável. A implementação deve preservar essa distinção.

## 1. PAXG na Binance

Foram consultados os índices públicos de `PAXGUSDT/1h` e `PAXGUSDT/1m`. Cada um lista **75 ZIPs mensais**, de agosto/2020 a outubro/2026, sem paginação pendente. Os tamanhos somados são 2.353.544 bytes para os arquivos horários e 82.231.042 bytes para os de minuto. Isso mede os arquivos listados; não é a validação de todas as linhas desses 150 ZIPs.

Foram abertos os meses agosto/2020, janeiro/2023 e outubro/2026 em ambas as resoluções:

| Mês | Horas | Minutos | Minutos sem negócio |
| --- | --- | --- | --- |
| 2020-08, desde a listagem | 84 | 5.040 | 3.703 |
| 2023-01 | 744 | 44.640 | 14.559 |
| 2026-10 | 744 | 44.640 | 2.996 |

Não houve timestamps faltantes no intervalo interno desses arquivos. Isso não significa negociação em todos os minutos: candles sem negócio não fornecem preço fresco de execução.

Também foi aberto o arquivo de negócios agregados de 02/11/2026: **31.977 registros**, com timestamps em microssegundos e IDs de negócios. Ele pode ajudar a auditar antiguidade de preços. O histórico de trades não reconstrói ofertas que nunca foram executadas.

Fontes: [documentação Binance](https://github.com/binance/binance-public-data), [índice horário](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/PAXGUSDT/1h/) e [índice de minutos](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/PAXGUSDT/1m/).

## 2. Ouro XAUUSD: acesso confirmado e correção necessária

A CLI `dukascopy-node@1.51.1` baixou bid e ask horários para a janela solicitada de 28/08/2020 a 08/11/2026. Também foram obtidos minutos recentes de 01–03/11/2026. Isso confirma a aquisição real, além de documentação ou teste de um endpoint.

O download horário inicial, sem volume, retornou **53.908 barras** em cada lado, alinhadas, sem valores nulos ou spreads de abertura negativos. Porém, a maior parte dos fechamentos de fim de semana estava escondida por barras repetidas com preço constante. Encontrar apenas um gap maior que 36h nessa saída era incompatível com o calendário de negociação.

Repetindo os downloads com volume e preservando barras inativas, foram identificadas **17.270 barras com volume zero** e **36.638 com volume positivo nos dois lados**. Bid e ask se alinharam por timestamp e não houve spreads open/close negativos nas barras ativas. Nesse subconjunto reapareceram **323 gaps maiores que 36h**, incluindo a mudança de horário da reabertura de 01/11/2026. Nenhuma barra positiva caiu em sábado. Esse total ainda exige classificação de feriados e cruzamento com token e conversão.

Na amostra de minuto, o bruto retornou 2.878 barras bid e 2.880 ask; a junção por timestamp e atividade positiva dos dois lados deixou 1.438 observações, sem spreads negativos. O primeiro minuto ativo foi 01/11/2026 às 23:00 UTC. Essa diferença de índices confirma a necessidade de junção por tempo.

Portanto, a ingestão deve obrigatoriamente:

1. Baixar com `-v -fl`, preservando a informação de atividade no bruto.
2. Identificar volume zero e calendário fechado antes de calcular bases ou detectar reaberturas.
3. Conservar a diferença entre cotação preenchida e observação ativa.
4. Unir bid e ask pelo timestamp, nunca pela posição da linha. As amostras de minuto sem volume não tinham índices perfeitamente iguais.
5. Tratar o volume do provedor como indicador de atividade dessa fonte, sem equipará-lo ao volume mundial de ouro.

Não basta excluir qualquer candle com high=low: um preço pode permanecer constante mesmo com observações reais. Atividade, calendário e timestamps precisam orientar a decisão.

Fontes: [downloader e código](https://github.com/Leo4815162342/dukascopy-node), [normalização dos candles](https://github.com/Leo4815162342/dukascopy-node/blob/master/src/data-normaliser/index.ts) e [horários publicados pela Dukascopy](https://www.dukascopy.com/europe/english/forex/forex_trading_accounts/link/).

## 3. USDT/USD: solução para a cobertura antiga

A Coinbase anunciou negociação de USDT em abril/2021. Nos testes, 27/04/2021 retornou vazio, enquanto as janelas testadas de novembro/2023 e novembro/2026 retornaram 24 horas cada. A janela de quatro horas de minutos recentes retornou 240 observações. Não se deve inferir a primeira data efetiva de candles apenas pela data anunciada de listagem.

A alternativa pública **Bitfinex `tUSTUSD`** foi verificada no próprio mapa de moedas: `UST` corresponde a Tether USDt. Não confundir esse código com o antigo UST da Terra.

Foi paginada a série horária para toda a janela de **28/08/2020 12:00 UTC a 08/11/2026 00:00 UTC**, com resultado de **54.261 horas únicas em 54.300 esperadas**, ou **39 ausências**. Foram seis páginas, respeitando o limite documentado. Isso oferece uma fonte observada de conversão desde o início, sem assumir USDC=USD.

Na implementação, escolher uma série primária consistente e comparar a sobreposição com Coinbase. As duas cotações representam mercados diferentes; discordâncias não devem ser removidas silenciosamente. As 39 ausências precisam ser localizadas antes de avaliar cobertura nos instantes críticos.

Fontes: [anúncio Coinbase](https://www.coinbase.com/en-fr/blog/tether-usdt-is-launching-on-coinbase-pro), [candles Coinbase](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles), [candles Bitfinex](https://docs.bitfinex.com/reference/rest-public-candles) e [configurações de moedas Bitfinex](https://docs.bitfinex.com/reference/rest-public-conf).

## 4. ETFs: arquivos reais e spreads oficiais

Foram baixados e abertos os arquivos XLSX oficiais de GLD e GLDM. Eles possuem fechamento, onças por cota, NAV, preço indicativo, midpoint em horário informado e outras colunas. As datas foram efetivamente lidas:

| ETF | Registros com data | Primeiro dia | Último dia retornado |
| --- | --- | --- | --- |
| GLD | 5.730 | 18/11/2004 | 05/11/2026 |
| GLDM | 2.186 | 26/06/2018 | 05/11/2026 |

A planilha não contém um livro intradiário completo. O NAV e o midpoint possuem horários próprios, que precisam ser respeitados em qualquer comparação. O arquivo também informa que a série histórica de LBMA Gold Price foi removida; não se deve prometer obtê-la ali.

As páginas State Street publicam a medida **30-Day Median Bid/Ask Spread**, além das taxas do fundo. Essa medida pode ancorar o custo atual com fonte oficial, mantendo sensibilidade. Ela não é o spread efetivo de cada operação histórica e não deve ser aplicada retroativamente como se fosse observado em 2020.

Fontes: [GLD](https://www.ssga.com/us/en/individual/etfs/spdr-gold-shares-gld), [GLDM](https://www.ssga.com/us/en/individual/etfs/spdr-gold-minishares-gldm), [arquivo GLD](https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en) e [arquivo GLDM](https://api.spdrgoldshares.com/api/v1/historical-archive?product=gldm&exchange=NYSE&lang=en).

Os avisos de uso dos arquivos restringem reprodução/redistribuição. O pacote do estudo deve privilegiar instruções de download e análises próprias, sem copiar os arquivos brutos para o repositório público.

## 5. O que limita a arbitragem executável

- **Livro atual:** os endpoints públicos de melhor bid/ask Binance e livro nível 1 Coinbase para PAXG responderam com preços e quantidades. Esses snapshots atuais não fornecem o histórico passado.
- **Arquivo público Binance:** o prefixo spot `monthly/bookTicker/PAXGUSDT/` consultado não listou arquivos. Isso não prova ausência de livro histórico em qualquer fornecedor.
- **Histórico especializado:** a Tardis lista PAXGUSDT desde 28/08/2020, com quotes e snapshots de livro. Foi acessada sem chave uma amostra real de quotes de 01/10/2026, com preços, quantidades e timestamps. A documentação oferece gratuitamente o primeiro dia de cada mês; acesso às demais datas depende de credenciais e plano compatível. Essa amostra pode calibrar spreads em datas limitadas, não reconstruir todos os fins de semana gratuitamente.
- **Empréstimo e short:** disponibilidade e custos específicos da conta não foram demonstrados. Taxa de empréstimo de outra moeda não substitui a de PAXG.
- **Mercado primário Paxos:** a documentação de cotações exige autenticação e condiciona as cotações de PAXG ao horário do ouro. Não dispomos de um histórico público de cotações executáveis da conta do participante.
- **Impacto e slippage:** candles e negócios não observam toda liquidez que poderia ser consumida. Sem histórico adequado, a análise permanece por hipóteses.

Fontes: [Tardis: disponibilidade e amostras](https://docs.tardis.dev/downloadable-csv-files/overview.md), [API dos datasets](https://docs.tardis.dev/downloadable-csv-files/api.md) e [cotações Paxos](https://docs.paxos.com/api-reference/endpoints/issuer-quotes/create-issuer-quote).

## 6. Ambiente e exportação

O ambiente executou Python 3.11.9 e Node 24.14.0. Foram importadas com sucesso as bibliotecas de análise e exportação necessárias, incluindo pandas, numpy, pyarrow, scipy, statsmodels, matplotlib e ReportLab.

Foi realizado um teste técnico em diretório temporário com dados explicitamente ilustrativos:

- gravação e leitura Parquet preservando UTC;
- geração de figura PNG;
- inserção da figura em PDF;
- confirmação com `pdfinfo`: uma página de 960×540 pontos, arquivo PDF válido de 22.920 bytes.

O teste confirma a cadeia de formatos, sem validar o pipeline econômico. `python-pptx` e LibreOffice não foram encontrados nesta consulta, mas o PDF final pode ser gerado diretamente com ReportLab; esses componentes não são bloqueadores.

## 7. Compromisso de implementação possível

É possível entregar download com cache e logs, painéis UTC com flags de moeda/atividade, métricas e intervalos, simulação condicional, comparação de custos, gráficos, apresentação PDF e código para reprodução. O núcleo pode operar com fontes públicas sem chave paga.

Antes dos resultados finais, ainda faltam download/validação dos demais arquivos, junção das fontes, auditoria de calendário, frescor de preços e cobertura dos instantes de sinal/entrada/saída. Não prometer arbitragem real executável onde faltam dados de acesso ou financiamento. A coleta de dados é viável; a qualidade da inferência depende dessa validação.
