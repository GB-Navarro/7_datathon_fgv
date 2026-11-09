# Especificação de implementação: O preço da promessa (versão 100% dados gratuitos)

Documento para agentes de código e orquestradores. Tem escopo, fontes com endpoints, esquemas, definições matemáticas, testes estatísticos, figuras, critérios de aceite, briefs por agente e plano dos slides. O guia intuitivo está em `projeto_humanos.md`.

**Prazo:** domingo 2026-11-08, 23:59 horário de Brasília (= 2026-11-09 02:59 UTC). Meta interna de submissão: 22:00 Brasília. Entregáveis: PDF de apresentação e scripts em `.txt` (Python), conforme o regulamento do 7º Datathon da FGV EESP.

---

## Texto canônico do problema, da pergunta e da tese

Todo texto, slide e resposta usa esta redação.

- **Problema:** tokens de ativos reais prometem preço fiel ao ativo e negociação 24 horas por dia; ninguém mediu direito se a promessa é cumprida, a que custo e com que riscos, nem se o mercado vai melhorar sozinho.
- **Pergunta central:** o ouro tokenizado cumpre a promessa de valer o ouro? E, se melhora com o tempo, é por competição entre arbitradores ou por infraestrutura?
- **Hipótese:** o custo de manter o token no preço é moderado em dias normais e tem risco de cauda em fins de semana e estresse; a arbitragem rende pouco demais para atrair capital profissional; logo, a maturidade depende de infraestrutura e adoção. A hipótese é testada pela regra de decisão H0 (seção 7) e pode ser invertida pelos dados.
- **Em uma frase:** "Medimos se o ouro tokenizado cumpre a promessa de valer ouro, quanto custa e que riscos tem, e simulamos se ele amadurece por competição ou por infraestrutura."
- **Vocabulário para o público:** "erro do token na reabertura" = diferença entre o preço do token e o do ouro quando o mercado abre; "poça de lucro" = quanto a arbitragem rende por ano, depois dos custos; "equilíbrio" = a partir de quantos meses o token fica mais barato que o ETF.

---

## 0. Regras invioláveis

1. **Só dados gratuitos.** Nenhum dado de Bloomberg. Sem chave paga. Chaves gratuitas permitidas: Etherscan.
2. **Tempo:** todo timestamp em UTC, `datetime64[ns, UTC]`. Detectar unidade pelo tamanho: valores acima de 1e14 são microssegundos, entre 1e11 e 1e14 são milissegundos.
3. **Unidade:** preço em dólares por 1 onça troy fina. PAXG, XAUT e XAUUSDT valem 1 onça por unidade. Desvio sempre em pontos-base (bps), `1 bp = 1e-4`.
4. **Sem look-ahead:** o que for usado em t usa só informação disponível até t. Séries diárias (Fear & Greed) entram com defasagem de 1 dia.
5. **Pré-registro:** parâmetros, limiares dos degraus e regras de estratégia ficam em `config/params.yaml` antes de olhar qualquer resultado. Toda variante testada vai para `results/variants.csv`.
6. **Honestidade nos resultados:** se um resultado contrariar a hipótese, o título do slide muda (ver seção 12). Proibido ajustar parâmetros depois de ver o resultado.
7. **Licença:** não versionar dados brutos da Dukascopy. Versionar código, parâmetros e saídas agregadas.
8. **Reprodutibilidade:** seeds fixas, `requirements.txt`, log de cada download com URL, data e hash.
9. **Texto:** português, sem travessões longos.
10. **Slides:** no máximo 10 slides no PDF, limite informado no material de abertura (confirmar no formulário de envio). Código e materiais suplementares são recomendados, não obrigatórios.

---

## 1. Definição de pronto e mínimo viável

A história do trabalho tem três tempos: **hoje** (oportunidades e riscos), **como evolui** (arbitragem e amadurecimento) e **e se continuar** (cenários simulados).

**Mínimo viável (MVP), que nunca sai:**

- [ ] `panel_weekends.parquet` com os fins de semana desde 2020-08-28.
- [ ] Oportunidades hoje: A (convergência na reabertura) e B (mercado primário, por preço), com ganho bruto e líquido (T1, F1).
- [ ] Custo do token contra o ETF e ponto de equilíbrio em meses (T4).
- [ ] Mapa de riscos medidos (T3, F9).
- [ ] Amadurecimento: regressão agrupada M1 e desvio horário de dias úteis M3 (F3).
- [ ] Simulador de cenários calibrado com os dados (`simulador_cenarios.py`, F10, T5).
- [ ] PDF com 10 slides, fontes em cada figura, e scripts em `.txt` (recomendados).

**Completo:** o MVP mais resposta da oferta on-chain (F2), eventos de infraestrutura (F5), benchmark do ETF (F4), fidelidade e sinal de fim de semana (F6, F8), oportunidades C e D, carteira (F7), análise de sensibilidade do simulador, caso ao vivo.

**Ordem de corte** (se faltar tempo): carteira e D, depois sinal de fim de semana, depois ETF, depois C, depois os eventos de infraestrutura.

## 2. Estrutura do repositório

```
preco-da-promessa/
  README.md  requirements.txt  run_all.py  Makefile
  config/ params.yaml  sources.yaml  events.csv
  data/ raw/  interim/  panel/        # raw e interim fora do git
  src/ fetch/  clean/  panel/  analysis/  figures/  utils/
  tests/
  results/        # csv, png, RESULTS.md
  slides/
  scripts_txt/
```

---

## 3. Ambiente

Python 3.11. Pacotes: `pandas`, `numpy`, `pyarrow`, `requests`, `httpx`, `tqdm`, `statsmodels`, `scipy`, `scikit-learn`, `matplotlib`, `pyyaml`, `openpyxl`, `yfinance`, `pycryptodome`. Node 18+ para `dukascopy-node`. Slides: `python-pptx` mais LibreOffice para converter em PDF, ou LaTeX Beamer.

---

## 4. Fontes de dados e como baixar

Janela: `2020-08-28` (primeiro dia do PAXGUSDT na Binance) a `2026-11-08` (UTC). O PAXG existe desde setembro de 2019, mas a Binance só listou o par contra USDT em 28/08/2020. Todos os downloads gravam em `data/raw/{fonte}/`.

### 4.1 Binance, arquivo público e API

Base: `https://data.binance.vision/`. O arquivo tem klines, trades, aggTrades, e para futuros também bookTicker e fundingRate ([binance-public-data](https://github.com/binance/binance-public-data)).

```
spot klines mensal: data/spot/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY}-{MM}.zip
spot klines diário: data/spot/daily/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY}-{MM}-{DD}.zip
```

**Datas de início verificadas:** `PAXGUSDT` a partir de 2020-08-28 (PAXG/USDT abriu dois dias depois dos pares contra BTC, BNB e BUSD); `XAUTUSDT` só a partir de 2026-03-27 (listagem com etiqueta de volatilidade), então o XAUT na Binance serve apenas de robustez recente; `XAUUSDT` perpétuo desde 2026-01-05.

Símbolos spot: `PAXGUSDT`, `XAUTUSDT`, `BTCUSDT`, `ETHUSDT`, `USDCUSDT`. Colunas dos klines: `open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base, taker_buy_quote, ignore`.

Regras:
- Listar o diretório do par para achar o primeiro mês disponível: `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/PAXGUSDT/1h/`.
- O mês corrente não tem arquivo mensal: usar arquivos diários, ou a API `GET https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1h&startTime={ms}&limit=1000`.
- Manter o mesmo par (USDT) ao longo de toda a série. A taxa de negociação padrão da Binance no spot é 0,10% (0,075% pagando em BNB), o que equivale a 10 bps (7,5 bps) por operação.

**Perpétuo de ouro XAUUSDT** (listado em 2026-01-05 10:00 UTC), pela API de futuros:

```
GET https://fapi.binance.com/fapi/v1/klines?symbol=XAUUSDT&interval=1h&startTime={ms}&limit=1500
GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=XAUUSDT&startTime={ms}&limit=1000
```

Paginar avançando `startTime` até a data final. Se o arquivo público de futuros tiver o par (`data/futures/um/monthly/klines/XAUUSDT/1h/`), pode ser usado, mas a API basta.

### 4.2 Coinbase (PAXG em dólar)

```
GET https://api.exchange.coinbase.com/products/PAXG-USD/candles?granularity=3600&start={ISO}&end={ISO}
GET https://api.exchange.coinbase.com/products/USDT-USD/candles?granularity=3600&start={ISO}&end={ISO}
```

No máximo 300 velas por chamada; a resposta vem como `[time, low, high, open, close, volume]` em ordem decrescente. Janelas de até 300 horas, com pausa de 0,2 s entre chamadas. Se `USDT-USD` não existir, usar `q = 1 / USDCUSDT` (supondo USDC = 1) e declarar.

### 4.3 Dukascopy (ouro à vista, horário, com bid e ask)

Ferramenta gratuita [`dukascopy-node`](https://github.com/Leo4815162342/dukascopy-node), que exige Node.js 20 ou superior. Antes do primeiro download, rodar `npx dukascopy-node --install-browser`: a ferramenta pode precisar do Chromium para passar pelo desafio de segurança do servidor. Conferir as opções com `npx dukascopy-node --help`.

Instrumentos e início dos dados, segundo o README da ferramenta: `xauusd` (ouro contra dólar, desde 03/06/1999), `gldususd` (SPDR Gold Shares ETF, em contrato por diferença), `dollaridxusd` (índice do dólar) e `usa500idxusd` (S&P 500).

```
npx dukascopy-node -i xauusd -from 2020-08-28 -to 2026-11-08 -t h1 -p bid -f csv
npx dukascopy-node -i xauusd -from 2020-08-28 -to 2026-11-08 -t h1 -p ask -f csv
npx dukascopy-node -i gldususd -from 2020-08-28 -to 2026-11-08 -t h1 -p bid -f csv
```

Usar `h1` (velas de 1 hora), não `m1`: o volume de dados e o tempo de download são muito menores e bastam. Baixar em blocos de 12 meses em paralelo se o download único for lento. Timestamps em UTC. Velas sem negócio podem ser omitidas, e a detecção de fim de semana usa lacunas entre velas (seção 6.1).

**Risco real:** um erro HTTP 403 sem desafio de segurança interrompe o download (issue 264 do projeto). Se ocorrer, abrir a página de exportação histórica da Dukascopy em um navegador comum para confirmar acesso, atualizar a ferramenta e, se persistir, usar os planos B da seção 4.7.

### 4.4 SPDR Gold Shares (ETF)

- **Preço da cota:** `gldususd` da Dukascopy em velas de 1 hora (mesma fonte e mesmo relógio do ouro à vista), válido nos horários da bolsa americana. Alternativa: `yfinance.download("GLD", interval="1d")` ou CSV diário do Stooq (`https://stooq.com/q/d/l/?s=gld.us&i=d`).
- **NAV e onças:** planilha "Historical Archive (XLSX)" na página oficial `https://www.spdrgoldshares.com/usa/gld/`. Localizar o link no HTML. Inspecionar as colunas (data, NAV por cota, onças por cota ou por cesta, total de onças).
- Taxa de administração: 0,40% ao ano.

### 4.5 On-chain: criação e resgate de PAXG

**Como a Paxos opera** (blog oficial da Paxos): os tokens são cunhados na blockchain e ficam em carteiras de estoque da Paxos; quando um cliente compra direto, os tokens são transferidos do estoque para a carteira dele. Logo, `SupplyIncreased` e `SupplyDecreased` medem a **reposição do estoque**, em lotes, e não cada criação ou resgate de cliente. O sinal por cliente está nas **transferências a partir de e para as carteiras de estoque da Paxos**.

- Contrato (proxy) na Ethereum: `0x45804880De22913dAFE09f4980848ECE6EcbAf78`, 18 casas decimais ([repositório da Paxos](https://github.com/paxosglobal/paxos-gold-contract)).
- **Descobrir o controlador de oferta:** `GET https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_call&to=0x45804880De22913dAFE09f4980848ECE6EcbAf78&data=0xe7ba1012&tag=latest&apikey={KEY}` (seletor de `supplyController()`). A resposta é o endereço preenchido a 32 bytes. Conferir no Etherscan se há outras carteiras da Paxos com grandes fluxos e incluí-las.
- `topic0` calculados com keccak256:

```
Transfer(address,address,uint256)   = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
SupplyIncreased(address,uint256)    = 0xf5c174d57843e57fea3c649fdde37f015ef08750759cbee88060390566a98797
SupplyDecreased(address,uint256)    = 0x1b7e18241beced0d7f41fbab1ea8ed468732edbcb74ec4420151654ca71c8a63
```

- **Criação para clientes** (saída do estoque): logs `Transfer` com `topic1` = controlador preenchido a 32 bytes (`0x000000000000000000000000` seguido do endereço sem o `0x`). **Resgate** (entrada no estoque): `Transfer` com `topic2` = controlador, usando o operador de tópicos da API (por exemplo `topic0_2_opr=and`); conferir os nomes dos operadores na documentação do endpoint `getLogs` por tópicos.
- API Etherscan V2 com chave gratuita (3 a 5 chamadas por segundo e 100 mil por dia):

```
GET https://api.etherscan.io/v2/api?chainid=1&module=logs&action=getLogs
    &address=0x45804880De22913dAFE09f4980848ECE6EcbAf78&topic0={TOPIC}&topic1={PAD}
    &fromBlock={A}&toBlock={B}&page=1&offset=1000&apikey={KEY}
```

Começar em `fromBlock=8000000`. Se uma janela devolver 1000 registros, dividir o intervalo. Campos de cada log: `timeStamp`, `blockNumber` e `data` vêm em **hexadecimal** (`int(x,16)`); dividir `data` por 1e18 para obter onças.
- **Janela da análise de oferta: até 2026-06-24.** O PAXG nativo na Solana (Token-2022) foi lançado em 25/06/2026, com ponte pela LayerZero a partir da Ethereum, e passa a ser emitido também nessa rede; depois dessa data, os eventos da Ethereum subestimam a criação. Não somar a Solana (risco de contar duas vezes o que atravessa a ponte).
- Conferência: o acumulado líquido de `SupplyIncreased` menos `SupplyDecreased` deve bater com `totalSupply()` do contrato (`module=stats&action=tokensupply&contractaddress=...`), tolerância de 1%.

Saída: `data/interim/paxg_flows.parquet` com `ts_utc, block, tx_hash, kind (inv_outflow|inv_inflow|mint|burn), amount_oz`.

### 4.6 Fear & Greed e demais

- `GET https://api.alternative.me/fng/?limit=0&format=json` (diário desde 2018-02-01; campos `value`, `timestamp`).
- Taxas da Paxos (leitura manual, página oficial de taxas do PAXG, `https://support.paxos.com/articles/2899561282-pax-gold-fees`). Registrar em `config/params.yaml`: criação isenta até 2026-09-30 na versão da página de 13/08/2026 e até 2027-01-01 em outra versão consultada (**conferir a vigente**); destruição a partir de 0,125% sobre resgate líquido em 30 dias, em tabela escalonada, desde 2026-09-01; 5 bps na conversão em espécie. **Conferir a página**, que pode mudar. Taxa de negociação em livro de ofertas é a da corretora, não a da Paxos.

### 4.7 Planos B

| Falha | Alternativa |
| --- | --- |
| Dukascopy bloqueia (erro 403) ou não baixa | Ouro à vista de outra fonte gratuita (Stooq `xauusd`, `i=h` se existir), ou `yfinance` com `GC=F` e `GLD` (só dias úteis e horário de bolsa); sem ouro intradiário, a oferta A e a maturidade M1 ficam no nível diário e o texto declara isso |
| XAUUSDT não aparece na API | Usar só a análise de reabertura (sem evento nem oportunidade D) |
| Etherscan sem chave | RPC público; se falhar, a oferta on-chain vira apenas contexto e H2(ii) sai |
| Coinbase sem PAXG-USD em toda a história | Dispersão (C) só no período disponível |
| SPDR XLSX não encontrado | Omitir F4 e o benchmark do ETF; manter a maturidade sem a comparação |

---

## 5. Painéis (contratos de dados)

### 5.1 `data/interim/token_1h.parquet`
`ts_utc` (início da vela), `symbol`, `open, high, low, close, volume, quote_volume, trades`.

### 5.2 `data/interim/gold_1h.parquet`
`ts_utc` (início da vela), `bid_open, bid_high, bid_low, bid_close, ask_open, ask_high, ask_low, ask_close`, mais `mid_*` (média de bid e ask), `spread_open_bps = (ask_open - bid_open) / mid_open * 1e4` e `spread_close_bps = (ask_close - bid_close) / mid_close * 1e4`.

### 5.3 `data/panel/panel_weekends.parquet` (uma linha por fim de semana)
`weekend_id, t_c (fechamento de sexta), t_0 (reabertura), S_c, S_0, spread_gold_0_bps, p_c, p_0, q_c, q_0, g_bps, m_bps, e_bps, e_te (erro em t_0+1h), e_ts1, e_ts6, e_ts24 (erro h horas depois de t_e), vol_token_0_usd, regime (big_gap|small_gap), year, semester`.

### 5.4 `data/panel/panel_hourly.parquet`
Uma linha por hora em que o ouro negocia: `ts_utc, d_bps, d_usd_bps (contra Coinbase), c_bps (Binance contra Coinbase), s_token_bps (Corwin-Schultz), vol_token_usd, is_ny_close, fng_lag1, gold_rv_24h`.

### 5.5 `data/panel/panel_daily.parquet`
`date_utc, r_token, r_gold, r_btc, r_eth, fng_lag1, btc_rv_7d, inv_outflow_oz, inv_inflow_oz, etf_premium_bps, etf_ozps`.

---

## 6. Definições matemáticas

### 6.1 Fins de semana e reabertura

```python
g = gold_1h.sort_values("ts_utc")
gap = g["ts_utc"].shift(-1) - g["ts_utc"]            # tempo entre início de velas consecutivas
closures = g[gap > pd.Timedelta(hours=36)]           # última vela antes de cada fechamento longo
# t_c = fim da última vela (início + 1h); t_0 = início da primeira vela depois do fechamento
# manter só fechamentos que contêm um sábado (fim de semana); feriados ficam de fora
```

Não codificar o horário de reabertura: ele muda com o horário de verão dos EUA e é detectado pela lacuna.

### 6.2 Preço em um instante t

- **Token:** `p(t) = close` da vela Binance que termina em `t`, isto é, a vela com `ts_utc = t - 1h`.
- **Ouro:** `S(t) = mid_open` da vela Dukascopy que começa em `t` (usado na reabertura, em que não há vela anterior); em dias úteis, `S(t) = mid_close` da vela que termina em `t`.
- **Stablecoin:** `q(t)` = valor do USDT em dólares (Coinbase `USDT-USD`, ou `1/USDCUSDT`).

### 6.3 Quantidades de fim de semana

```
g_w = (S(t_0) / S(t_c) - 1) * 1e4        # salto do ouro, bps
m_w = (p(t_0)*q / (p(t_c)*q_c) - 1) * 1e4  # movimento do token até a hora anterior à reabertura, bps
e_w = (p(t_0)*q - S(t_0)) / S(t_0) * 1e4   # erro do token na reabertura, bps
```

Identidade de conferência: `e_w ≈ e_c + (m_w - g_w)`, em que `e_c` é o erro no fechamento de sexta. É exata em retornos logarítmicos e, em retornos simples, vale a menos de um termo de segunda ordem (cerca de `(m_w - g_w) * (g_w - e_c)`). O teste unitário usa movimentos sintéticos de até 0,5% e exige erro de no máximo 1 bp.

### 6.4 Desvio em dia útil

`d_t = (p(t)*q(t) - S(t)) / S(t) * 1e4`, usando fechamento de vela dos dois lados, em horas em que o ouro negocia. `d_usd` usa `PAXG-USD` da Coinbase no lugar de `p*q`.

### 6.5 Spread do token (Corwin e Schultz, 2012; conferir no artigo)

Para velas horárias consecutivas `t` e `t+1`:

```
beta  = sum_{j in {t,t+1}} [ln(H_j / L_j)]^2
gamma = [ln(max(H_t,H_{t+1}) / min(L_t,L_{t+1}))]^2
alpha = (sqrt(2*beta) - sqrt(beta)) / (3 - 2*sqrt(2)) - sqrt(gamma / (3 - 2*sqrt(2)))
S = 2 * (exp(alpha) - 1) / (1 + exp(alpha)),  truncar em zero
s_token_bps = S * 1e4
```

Calibração: se der tempo, gravar o livro de `PAXGUSDT` (`GET https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT`, a cada 10 segundos) e comparar com o estimador nas horas em comum; reportar o viés.

### 6.6 Custos

```
f  ∈ {2, 5, 10} bps por operação no token   (institucional, intermediário, varejo padrão da Binance); base = 5, que é favorável a um participante com desconto de volume. O varejo padrão paga 10 bps (7,5 com BNB).
gold_comm = 1 bp por operação na perna de ouro; s_gold = média de spread_close_bps das velas que terminam em t_e e em t_s (Dukascopy); na variante de sensibilidade com entrada em t_0, usar spread_open_bps
kappa = 2 bps (conversão de stablecoin)
C_A = 2*f + s_token + s_gold + 2*gold_comm + kappa     # round trip, s em bps (meio spread ×2 = spread cheio)
```

### 6.7 Oportunidade A: convergência depois da reabertura

O **erro de reabertura** `e_w` (6.3) é a medida de qualidade do preço do token. Ele não é, por si só, uma operação executável: no primeiro instante depois da reabertura o ouro à vista tem spread largo e preços pouco confiáveis. A operação testada entra **uma hora depois**, quando a liquidez volta.

```
t_e = t_0 + 1h ;  saída t_s = t_e + h,  h ∈ {1, 6, 24} horas
e(t) = (p(t)*q - S(t)) / S(t) * 1e4          (p e S pela regra de 6.2; em t_e e t_s, S = mid_close da vela que termina no instante)
filtro: |e(t_e)| > m,  m ∈ {0, 10, 20} bps
pnl_i = sign(e(t_e)) * (e(t_e) - e(t_s)) - C_A
```

Convenção: `e>0` (token caro) = vender token e comprar ouro, com ganho quando `e` cai. **Variante pré-registrada: entrada em `t_e`, h = 6, m = 10, f = 5.** Variante de sensibilidade: entrada em `t_0`, para mostrar quanto do ganho aparente vem da iliquidez do primeiro instante. Todas vão para `results/variants.csv`.

**Capacidade:** `0,05 * média(quote_volume da vela [t_e-1h, t_e) e da vela [t_e, t_e+1h))`, em dólares.

**Regimes:** `big_gap` se `|g_w|` está no quartil superior da amostra inteira; caso contrário `small_gap`. Descritivo, não preditivo.

**Expectativa honesta:** com os custos de 6.6, o ganho líquido deve ser raro e pequeno (ver a simulação de sensibilidade na seção 15). O resultado é reportado como está.

### 6.8 Oportunidade B: mercado primário (limite superior)

Referência diária às 15:00 UTC: `d_15 = d_t` nessa hora. Limiares (em bps): criação se `d_15 > f_plus + (s_token + s_gold)/2 + kappa`, com `f_plus ∈ {0, 5, 12.5}`; resgate se `d_15 < -(f_minus + (s_token + s_gold)/2 + kappa)`, com `f_minus ∈ {12.5, 25, 100}` (a Paxos cobra cerca de 0,125% nos pedidos maiores e cerca de 1% nos pequenos; a criação mínima é de 1 onça). Ganho superior por dia = `|d_15| - limiar`. Capacidade realizada = mediana diária de `(mint_oz + burn_oz) * S`. O preço real da Paxos para criar e resgatar não é observado: o resultado é limite superior e deve estar escrito assim no slide.

### 6.9 Resposta da oferta (H2)

Frequência diária (o estoque da Paxos se movimenta em lotes), amostra de 2020-08-28 a 2026-06-24. A variável é a **saída líquida do estoque** no dia: `F_t = inv_outflow_oz - inv_inflow_oz` (onças entregues a clientes menos onças devolvidas). `E+_t = max(d_15 - B+, 0)` e `E-_t = max(-d_15 - B-, 0)`, com `B+ = f_plus + ...` e `B- = f_minus + ...` na variante base (`f_plus = 0`, `f_minus = 12.5`).

```
F_{t+1} = a + b_plus*E+_t + b_minus*E-_t + g'X_t + sum_{k=1..5} rho_k F_{t-k} + u
X_t = fim de semana anterior, fng_lag1, gold_rv_24h, log volume do token
```

Erros de Newey-West com 5 defasagens. Esperado: `b_plus > 0`, `b_minus < 0`. Robustez: usar `SupplyIncreased` e `SupplyDecreased` agregados por semana. O fluxo de estoque também reflete a demanda de clientes e a gestão do estoque pela Paxos: o que se mede é a resposta da oferta ao desvio, não a identidade de quem a provoca.

### 6.10 Oportunidade C: dispersão entre corretoras

`c_t = (p_Binance(t)*q(t) - p_Coinbase(t)) / p_Coinbase(t) * 1e4`. Custo: `C_C = 2*f + (s_B + s_C)/2 + kappa` (negociação nos dois lados, com estoque nos dois). Ganho líquido por hora `max(|c_t| - C_C, 0)`; capacidade `0,05 * min(quote_volume_B, quote_volume_C)`. Reportar fração de horas com ganho positivo, mediana e percentil 95, por regime.

### 6.11 Oportunidade D: carrego do perpétuo

Período: `2026-01-05 10:00 UTC` até hoje. Posição: comprado em PAXG spot, vendido em XAUUSDT. Por dia:

```
pnl_bps_dia = sum_{k no dia} funding_k * 1e4        # funding paga a quem está vendido se positivo
              + (dlnP_spot - dlnP_perp) * 1e4          # risco de base
custos amortizados em 30 dias: (4*f + s_token + s_perp) / 30, com s_perp = 1 bp (parâmetro)
```

Reportar carrego bruto e líquido anualizados, Sharpe diário e pior drawdown. O XAUUSDT não é ouro físico: o risco de base está no resultado.

### 6.12 Maturidade (H3)

Amostra a partir de 2020-08-28. **Atenção ao poder:** a simulação da seção 15 mostra que 14 semestres de 26 fins de semana detectam uma queda forte do repasse com cerca de 60% a 80% de chance e uma queda moderada com 20% a 35%. Por isso o teste principal é uma regressão agrupada com tempo contínuo, e há um segundo indicador com muito mais observações.

- **M1, repasse do estresse ao erro (teste principal):** `|e_w| = a + b*|g_w| + c*tau + d*(|g_w|*tau) + u`, com `tau` em [0,1] (fração do período) e erros HC3. `d < 0` indica repasse caindo. Mostrar, como figura descritiva, `b_s` por semestre (pelo menos 20 fins de semana) com intervalo por bootstrap.
- **M2, velocidade de fechamento:** `kappa_h = 1 - |e(t_e+h)| / |e(t_e)|` para `h ∈ {1, 6}`, mediana por semestre entre fins de semana com `|e(t_e)| >= 10`.
- **M3, desvio em dia útil (indicador com mais dados):** mediana e percentil 95 de `|d_t|` por trimestre (dezenas de milhares de horas por ano); meia-vida do AR(1) horário `d_{t+1} = phi*d_t + u`, `HL = ln(0.5)/ln(phi)`; tendência da mediana trimestral por regressão do logaritmo da mediana sobre o tempo com erros de Newey-West.
- **Spread efetivo (M4):** mediana trimestral de `s_token_bps`.
- **M5, teste da competição (o elo entre arbitragem e melhora do erro):** por trimestre `q`, `Delta M3_{q+1} = a + b*A_q + c'*Z_q + u`, em que `A_q` é a atividade de arbitragem no trimestre (volume de fluxos do estoque da Paxos em onças e número de violações exploradas pela regra A ou B) e `Z_q` controla volatilidade do ouro, fração de semanas de estresse e liquidez geral do token. Erros de Newey-West com 2 defasagens e cerca de 22 a 25 trimestres. É previsão, não causalidade. Alimenta a condição (c) da regra H0.
- **Benchmark do ETF (diário e horário):** `prem_t = P_close / (ozps_t * S(close)) - 1`. Com `gldususd` da Dukascopy, o preço da cota e o ouro à vista vêm da mesma fonte e do mesmo relógio. `ozps_t = NAV_t / S_LBMA_proxy_t` (se o XLSX trouxer onças por cota, usar direto), com `S_LBMA_proxy` = `mid` às 15:00 de Londres (`pytz`). Medidas: mediana e percentil 95 de `|prem|` e meia-vida do AR(1). A distância de maturidade em cada indicador é o do token menos o do ETF no mesmo trimestre. Comparar sobretudo a **variação ao longo do tempo**, não o nível, porque o ETF e o token têm ruídos de medição diferentes.
- **Extrapolação de paridade:** só se o intervalo da inclinação de Theil-Sen da distância M3 excluir zero com sinal negativo; então `t* = D_último / (-beta)` anos, com intervalo de bootstrap, marcado como extrapolação e fora do título do slide. Caso contrário, reportar "tendência não detectada".

### 6.13 Eventos de infraestrutura (H4, exploratório)

Dois eventos de data conhecida. **Não é preciso dado da CME**: o que se usa é a data, e o desfecho é o erro do token medido com dados gratuitos.

```
|e_w| = a + b*|g_w| + c1*Perp + c2*Oz1 + d1*(|g_w|*Perp) + d2*(|g_w|*Oz1) + u
Perp = 1 para reaberturas a partir de 2026-01-05 (perpétuo XAUUSDT na Binance)
Oz1  = 1 para reaberturas a partir de 2026-07-24 (1OZ da CME 24/7, conforme o aviso da CME)
```

HC3. Os coeficientes de interesse são `d1` e `d2` (efeito no repasse do estresse). Reportar **tamanho do efeito com intervalo de 95%**, não só significância. **Placebos:** 30 datas de corte sorteadas entre 2021-01-01 e 2025-12-31, cada uma com pelo menos 40 fins de semana de cada lado; comparar `d1_real` com a distribuição de `d_placebo`. Segundo evento candidato, a confirmar a data: futuros de PAXG na Deribit (dezembro de 2024).

**Limites declarados:** (i) são cerca de 43 fins de semana depois do perpétuo e cerca de 15 depois do 1OZ, e a simulação da seção 15 mostra poder baixo (cerca de 38% para uma queda de 0,10 no repasse com 44 fins de semana depois do evento, e cerca de 17% com 14); (ii) 2026 teve volatilidade extrema do ouro e vários eventos ao mesmo tempo; (iii) depois do 1OZ o ouro negocia no fim de semana, então o salto `g_w` medido na reabertura do ouro à vista pode encolher por construção: conferir a distribuição de `|g_w|` antes e depois. **Regra de texto:** resultado não significativo vira "não detectamos efeito", nunca "o evento não alterou".

### 6.14 Degrau 1: veículo 24/7

Mediana de `s_token_bps` por ano e por hora da semana; participação de sábado e domingo no `quote_volume`. **Critério pré-registrado:** mediana do spread efetivo ≤ 10 bps nos últimos 12 meses e volume de fim de semana relevante (participação > 15%).

### 6.15 Degrau 2: proxy e proteção (H5)

Retornos diários em horário comum, às 21:00 UTC (fechamento de vela dos dois lados), de segunda a sexta; o retorno de segunda cobre o fim de semana para os dois ativos.

- Fidelidade: `R_token = a + beta*R_gold + u`, `beta`, `R²`, erro de fidelidade `TE_h = std(R_token - R_gold)` anualizado, e deriva (média da diferença, anualizada), para horizontes `h ∈ {1, 5, 21, 63}` dias úteis sem sobreposição.
- Estresse: dias de ouro com `|R_gold| >= 2*sigma` (sigma móvel de 252 dias, só passado), e dias de estresse cripto (`fng_lag1 <= 25` ou `R_btc <= -5%`). Razão de captura `sum(R_token)/sum(R_gold)` nos dias de estresse de ouro.
- **Critério pré-registrado:** `beta` em [0,95; 1,05], razão de captura em [0,8; 1,2], `TE_21` ≤ 100 bps.
- **Carteira** (teste de 2024-01-01 a 2026-11-07, treino até 2023-12-31): S0 = 60% BTC e 40% ETH; S1 = 80% de S0 mais 20% PAXG; S2 = PAXG em 10% na calma e 30% em estresse, estresse = `fng_lag1 <= 25` ou volatilidade realizada de 7 dias do BTC acima do percentil 80 do treino. Rebalanceamento às segundas 00:00 UTC; custo de 10 bps por lado sobre o valor negociado. Métricas: retorno e volatilidade anualizados, perda máxima, CVaR 5% diário, Sharpe, giro, e retorno médio nos 5% piores dias do BTC. Bootstrap em blocos estacionário (bloco médio de 10 dias, 2.000 réplicas) para `MaxDD(S1) - MaxDD(S0)` e `MaxDD(S2) - MaxDD(S0)`.

### 6.16 Degrau 3: sinal de fim de semana (H6)

```
g_w = a + b * m_w + u                         # m_w usa o preço até a hora anterior à reabertura
```

OLS com HC3 na amostra inteira (inclinação e intervalo) e **previsão fora da amostra**: janela expansiva, treino até 2022-12-31, previsão semana a semana a partir de 2023-01-01.

```
R2_OS = 1 - sum((g - g_hat)^2) / sum(g^2)         # benchmark: previsão zero (nenhum salto)
Clark-West: f_w = g^2 - [(g - g_hat)^2 - g_hat^2]; teste t unilateral da média de f_w com erros HAC
acerto = fração de semanas com sinal(g_hat) = sinal(g), entre as semanas com |g| > 5 bps
```

**Critério pré-registrado (métricas robustas):** razão `MAE(modelo)/MAE(previsão zero) <= 0,60`, correlação de postos de Spearman entre `m_w` e `g_w` de pelo menos 0,80, acerto direcional de pelo menos 70% entre as semanas com `|g| > 10` bps, e p de Clark-West < 0,10. O `R2_OS` é reportado apenas como medida descritiva, com intervalo de bootstrap, porque medidas de variância são instáveis com poucos saltos enormes (a simulação da seção 15 mostra IC95% de 0,37 a 0,67 com 330 fins de semana e de -0,32 a 0,74 em um ano). Como comparação (não como critério), repetir com o movimento de fim de semana do perpétuo XAUUSDT, para ver se o token acrescenta informação.

### 6.17 Degrau 4

Não medido. O slide cita RedStone (menos de 2% do mercado como colateral) e lista as condições que faltam (liquidez, resiliência em liquidações, produtos com rendimento). Cenários só em palavras condicionais.

---

### 6.18 Mapa de riscos medidos (hoje)

Cada risco tem uma medida gratuita ou uma fonte documental. Saídas: `results/T3_riscos.csv` e F9.

| Risco | Medida | Fonte |
| --- | --- | --- |
| Cauda do erro no fim de semana | p95 e máximo de `abs(e_w)` por regime; os 5 piores fins de semana (data, `g_w`, `m_w`, `e_w`); fração com `abs(e_w) > 50` bps | `panel_weekends` |
| Stablecoin | máximo e percentil 99 de `abs(q - 1)` em bps, com data; contribuição ao desvio (H3 de 6.2) | Coinbase `USDT-USD` ou `1/USDCUSDT` |
| Fragmentação entre corretoras | p95 de `abs(c_t)` (Binance contra Coinbase) | 6.10 |
| Liquidez em estresse | razão spread mediano em estresse contra calma; razão volume de fim de semana em estresse contra calma | 6.5 |
| Emissor e resgate | armazenamento zero hoje, com cláusula de diluição nos termos; resgate físico a partir de cerca de 430 PAXG; taxas de resgate de 0,125% a cerca de 1% | Página de taxas da Paxos; termos |
| Colateral em DeFi | menos de 2% do mercado de ouro tokenizado é usado como colateral (cerca de US$ 63 milhões de XAUT e PAXG na Aave e na Morpho); liquidações de XAUT na Aave em 23/03/2026 sem interrupção | RedStone, 30/07/2026 |
| Concentração | PAXG e XAUT somam cerca de 97% da oferta de ouro tokenizado | Relatórios de mercado (DWF Labs) |

### 6.19 Simulador de cenários

Arquivo: `simulador_cenarios.py` (já entregue com o plano; testes com `--selftest`). Ele simula, fim de semana a fim de semana, o salto do ouro e o erro do token na reabertura, e mede, por ano e por cenário: erro mediano e de cauda, fração de fins de semana com ganho líquido de arbitragem, poça de lucro em US$ por ano para três níveis de acesso (taxa de 10, 5 e 2 bps), ponto de equilíbrio do token contra o ETF e risco de cauda.

```
g_w   = sigma_g * m_regime * t_nu / sqrt(nu/(nu-2))            salto do ouro, cauda pesada
|e_w| = a_y + b_y*|g_w| + u_w                                   erro do token
C_w   = 2*fee + (s_token + s_gold)*spread_y*(mult se estresse) + 2*gold_comm + conv
net_w = max(kappa*|e_w| - C_w, 0)
pool  = soma_w part * V_y * net_w / 1e4                         US$ por ano
equilibrio_y = 12*(C_token_y - etf_rt) / (etf_fee - storage_y)  meses
```

**Calibração (gerar `config/cal.json` a partir dos dados; os padrões do script são ilustrativos):**

| Parâmetro | Como estimar |
| --- | --- |
| `sigma_g`, `nu_g` | desvio-padrão robusto (1,4826 vezes o MAD) e máxima verossimilhança t de Student de `g_w` nos últimos 24 meses, em semanas de calma |
| `p_stress`, `mult_stress` | fração de semanas `big_gap` e razão entre os desvios de `g_w` em estresse e calma |
| `a0`, `b0`, `u_scale`, `u_nu` | regressão `abs(e_w) = a + b*abs(g_w) + u` nos últimos 12 a 24 meses; ajuste de escala e graus de liberdade aos resíduos positivos |
| `stress_u_mult` | razão da escala dos resíduos em estresse contra calma |
| `fee` | 5 bps (intermediário); o padrão da Binance é 10 bps (7,5 com BNB) |
| `s_token`, `s_gold`, `stress_spread_mult` | spread **cheio** mediano de `s_token_bps` e de `spread_close_bps` (últimos 12 meses) e razão estresse contra calma |
| `kappa` | mediana de `1 - abs(e(t_e+6))/abs(e(t_e))` entre fins de semana com `abs(e(t_e)) >= 10` |
| `V0` | mediana, em US$, do `quote_volume` das duas velas em torno de `t_0` no PAXGUSDT da Binance (últimos 12 meses) |
| `etf_fee_bps_year`, `etf_rt` | 40 (SPDR GLD); mediana do spread cheio de `gldususd` em horário de bolsa |
| `storage_token_bps_year` | 0 hoje; o cenário C usa 20 como hipótese de diluição |
| `desk_cost_usd_year` | suposição de US$ 500 mil; sensibilidade de 100 mil a 2 milhões |
| `r_b`, `r_a` (cenário A) | da regressão agrupada de 6.12: `r_b = 1 - (max(b+d,0.01)/b)^(1/T)`, com `T` em anos; usar o IC de `d` como faixa |

**Cenários** (condicionais, não previsões):

| Cenário | Premissas |
| --- | --- |
| A. Continua como está | queda anual do repasse e do intercepto igual à tendência medida; liquidez crescendo no ritmo medido do PAXG; custos constantes |
| B. Infraestrutura avança | queda do repasse 2,5 vezes a do cenário A; taxas caindo 25% ao ano e spreads 15%; liquidez crescendo mais rápido |
| C. Estagna e estressa | sem queda do repasse; probabilidade e tamanho dos saltos de estresse maiores; emissor passa a cobrar 20 bps de armazenamento a partir do ano 3 |
| D. Adoção produtiva | colateral e rendimento ampliam a liquidez e cortam spreads; cascatas de liquidação em semanas de estresse criam erros de cauda maiores |

**Análises obrigatórias do simulador:** (i) `python simulador_cenarios.py --cal config/cal.json --out results/cenarios` (F10 e T5); (ii) **estresse inverso**: quanto a liquidez ou os erros teriam de crescer para a poça de lucro sustentar uma mesa profissional; (iii) `--sens`: sensibilidade a cada parâmetro em mais ou menos 50% (a maior alavanca na demonstração foi `kappa`, a fração do erro que converge). **Regras:** apresentar sempre como "se X, então Y"; mostrar a faixa de incerteza dos parâmetros; nunca citar um valor de cenário sem dizer a calibração usada; manter o aviso de que os parâmetros da demonstração são ilustrativos até a calibração com dados reais. Observação de modelo: `fee` e `etf_fee_bps_year` afetam o ponto de equilíbrio; a poça de arbitragem usa as taxas explícitas dos níveis de acesso.

---

## 7. Hipóteses, testes primários e múltiplos testes

**H0, tese central (regra de decisão, não teste estatístico).** A conclusão "a maturidade depende de infraestrutura, não de competição entre arbitradores" só é apresentada se valerem as três condições abaixo; os limiares são pré-registrados em `config/params.yaml`:

(a) a poça de lucro anual de A, B e C, com a calibração real e usando o limite superior para B, é menor que 10% do custo de uma mesa (US$ 500 mil; repetir com 100 mil e 2 milhões) em todos os níveis de acesso;
(b) no estresse inverso (6.19), a liquidez precisa crescer pelo menos 10 vezes ou os erros pelo menos 3 vezes para a poça sustentar uma mesa;
(c) M5 (6.12) não detecta que mais atividade de arbitragem leve a menos erro (`b >= 0` ou intervalo de 95% incluindo zero).

Se (a) ou (b) falharem: "a arbitragem pode sustentar capital profissional para {níveis de acesso}". Se só (c) falhar: "há indício de que a competição contribui". O slide 9 usa o texto que corresponder ao resultado.

| H | Afirmação | Estatística primária |
| --- | --- | --- |
| H1 | Hoje o ganho líquido de arbitragem é raro, pequeno e concentrado em fins de semana de salto grande; o acesso importa | Diferença das médias de `pnl` de A entre `big_gap` e `small_gap` (variante base), bootstrap |
| H2 | O risco de cauda do token é maior em estresse | Razão do p95 de `abs(e_w)` em estresse contra calma, bootstrap |
| H3 | O token compensa contra o ETF acima de N meses | Descritiva: ponto de equilíbrio com IC por bootstrap dos custos (sem p-valor) |
| H4 | A oferta responde ao desvio (o mecanismo de arbitragem existe) | `b_plus` de 6.9 (unilateral) |
| H5 | O repasse do estresse ao erro cai com o tempo (exploratório) | `d` da regressão agrupada de 6.12 (unilateral) |
| H6 | O perpétuo e o 1OZ reduziram o repasse (exploratório, poder baixo) | `d1` de 6.13 contra a distribuição de placebos |

Correção de Benjamini-Hochberg (nível 10%) sobre os p-valores de H1, H2, H4, H5 e H6. H3 e os cenários são descritivos: os cenários são análise de sensibilidade, não teste. Os critérios dos papéis (6.14 a 6.16) são regras de decisão pré-registradas. Dada a baixa potência de H5 e H6, a apresentação reporta tamanho de efeito e intervalo e usa "detectamos" e "não detectamos".

## 8. Figuras e tabelas

Estilo: fundo claro, ouro em âmbar, token em azul, violações em vermelho, fonte e período no rodapé, número de observações visível, 16:9, 200 dpi.

| ID | Conteúdo | Arquivo |
| --- | --- | --- |
| F1 | Distribuição do ganho líquido de A por regime e fração de fins de semana com ganho positivo | `results/F1_oportunidade_A.png` |
| F2 | Assimetria prêmio e desconto (histograma e meia-vida) e coeficientes `b_plus`, `b_minus` | `F2_assimetria_oferta.png` |
| F3 | Amadurecimento: repasse por semestre, regressão agrupada e desvio horário de dias úteis por trimestre, com intervalos | `F3_maturidade.png` |
| F4 | `abs(d)` do token e `abs(prem)` do ETF por semestre | `F4_token_vs_etf.png` |
| F5 | Eventos de infraestrutura: efeito estimado com IC e distribuição de placebos | `F5_eventos.png` |
| F6 | Fidelidade (beta, `TE_h`) e razão de captura em estresse | `F6_fidelidade.png` |
| F7 | Curvas de perda máxima de S0, S1 e S2 no teste | `F7_carteira.png` |
| F8 | Dispersão `m_w` contra `g_w` e métricas robustas de sinal | `F8_sinal.png` |
| F9 | Mapa de riscos: p95 e máximo do erro por regime, stablecoin, spread em estresse | `F9_riscos.png` |
| F10 | Cenários: erro mediano e p95, poça de arbitragem, equilíbrio contra o ETF e risco de cauda (saída do simulador) | `F10_cenarios.png` |
| F11 | Sensibilidade (tornado) e estresse inverso | `F11_sensibilidade.png` |
| T1 | Catálogo de oportunidades A a D (bruto, líquido, acerto, pior perda, capacidade, quem executa, cenários de custo) | `results/T1_oportunidades.csv` |
| T2 | Veredicto dos papéis (alcançado, parcial, ainda não) com o critério e o número | `results/T2_papeis.csv` |
| T3 | Mapa de riscos medidos | `results/T3_riscos.csv` |
| T4 | Custo do token contra o ETF e ponto de equilíbrio, por horizonte e cenário de custo | `results/T4_token_vs_etf.csv` |
| T5 | Cenários: saída anual do simulador | `results/T5_cenarios.csv` |

Todo número que aparece em slide vem de `results/RESULTS.md`, gerado por script. Proibido digitar número à mão no slide.

## 9. Pacotes de trabalho e briefs por agente

Interfaces: cada agente grava o arquivo indicado e nada além. Quem consome espera o arquivo em `data/interim` ou `data/panel`.

| Pacote | Entrada | Saída | Depende de | Tempo-alvo (Brasília) |
| --- | --- | --- | --- | --- |
| WP0 Orquestração | n/a | repo, `config/`, `events.csv`, merge e QA final | n/a | 11:30 |
| WP1 Cripto | 4.1, 4.2, 4.6 | `token_1h.parquet`, `perp_1h.parquet`, `funding.parquet`, `coinbase_*.parquet`, `fng.parquet` | WP0 | 12:30 |
| WP2 Ouro e ETF | 4.3, 4.4 | `gold_1h.parquet`, `etf_nav.parquet`, `gld_close.parquet` | WP0 | 12:30 |
| WP3 On-chain | 4.5 | `paxg_flows.parquet` | WP0 | 12:30 |
| WP4 Painéis | WP1, WP2, WP3 | `panel_weekends`, `panel_hourly`, `panel_daily` e testes | WP1, WP2, WP3 | 14:00 |
| WP5 Oportunidade A, maturidade, evento, sinal | `panel_weekends`, `panel_hourly` | F1, F3, F5, F8, parte de T1 e T2 | WP4 | 17:00 |
| WP6 Oportunidades B, C, D e oferta | `panel_hourly`, `panel_daily`, `paxg_flows` | F2, parte de T1 | WP4 | 17:00 |
| WP7 Papéis 1 e 2, ETF e carteira | `panel_daily`, `panel_hourly` | F4, F6, F7, parte de T2 | WP4 | 17:00 |
| WP8 Figuras e RESULTS.md | todas as saídas | figuras finais e `RESULTS.md` | WP5, WP6, WP7 | 18:30 |
| WP9 Slides | `RESULTS.md`, figuras | PDF de 10 slides e roteiro | WP8 (rascunho a partir de 15:00 com placeholders) | 20:30 |
| WP10 QA estatístico e red team | tudo | relatório de problemas e correções | contínuo | 19:00 |
| WP11 Riscos, custo contra o ETF e simulador | `panel_weekends`, `panel_hourly`, `gold_1h` (spreads de `gldususd`), resultados de WP5 a WP7 | T3, T4, T5, F9, F10, F11, `config/cal.json` | WP5, WP6, WP7 | 17:30 |

### Briefs (copiar para cada agente)

**WP1 Cripto.** Baixe, de 2020-08-28 a 2026-11-08 (XAUTUSDT só desde 2026-03-27), velas de 1 hora de PAXGUSDT, XAUTUSDT, BTCUSDT, ETHUSDT e USDCUSDT (arquivo da Binance; API para o mês corrente), velas de 1 hora e financiamento de XAUUSDT (API de futuros), e velas de 1 hora de PAXG-USD e USDT-USD (Coinbase). Baixe o Fear & Greed completo. Converta timestamps para UTC e padronize os esquemas de 5.1. Registre o primeiro mês disponível de cada par e todos os buracos. Entregue em `data/interim/`.

**WP2 Ouro e ETF.** Baixe XAUUSD e `gldususd` de 1 hora, bid e ask, de 2020-08-28 a 2026-11-08 com `dukascopy-node` em blocos paralelos; una em `gold_1h.parquet` (5.2). Baixe a planilha do SPDR Gold Shares (NAV, onças). Valide o ouro contra `gldususd` em horário de bolsa (correlação dos retornos horários acima de 0,95) e registre a diferença de nível. Entregue em `data/interim/`.

**WP3 On-chain.** Descubra o controlador de oferta do PAXG (`supplyController()`) e colete, via Etherscan com chave gratuita (ou RPC público), os `Transfer` de saída e de entrada do estoque da Paxos e os eventos `SupplyIncreased` e `SupplyDecreased`, com os topic0 da seção 4.5, dividindo janelas que devolvam 1000 registros. Converta valores para onças (campos em hexadecimal). Restrinja a análise de oferta a até 2026-06-24. Confira a soma líquida acumulada contra `totalSupply()` do contrato na Ethereum (`GET https://api.etherscan.io/v2/api?chainid=1&module=stats&action=tokensupply&contractaddress=0x45804880De22913dAFE09f4980848ECE6EcbAf78&apikey={KEY}`; tolerância de 1%). Entregue o parquet de 4.5.

**WP4 Painéis.** Construa `panel_weekends`, `panel_hourly` e `panel_daily` pelas definições de 6.1 a 6.5 e os esquemas de 5.3 a 5.5. Escreva os testes da seção 10. Reporte o número de fins de semana (esperado entre 340 e 370), a proporção de células faltantes, e a distribuição da hora UTC de reabertura (valores esperados: 21, 22 ou 23).

**WP5 Oportunidade A, maturidade, evento e sinal.** Implemente 6.7, 6.12 (M1, M2, M3 e tendência), 6.13 e 6.16, incluindo a variante de sensibilidade com entrada em t_0. Use as variantes pré-registradas como principais e grave todas em `results/variants.csv`. Produza F1, F3, F5 e F8, e as linhas de A em T1 e do degrau 3 em T2, usando as métricas robustas de 6.16.

**WP6 Oportunidades B, C, D e oferta.** Implemente 6.8, 6.9, 6.10 e 6.11. Produza F2 e as linhas de B, C e D em T1. Declare em cada tabela que B é limite superior.

**WP7 Papéis 1 e 2, ETF e carteira.** Implemente 6.12 (benchmark do ETF), 6.14, 6.15. Produza F4, F6, F7 e as linhas dos degraus 1, 2 e 4 em T2 (arquivo `T2_papeis.csv`).

**WP8 Figuras e RESULTS.md.** Padronize o estilo, confira unidades e rótulos, e gere `results/RESULTS.md` com cada número citado nos slides, o arquivo de origem e o tamanho da amostra.

**WP9 Slides.** Monte 10 slides (seção 11) a partir de `RESULTS.md` e das figuras. Comece cedo com placeholders e preencha à medida que os resultados chegam. Exporte para PDF. Aplique as regras de título condicional da seção 12.

**WP11 Riscos, custo contra o ETF e simulador.** (1) Calcule o mapa de riscos de 6.18 (T3, F9). (2) Calcule o custo de ida e volta do token (`2*fee + s_token + conv`) e do ETF (spread de `gldususd` mais 40 bps por ano pro rata), com três cenários de taxa (2, 5 e 10 bps) e IC por bootstrap, e o ponto de equilíbrio em meses (T4). Registre que o armazenamento da Paxos é zero hoje, com cláusula de diluição. (3) Estime os parâmetros de calibração da tabela de 6.19 e grave `config/cal.json`. (4) Rode `python simulador_cenarios.py --selftest`, depois `--cal config/cal.json --out results/cenarios`, depois `--sens` e o estresse inverso; gere T5, F10 e F11. (5) Escreva em `RESULTS.md` o aviso de que cenários são condicionais.

**WP10 QA e red team.** (1) Reproduza à mão três fins de semana de ponta a ponta e compare com o painel. (2) Verifique unidades, sinais (convenção de `e` e de `pnl`), fuso e ausência de look-ahead. (3) Verifique a aplicação do Benjamini-Hochberg. (4) Confira se todo número do PDF bate com `RESULTS.md`. (5) Procure afirmações no PDF que o dado não sustente e proponha a correção. (6) Verifique se os critérios dos degraus foram lidos de `params.yaml` sem alteração.

---

## 10. Testes automatizados (`tests/`)

- `test_tz`: índices em UTC, sem horas duplicadas.
- `test_units`: 1 oz = 31,1034768 g; PAXG, XAUT e XAUUSDT = 1 oz.
- `test_weekend_detection`: dados sintéticos com lacunas conhecidas retornam os `t_c` e `t_0` corretos, inclusive com mudança de horário de verão.
- `test_identity`: `e_w ≈ e_c + (m_w - g_w)` dentro de 1 bp em dados sintéticos com movimentos de até 0,5%.
- `test_no_lookahead`: o valor de `m_w` não muda se os dados depois de `t_0` forem apagados.
- `test_pnl_sign`: token caro com convergência dá `pnl` positivo; token barato com convergência também.
- `test_cs_spread`: o estimador de Corwin e Schultz recupera um spread conhecido em dados sintéticos (tolerância de 30%).
- `test_ar1_recovery`: AR(1) com `phi = 0,9` devolve meia-vida de 6,6 horas (±10%).
- `test_supply_regression`: oferta sintética que reage ao excesso com `b` conhecido é recuperada.
- `test_topic0`: os hashes da seção 4.5 batem com keccak256 das assinaturas.

---

## 11. Plano de construção dos slides (10)

O limite informado no material de abertura é de 10 slides. A história tem três tempos: **hoje**, **como evolui** e **e se continuar**. Cada título é uma conclusão; os valores entre chaves vêm de `RESULTS.md`. A estrutura cobre os cinco critérios da banca: relevância (1 e 2), adequação metodológica (3), qualidade da solução e do material (4 a 8), criatividade (o conjunto) e implicações (9 e 10).

| Nº | Título (modelo) | Visual | Números |
| --- | --- | --- | --- |
| 1 | O ouro tokenizado cumpre a promessa de valer ouro? E amadurece por competição ou por infraestrutura? | Título, equipe, problema, pergunta e a frase do jurado (texto canônico) | n/a |
| 2 | No fim de semana, o token forma preço sozinho, e isso tem valor e risco | Março de 2026 (token contra ouro); mercado; uso como colateral | `events.csv`; CoinGecko; Tiger Research; RedStone |
| 3 | Medimos o erro do token na reabertura, o custo e o risco, com dados gratuitos | Esquema sexta, fim de semana, reabertura; fontes; cenários de custo | seção 6 |
| 4 | Hoje: compensa contra o ETF a partir de {N} meses, e a arbitragem rende {y} bps em {x}% dos fins de semana | T4 e T1 | `T4_token_vs_etf.csv`, `T1_oportunidades.csv` |
| 5 | Hoje: o maior risco é {risco}, com erro de cauda de {p95} bps em estresse | F9 | `T3_riscos.csv` |
| 6 | Quem mantém o preço ganha pouco: a oferta {responde / não responde} e a poça é de US$ {z} mil por ano | F2 e F1 | `F2`, `F1` |
| 7 | O erro {caiu / não mostrou queda} de {a} para {b}, e os eventos de infraestrutura {pesaram / não tiveram efeito detectável} | F3 e F5 | `F3`, `F5` |
| 8 | Se continuar assim, em {ano} o equilíbrio será de {n} meses e a poça de US$ {z}; em outros cenários, {resumo} | F10 e F11 | `T5_cenarios.csv`, `F10`, `F11` |
| 9 | O que isso implica: o token já é {papéis}; a regra H0 {foi / não foi} cumprida, então a maturidade tende a vir de {infraestrutura e adoção / também da competição} | T2, resultado de H0 e implicações para o Brasil como argumento | `T2_papeis.csv`, `H0_decisao.csv` |
| 10 | O que aprendemos, o que não sabemos e os próximos passos | Limitações e próximos passos | n/a |

**Defesa oral de 5 minutos:** slides 1, 4, 5, 8 e 9.

**Dependência dos slides e o que fazer se faltar (a versão garantida):**

| Slide | Depende de | Se faltar |
| --- | --- | --- |
| 1, 2, 3, 10 | nada | n/a |
| 4 | T4 e T1 (MVP) | n/a |
| 5 | T3 (MVP) | usar só os riscos documentais |
| 6 | poça de T1 (MVP); F2 (completo) | sem F2, mostrar só a poça e declarar que a resposta da oferta não foi medida |
| 7 | F3 (MVP); F5 (completo) | sem F5, omitir os eventos e declarar |
| 8 | simulador calibrado (MVP) | se a calibração falhar, não apresentar valores de cenário; mostrar só a lógica e a sensibilidade |
| 9 | H0 (T1, estresse inverso, M5); T2 (completo) | sem T2, papéis em texto condicional; sem M5, a condição (c) é declarada como não testada |

**Construção:** gráficos com matplotlib em PNG 16:9; montar com `python-pptx` (ou Beamer); converter para PDF; abrir o PDF e conferir que nenhum texto está cortado, que há no máximo 10 páginas e que cada slide tem uma mensagem. Dar crédito aos mentores, se houver mentoria (contato: digitalfinance@fgv.br).

## 12. Títulos condicionais (regra de honestidade)

Resultado não significativo nunca vira "não houve efeito": vira "não detectamos", porque o poder é baixo (seção 15). Os números de cenário são sempre condicionais.

| Slide | Se confirmar | Se contrariar ou for inconclusivo |
| --- | --- | --- |
| 4 | "Compensa contra o ETF a partir de {N} meses" | "Contra o ETF, o token só compensa em horizontes acima de {N} meses, e em estresse não compensa" |
| 5 | "O maior risco é {risco}" | "Os riscos medidos são pequenos em calma e relevantes em estresse" |
| 6 | "A oferta responde ao desvio" | "Não detectamos resposta da oferta, o que sugere que o preço é mantido por poucos agentes" |
| 7 | "O erro caiu de {a} para {b}" | "Não detectamos queda do erro: o mercado cresceu, e a maturidade não ficou demonstrada" |
| 8 | "Em {cenário}, o equilíbrio cai para {n} meses" | "Em nenhum cenário razoável a arbitragem sustenta uma mesa profissional" |
| 9 | "A regra H0 foi cumprida: a maturidade tende a vir de infraestrutura e adoção" | "A regra H0 não foi cumprida: {texto de H0 correspondente}" |

## 13. Caso ao vivo (opcional, só se tudo estiver pronto até as 19h)

Hoje é domingo, então há uma reabertura ao vivo. Gravar de 20:30 UTC a 01:00 UTC do dia 09, a cada 5 segundos, `PAXGUSDT` e `XAUUSDT` (`GET /api/v3/ticker/bookTicker` e `GET /fapi/v1/ticker/bookTicker`). Depois, baixar os mesmos minutos do ouro à vista da Dukascopy (quando disponíveis) e traçar token contra ouro em torno da reabertura. Entra como slide extra de "o caso de hoje" apenas se os dados chegarem a tempo; nunca atrasar a entrega por isso.

---

## 14. Pendências a verificar na execução

| Item | Como verificar | Se falhar |
| --- | --- | --- |
| Download da Dukascopy | Rodar um mês de teste com `dukascopy-node`; instalar o Chromium da ferramenta | Plano B da seção 4.7; declarar o nível de resolução |
| Início de cada par na Binance | Listar o diretório do S3 (PAXGUSDT deve começar em 2020-08-28) | Começar na primeira data disponível |
| Unidade de tempo dos arquivos | Magnitude do `open_time` | Converter |
| XAUUSDT na API de futuros | Chamar o endpoint de klines | Cortar F5 (evento do perpétuo) e a oportunidade D |
| Coinbase com PAXG-USD e USDT-USD, e candles vazios | Chamar `candles`; lembrar que não há dado nos intervalos sem negócios | Usar `1/USDCUSDT`; limitar C a horas em que os dois lados têm negócios |
| Carteiras de estoque da Paxos e `supplyController()` | `eth_call` e inspeção no Etherscan | Usar `SupplyIncreased` e `SupplyDecreased` semanais, declarando que medem reposição de estoque |
| Colunas do XLSX do SPDR | Abrir e inspecionar | Calcular onças por cota por `NAV / mid_Dukascopy(15h Londres)` |
| Tabela de taxas da Paxos (isenção de criação até 2026-09-30 ou 2027-01-01 conforme a versão; resgate de 0,125% a cerca de 1% conforme o tamanho; armazenamento hoje zero, com cláusula de diluição nos termos) | Ler a página oficial | Cenários de taxa de 6.8 cobrem a incerteza |
| Data de lançamento dos futuros de PAXG na Deribit | Anúncio da Deribit | Omitir o segundo evento |
| Fórmula do estimador de spread | Artigo de Corwin e Schultz (2012) | Usar o estimador de Roll |
| Limite de 10 slides, formulário de envio e regras de autoria | Material de abertura e e-mail da organização (digitalfinance@fgv.br) | Seguir a regra mais restritiva |

**Item que exige decisão humana:** o plano usa agentes de IA para executar. O material consultado não traz regra sobre uso de IA, mas vale confirmar com a organização antes da entrega e citar as ferramentas usadas.

## 15. Validação desta especificação

### 15.1 O que foi checado e o resultado

| Item | Resultado |
| --- | --- |
| Tema livre e adequação ao desafio | O material de abertura, segundo o repositório público de outra equipe, deixa o tema livre e lista tokenização de ativos do mundo real entre as sugestões. Não consegui abrir o PDF original; confirmar |
| Critérios da banca | Relevância do problema, adequação metodológica, qualidade da solução e do material, criatividade e análise das implicações. Cobertos pelos 10 slides |
| Limite de slides | Até 10 (o plano anterior tinha 12): corrigido |
| Binance PAXGUSDT | Começa em 2020-08-28, não em 2019: janela corrigida |
| Binance XAUTUSDT | Só desde 2026-03-27: robustez recente apenas |
| Dukascopy | `xauusd` desde 1999 e `gldususd` disponíveis; ferramenta exige Node 20, pode precisar de Chromium e pode receber erro 403: risco declarado e plano B |
| Etherscan `getLogs` | Parâmetros conferidos na documentação oficial; campos de resposta em hexadecimal |
| Coinbase candles | No máximo 300 velas por chamada, sem dado em intervalos sem negócios |
| Paxos, oferta on-chain | A Paxos cunha para estoque e transfere aos clientes; o desenho anterior (eventos de cunhagem como pegada) estava errado: corrigido para fluxos do estoque, com janela até 2026-06-24 por causa da Solana |
| Taxas | Binance spot 10 bps (7,5 com BNB); Paxos resgate de cerca de 0,125% a cerca de 1% conforme o tamanho: parâmetros corrigidos |

### 15.2 Poder estatístico (simulação)

Simulação com parâmetros de partida declarados: salto do ouro com cauda pesada e desvio-padrão de 30 bps, ruído do token com cauda pesada e escala de 10 bps, repasse `b` e intercepto `a` como indicados. **Os números ilustram o poder, não são resultados.**

| Teste | Cenário | Poder |
| --- | --- | --- |
| Mann-Kendall sobre `b_s` (14 semestres, 26 fins de semana cada) | sem tendência | 2% de rejeição |
| | queda de 0,30 para 0,25 | 10% |
| | queda de 0,30 para 0,20 | 20% |
| | queda de 0,30 para 0,10 | 62% |
| Regressão agrupada com tempo contínuo | sem tendência | 3% |
| | queda de 0,30 para 0,25 | 12% |
| | queda de 0,30 para 0,20 | 33% |
| | queda de 0,30 para 0,10 | 80% |
| Contraste antes e depois, 290 contra 44 fins de semana | queda do repasse de 0,10 | 38% |
| | queda de 0,20 | 76% |
| Contraste com 14 fins de semana depois (1OZ) | queda de 0,10 | 17% |
| | queda de 0,20 | 39% |

**Consequências:** (1) o teste por semestre foi rebaixado a descritivo e o teste principal passou a ser a regressão agrupada; (2) a maturidade ganha um segundo indicador com muito mais dados (desvio horário em dias úteis); (3) o efeito dos eventos é reportado com intervalo e a linguagem é "detectamos" ou "não detectamos".

**Sensibilidade da oportunidade A** (erro de reabertura com mediana de cerca de 19 bps, hipótese ilustrativa; `kappa` é a fração do erro que converge, `C` é o custo de ida e volta): com `kappa` = 0,5, o ganho líquido positivo ocorre em 14% dos fins de semana com `C` = 15 bps, 2% com `C` = 25 e 0,4% com `C` = 35. Com `kappa` = 0,7, ocorre em 38%, 7% e 2%. O custo de corretora decide quase tudo.

### 15.3 Correções aplicadas nesta validação

1. Slides: de 12 para 10.
2. Janela de dados: de 2019 para 2020-08-28.
3. XAUT na Binance: de série longa para robustez de 2026.
4. Oferta on-chain: de eventos de cunhagem para fluxos do estoque da Paxos, até 2026-06-24.
5. Oportunidade A: entrada uma hora depois da reabertura, com a entrada no primeiro instante como sensibilidade.
6. Evento do 1OZ recuperado: a data basta, não é preciso dado da CME; dois eventos com variáveis separadas.
7. Critério do degrau 3 endurecido.
8. Teste de maturidade trocado por regressão agrupada e acrescentado o indicador horário de dias úteis.
9. Preço do ETF passa a vir da Dukascopy (`gldususd`), com a mesma fonte e o mesmo relógio do ouro.
10. Linguagem dos resultados não significativos.

### 15.4 Pontos frágeis que continuam

- O ouro à vista da Dukascopy e o perpétuo da Binance não são o mercado regulado.
- Os primeiros anos do PAXG têm pouca liquidez e preços possivelmente defasados.
- O preço da Paxos para criar e resgatar não é observado.
- A maturidade e os eventos têm poder baixo a moderado, e as conclusões são exploratórias.
- Não há componente de aprendizado de máquina, que apareceu em dois dos três trabalhos premiados de 2025; um monitor simples de previsão do erro de reabertura é a extensão natural se houver tempo.
- Não consegui confirmar o conteúdo do PDF de abertura nem se há regra sobre o uso de IA.

### 15.5 Validação do simulador (entregue com o plano)

Dez testes automáticos passam (`python simulador_cenarios.py --selftest`): poça estável sem tendência; taxa menor aumenta a poça; repasse maior aumenta a poça e o erro; poça linear na liquidez; sem erro não há oportunidade; erro de cauda cai com a maturidade; estabilidade entre sementes; equilíbrio infinito quando o emissor passa a cobrar mais que o ETF; acesso institucional rende mais que o padrão; estresse inverso atinge o alvo. Com os parâmetros ilustrativos, a demonstração mostrou: o erro de cauda cai nos cenários A, B e D e fica em torno de 50 bps no C; o equilíbrio contra o ETF fica em cerca de 4,5 meses no A, cai para 1,6 mês no B, dobra para 9 meses no C quando o emissor cobra 20 bps de armazenamento, e a poça de arbitragem fica na casa de centenas a poucos milhares de dólares por ano, longe de sustentar uma mesa (estresse inverso: liquidez 956 vezes maior ou erros 20 vezes maiores). **Esses números dependem dos parâmetros ilustrativos e devem ser refeitos com a calibração dos dados reais.** A maior alavanca na análise de sensibilidade foi a fração do erro que converge (`kappa`).

### 15.6 Avaliação das estratégias e clareza

A comparação das estratégias discutidas (matriz de notas, com a ressalva de que são julgamentos) está em `projeto_humanos.md`, seção 11. A checagem de clareza encontrou três problemas, já corrigidos: o problema não estava explícito, a tese afirmava a conclusão antes da evidência e a afirmação central (a competição não traz maturidade) não tinha teste direto. Agora há texto canônico, regra de decisão H0 com limiares pré-registrados e o teste M5.
