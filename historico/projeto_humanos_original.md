# O preço da promessa: âncora, arbitragem e valor no ouro tokenizado

Guia do projeto para a equipe. 7º Desafio de Dados (Datathon) de Moedas Digitais da FGV EESP. A história tem três tempos: **hoje** (oportunidades e riscos), **como evolui** (arbitragem e amadurecimento) e **e se continuar** (cenários simulados). **Entrega hoje, domingo 08/11/2026, até 23h59 (Brasília), em PDF de no máximo 10 slides.** Versão com dados 100% gratuitos, feita para ser executada em um dia por vários agentes de IA. A especificação técnica está em `projeto_agentes.md`, e o simulador de cenários em `simulador_cenarios.py`.

---

## 1. O problema, a pergunta e a tese

**Problema.** Tokens de ativos reais prometem duas coisas: preço fiel ao ativo e negociação 24 horas por dia. Ninguém mediu direito se essa promessa é cumprida, a que custo e com que riscos, nem se o mercado vai melhorar sozinho. Investidores, emissores, bolsas e reguladores decidem hoje por narrativa.

**Pergunta central.** O ouro tokenizado, o caso mais líquido de ativo real tokenizado, cumpre a promessa de valer o ouro? E, se ele melhora com o tempo, é porque os arbitradores competem ou porque a infraestrutura avança?

**Hipótese, com regra de decisão.** O custo de manter o token no preço é moderado em dias normais e tem risco de cauda em fins de semana e em estresse; o que os arbitradores ganham para mantê-lo no preço é pequeno demais para atrair capital profissional; logo, a maturidade depende de infraestrutura e adoção, não de competição. Se os dados mostrarem o contrário (poça de lucro grande, resposta forte da oferta, melhora que acompanha a atividade de arbitragem), a conclusão se inverte e o trabalho diz isso.

**Em uma frase para o jurado:** *"Medimos se o ouro tokenizado cumpre a promessa de valer ouro, quanto isso custa e que riscos tem, e simulamos se ele amadurece por competição ou por infraestrutura."*

**Decisão que o trabalho informa:** o investidor (token ou ETF, e a partir de quanto tempo), o emissor e a bolsa (qual custo reduzir) e o regulador (o que a infraestrutura 24/7 precisa entregar).

Três perguntas, uma por tempo:

| Tempo | Pergunta | O que entregamos |
| --- | --- | --- |
| **Hoje** | Que oportunidades e que riscos o ouro tokenizado tem? | Custo contra o ETF e ponto de equilíbrio em meses; catálogo de arbitragem com ganho líquido e quem executa; mapa de riscos medidos |
| **Como evolui** | A arbitragem o mantém no preço, e ele está amadurecendo? | Resposta da oferta; tendência do erro do token comparada com a de um ETF; efeito de eventos de infraestrutura; teste de se mais arbitragem leva a menos erro |
| **E se continuar** | O que acontece com oportunidades, custos e riscos nos próximos anos? | Simulação de quatro cenários, com sensibilidade e estresse inverso |

**Regra de decisão (definida antes dos dados).** A conclusão "infraestrutura, não competição" só é apresentada se as três condições valerem: (a) a poça de lucro anual da arbitragem (A, B e C) fica abaixo de 10% do custo de uma mesa profissional (suposto em US$ 500 mil, testado de 100 mil a 2 milhões) em todos os níveis de acesso; (b) no estresse inverso, a liquidez teria de crescer pelo menos 10 vezes ou os erros pelo menos 3 vezes para sustentar uma mesa; (c) mais atividade de arbitragem em um trimestre não vem seguida de menos erro no trimestre seguinte. Se (a) ou (b) falharem, a conclusão vira "a arbitragem pode sustentar capital profissional para quem tem acesso". Se só (c) falhar, vira "há indício de que a competição contribui".

O fio condutor: **promessa de preço → arbitragem a cumpre → o quanto ela rende e o quanto o preço erra medem a maturidade → a simulação mostra o que isso implica.**

---

## 2. A ideia, de forma intuitiva

Imagine que um token diz valer uma onça de ouro. Se ele sobe 3% no sábado e o ouro só abre 2% acima na segunda, quem comprou o token no sábado pagou caro. Alguém que vê essa diferença pode vender o token e comprar ouro na reabertura, lucrando quando os preços se encontram. Esse alguém é o arbitrador, e o que ele ganha é o preço de manter a promessa.

Dois fatos tornam o ouro o melhor laboratório:

1. **O fim de semana é o ponto de maior atrito.** A CME fecha na sexta às 17h de Nova York e reabre no domingo às 18h. Nesse intervalo, o token é quase o único preço de ouro que existe. Em quatro fins de semana de 2026 o token se mexeu mais do que o ouro realizou na segunda: na de 23/02, o token subiu 3,5% e o ouro abriu 2,85% acima; na de 16/03, o token caiu 2,64% e o ouro 1,18%; na de 23/03, -3,72% contra -3,03%. Em 02/03, o token chegou a mais de US$ 5.400 no sábado e esfriou no domingo, e o ouro à vista alcançou o pico um dia depois ([CoinGecko](https://www.coingecko.com/learn/tokenized-gold-price-signal)).
2. **Fontes populares discordam sobre o desvio normal do token.** Uma diz que ele fica com desconto de 0,5% a 2,5%, outra que teve prêmio de 1,5% a 2% por meses em 2025 ([Gate](https://www.gate.com/crypto-wiki/article/paxg-is-trading-at-a-premium-to-gold)), outra que fica dentro de meio por cento ([OneBullEx](https://www.onebullex.com/explore/paxg-vs-gold-price-basis-and-liquidity)). Quase todas comparam o token com o último preço à vista, que no fim de semana está defasado. Medir isso direito, na hora certa, já é uma contribuição.

---

## 3. O que será mostrado

### 3.1 Hoje: as oportunidades

| Oportunidade | O que é | Como se mede |
| --- | --- | --- |
| **Ouro 24/7** | O token negocia quando as bolsas fecham e forma preço sozinho no fim de semana | Erro do token na reabertura; fração dos fins de semana com erro abaixo de 25 bps |
| **Custo contra o ETF** | O token não cobra armazenamento hoje (a Paxos reserva o direito de cobrar no futuro, por diluição); o ETF cobra 19 a 40 bps por ano. Em troca, o token tem custo maior de entrada e saída | Ponto de equilíbrio em meses, com intervalo (por exemplo, 25 bps de ida e volta no token contra 3 bps no ETF dá cerca de 6 meses) |
| **Arbitragem A** | Convergência na reabertura: vender o caro e comprar o barato, uma hora depois do mercado abrir | Ganho bruto e líquido; capacidade; quem executa |
| **Arbitragem B** | Mercado primário da Paxos: criar tokens quando há prêmio (criação gratuita enquanto durar a isenção) e resgatar quando há desconto | Preço contra taxas (limite superior); só clientes verificados |
| **Arbitragem C** | O mesmo token com preços diferentes na Binance e na Coinbase | Dispersão líquida de custos |
| **Arbitragem D** | Comprar o token e vender o perpétuo de ouro (XAUUSDT, desde 05/01/2026), recebendo o financiamento | Carrego líquido, com risco de base |
| **Usos produtivos** | Colateral em empréstimos e ouro que rende (PAXGy) | Contexto: menos de 2% do mercado é usado como colateral ([RedStone](https://cointelegraph.com/news/tokenized-gold-defi-stress-test-collateral-adoption-redstone)) |

Cada arbitragem é medida **bruta e líquida** de custos, com a **capacidade** e quem executa, em três cenários de custo.

### 3.2 Hoje: os riscos

| Risco | O que se mede |
| --- | --- |
| Cauda do erro no fim de semana | Percentil 95 e pior fim de semana do erro, por regime; fração com erro acima de 50 bps |
| Stablecoin | Maior desvio do USDT contra o dólar, com a data |
| Fragmentação | Dispersão entre corretoras |
| Liquidez em estresse | Spread e volume do token em semanas de estresse contra calma |
| Emissor e resgate | Armazenamento zero hoje, com cláusula de diluição; resgate físico a partir de cerca de 430 tokens; taxas de resgate de 0,125% a cerca de 1% |
| Colateral em DeFi | Menos de 2% do mercado; liquidações de XAUT na Aave em 23/03/2026 correram sem interrupção |
| Concentração | PAXG e XAUT somam cerca de 97% do ouro tokenizado |

### 3.3 Como evolui: arbitragem e amadurecimento

Oportunidade de arbitragem se autodestrói: cada desvio explorado estreita a banda para o próximo. Por isso a trajetória dela é a medida da maturidade. Medimos:

1. **Se a oferta responde.** Quando o desvio passa da banda, os tokens saem ou entram no estoque da Paxos? (O estoque é medido por transferências, porque a Paxos cunha para um estoque e o entrega aos clientes.)
2. **O repasse do estresse ao erro.** Em cada fim de semana, quanto de um choque do ouro vira erro do token, ao longo de agosto de 2020 a 2026.
3. **O desvio em dias úteis,** que tem muito mais dados que o fim de semana e por isso é o indicador mais confiável da tendência.
4. **Eventos de infraestrutura** de data conhecida: o perpétuo de ouro na Binance (05/01/2026) e o contrato 1OZ da CME em 24/7 (24/07/2026). Não precisamos de dados da CME: usamos só a data. Com poucos fins de semana depois de cada evento, a análise é **exploratória**.

Cada medida é comparada com o mesmo indicador do **ETF SPDR Gold Shares**, o mercado maduro, e comparamos sobretudo como cada um **muda ao longo do tempo**.

**Aviso de poder estatístico (simulado):** com cerca de 330 fins de semana, uma queda forte do repasse (de 0,30 para 0,10) é detectada com cerca de 80% de chance, mas uma queda moderada (de 0,30 para 0,20) só com cerca de 33%. Por isso o trabalho reporta o tamanho do efeito com intervalo e usa "detectamos" e "não detectamos", nunca "não houve efeito".

### 3.4 E se continuar: os cenários simulados

O simulador (`simulador_cenarios.py`) gera, fim de semana a fim de semana, o salto do ouro e o erro do token, com os parâmetros estimados dos dados, e mede a cada ano: o erro mediano e de cauda, quantos fins de semana dão ganho líquido de arbitragem e quanto isso soma por ano (a "poça de lucro"), o ponto de equilíbrio contra o ETF e o risco de cauda.

| Cenário | O que supõe |
| --- | --- |
| **A. Continua como está** | A tendência medida continua, com os mesmos custos |
| **B. Infraestrutura avança** | Perna 24/7 regulada, taxas e spreads em queda, mais liquidez |
| **C. Estagna e estressa** | Sem melhoria, mais semanas de estresse, e o emissor passa a cobrar armazenamento por diluição |
| **D. Adoção produtiva** | Colateral e rendimento ampliam a liquidez, mas cascatas de liquidação criam erros de cauda |

Duas análises acompanham: o **estresse inverso** (quanto a liquidez ou os erros teriam de crescer para a arbitragem sustentar uma mesa profissional?) e a **sensibilidade** (qual suposição mais muda o resultado?).

**O que a demonstração do simulador mostrou, com parâmetros apenas ilustrativos (arquivo `cenarios_demo.png`):**
- O ponto de equilíbrio contra o ETF fica em cerca de 4,5 meses no cenário A, cai para 1,6 mês no B e dobra para 9 meses no C, quando o emissor passa a cobrar 20 bps de armazenamento.
- O erro de cauda cai nos cenários A, B e D e fica em torno de 50 bps no C; a fração de fins de semana com erro acima de 50 bps vai de cerca de 1,4% para 0,6% no A e fica em cerca de 5% no C.
- A poça de lucro da arbitragem fica entre centenas e poucos milhares de dólares por ano, e só no D chega a cerca de dez mil, porque as cascatas criam erros grandes. É muito menos que o custo de uma mesa profissional (suposto em US$ 500 mil por ano). No estresse inverso, a liquidez teria de ser cerca de 950 vezes maior, ou os erros 20 vezes maiores.
- A maior alavanca é a fração do erro que converge dentro do horizonte, o que diz onde medir com mais cuidado.
- **Implicação, condicional a esses parâmetros:** a competição entre arbitradores, sozinha, tende a não trazer a maturidade; ela vem de infraestrutura (custos menores, perna 24/7 regulada) e de adoção. Os números reais virão da calibração com os dados.

**Regras de leitura:** cenários são "se X, então Y", não previsões; a calibração e a faixa de incerteza dos parâmetros aparecem junto de cada resultado.

### 3.5 Os papéis do token, hoje e amanhã

| Papel | Critério (definido antes dos dados) | Hoje |
| --- | --- | --- |
| Veículo de negociação 24/7 | Spread efetivo mediano até 10 bps e volume relevante em fins de semana | A medir |
| Proxy de reserva de valor | Beta contra o ouro entre 0,95 e 1,05; razão de captura em estresse entre 0,8 e 1,2; erro de fidelidade de 21 dias até 100 bps | A medir |
| Sinal de preço de fim de semana | Erro absoluto mediano de previsão até 60% do de prever zero; correlação de postos de pelo menos 0,80; acerto de direção de pelo menos 70% | A medir |
| Colateral e ativo produtivo | Não medido; depende de adoção e de resiliência em liquidações | Contexto: menos de 2% do mercado |

O veredicto por papel é "alcançado", "parcial" ou "ainda não", e a simulação mostra o que mudaria o resultado em cada cenário.

---

## 4. O que o trabalho vai mostrar

Um slide-resposta, preenchido com os números dos dados:

> **Hoje**, ter ouro em token compensa contra o ETF a partir de **N meses**, e a arbitragem rende **Y bps líquidos** em **X% dos fins de semana**, com capacidade pequena e só para quem tem acesso. Os maiores riscos são **R**, com erro de cauda de **P bps** em estresse. **Na trajetória**, o erro do token **[caiu / não mostrou queda]** de **A para B**. **Se continuar como está**, em **ANO** o equilíbrio será de **M meses**; **se a infraestrutura avançar**, de **M2**; **se estagnar e estressar**, de **M3**. A arbitragem sozinha não sustenta uma mesa profissional: a maturidade tende a vir de **infraestrutura e adoção**.

A frase final sobre competição ou infraestrutura só entra se a regra de decisão da seção 1 for cumprida. **Se o resultado for contrário ao esperado, a conclusão muda de manchete, não de estrutura:**

| Se o dado mostrar | A manchete vira |
| --- | --- |
| Equilíbrio curto e erro de cauda pequeno | O token já é uma alternativa ao ETF para horizontes médios, e os cenários mostram como melhora |
| Equilíbrio longo ou erro de cauda grande em estresse | O token ainda custa caro e falha quando mais se precisa; a simulação mostra o que precisaria mudar |
| Oferta que responde e erro em queda | O mecanismo de arbitragem existe e o mercado amadureceu |
| Sem tendência | O mercado cresceu, mas não amadureceu |

---

## 5. Dados 100% gratuitos

| Dado | Fonte | Como obter | Uso |
| --- | --- | --- | --- |
| PAXG, BTC, ETH, velas de 1 hora | Arquivo público da Binance (data.binance.vision) | Arquivos zip mensais por par | Desvio, maturidade, carteira. O PAXG/USDT começa em 28/08/2020; o XAUT na Binance só desde 27/03/2026 (robustez recente) |
| XAUUSDT (perpétuo de ouro) e financiamento | Binance, API pública de futuros | Chamadas sem chave | Oportunidade D, evento de infraestrutura, referência de fim de semana |
| PAXG em dólar | Coinbase, API pública | Velas de 1 hora, 300 por chamada | Dispersão (C), efeito da stablecoin |
| Ouro à vista, velas de 1 hora com bid e ask | Dukascopy | Ferramenta gratuita `dukascopy-node` | Referência de ouro, reabertura, erro e salto |
| NAV e onças do ETF SPDR Gold Shares | Arquivo oficial do fundo (XLSX) | Download na página do fundo | Benchmark de maturidade |
| Preço da cota do ETF | Dukascopy (`gldususd`), mesma fonte do ouro; alternativa Yahoo Finance ou Stooq | Velas de 1 hora | Prêmio do ETF |
| Criação e resgate de PAXG | Transferências do estoque da Paxos na Ethereum (a Paxos cunha para estoque e transfere aos clientes) | API do Etherscan com chave gratuita | Resposta da oferta (oportunidade B), até 24/06/2026, antes da Solana |
| Estresse cripto | Crypto Fear & Greed Index | API sem chave | Regimes |
| Taxas da Paxos | Página oficial de taxas | Leitura manual | Bandas do mercado primário |

**O que saiu por não haver dado gratuito:** o Bloomberg (curva do GC, carrego, LBMA), o contrato 1OZ da CME (o experimento de julho), o futuro GLD da B3 e a rota brasileira. O ângulo brasileiro passa a ser argumento, não medição.

---

## 6. O que o trabalho não afirma

- Não afirma que o ouro é reserva de valor por décadas. O token só existe desde 2019, então medimos proteção e fidelidade no período.
- Não afirma causalidade no experimento da Binance. É um evento de data conhecida, com um 2026 muito volátil por cima.
- Não afirma que dá para ganhar muito arbitrando. O achado provável é o contrário, e ele sustenta a tese.
- Não prevê o futuro. Os cenários dizem "se X, então Y".

---

## 7. Plano de hoje, hora a hora (Brasília)

Vários agentes em paralelo. Os blocos estão na especificação técnica, com o brief de cada agente.

| Horário | Bloco | Resultado esperado |
| --- | --- | --- |
| 11h30 a 12h30 | **Dados:** quatro agentes baixam, em paralelo, cripto, ouro, on-chain e ETF; um cria o repositório e a configuração | Arquivos brutos completos |
| 12h30 a 14h00 | **Painéis e testes:** painel semanal de reabertura, painel horário de dia útil, painel diário | Painéis validados |
| 14h00 | **Ponto de decisão 1:** painéis prontos? Se não, aplicar a ordem de corte | |
| 14h00 a 17h00 | **Análises em paralelo:** oportunidade A, maturidade e eventos; oportunidades B, C e D; papéis; mapa de riscos; custo contra o ETF; calibração do simulador | Resultados e figuras brutas |
| 17h00 | **Ponto de decisão 2:** resultados do núcleo congelados | |
| 17h00 a 19h30 | **Rodar o simulador com a calibração real (cenários, estresse inverso, sensibilidade); figuras finais; revisão estatística; slides com números reais** | PDF preliminar |
| 19h00 a 20h00 | **Opcional, ao vivo:** gravar a reabertura de domingo à noite (token contra ouro) para um slide "o caso de hoje" | |
| 19h30 a 21h00 | **Revisão por alguém de fora, ensaio, exportar PDF e scripts em .txt** | Arquivos finais |
| 21h00 a 22h00 | **Submissão** | Entregue com 2 horas de folga |

**Regra:** nenhuma análise nova depois das 19h. Se algo atrasar, cortar nesta ordem: carteira e oportunidade D, sinal de fim de semana, benchmark do ETF, oportunidade C, eventos de infraestrutura. O núcleo que nunca sai: reabertura (A), oportunidade B por preço, custo contra o ETF, mapa de riscos, amadurecimento e o simulador calibrado.

**Versão garantida.** Mesmo se a resposta da oferta, os eventos de infraestrutura ou os papéis não ficarem prontos, o PDF fica completo: os slides 4, 5, 7 e 8 dependem só do núcleo; o slide 6 mostra a poça de lucro e declara que a resposta da oferta não foi medida; o slide 7 omite os eventos; o slide 9 traz os papéis em texto condicional. Nenhum slide fica vazio.

---

## 8. Roteiro dos slides (10)

O material de abertura limita o PDF a 10 slides (segundo o repositório público de outra equipe; confirmar no formulário de envio). A banca avalia relevância do problema, adequação metodológica, qualidade da solução e do material, criatividade e análise das implicações. Princípios: título que é a conclusão, um gráfico por slide, números com unidade e fonte, nada de texto para ler em voz alta.

1. **Título, problema, pergunta e a frase do jurado.** *Fala (45 s):* "Tokens de ativos reais prometem preço fiel e negociação 24 horas por dia, e ninguém mediu direito se isso é cumprido. Medimos se o ouro tokenizado cumpre a promessa de valer ouro, quanto custa e que riscos tem, e simulamos se ele amadurece por competição ou por infraestrutura."
2. **Por que importa.** O fim de semana de 23/03/2026: o token caiu 3,7% e o ouro à vista 3,0%; mercado de US$ 178 bilhões negociados em 2025, atrás só do ETF GLD (Tiger Research); menos de 2% usado como colateral. *Fala (40 s).*
3. **Como medimos.** Erro de reabertura em um desenho simples (sexta, fim de semana, reabertura); custos; risco; dados gratuitos. *Fala (40 s):* adequação metodológica.
4. **Hoje: oportunidades.** Ponto de equilíbrio contra o ETF e catálogo de arbitragem com ganho líquido e quem executa. *Fala (60 s):* "Compensa a partir de N meses, e a arbitragem rende pouco e só com acesso."
5. **Hoje: riscos.** Mapa de riscos medidos: cauda do erro em estresse, stablecoin, liquidez, emissor, colateral. *Fala (50 s).*
6. **Quem mantém o preço.** A oferta responde ao desvio? Quanto rende a arbitragem? Tamanho da poça. *Fala (50 s).*
7. **Amadurecimento.** Erro do token ao longo do tempo, com o ETF ao lado, e eventos de infraestrutura (exploratório). *Fala (50 s).*
8. **Se continuar: os cenários.** Painel do simulador (erro, poça, equilíbrio, risco de cauda), estresse inverso e sensibilidade. *Fala (70 s):* "Se continuar como está, em ANO o equilíbrio será de M meses; se a infraestrutura avançar, de M2; se estagnar e estressar, de M3."
9. **O que isso implica.** Papéis do token hoje e amanhã; o resultado da regra de decisão da seção 1 (a maturidade tende a vir de infraestrutura e adoção, ou a competição também contribui); implicações para a tokenização no Brasil, marcadas como argumento. *Fala (60 s).*
10. **O que aprendemos e o que não sabemos.** Limitações, próximos passos (Bloomberg, 1OZ, GLD da B3) e créditos aos mentores, se houver.

**Defesa oral de 5 minutos:** slides 1, 4, 5, 8 e 9.

**Perguntas prováveis e respostas curtas:**
- *"Os cenários são previsões?"* Não: são "se X, então Y", calibrados com os dados e com a sensibilidade das suposições; o estresse inverso mostra o que teria de ser verdade para a conclusão mudar.
- *"Isso é causal?"* Não: os eventos têm data conhecida, mas poucos fins de semana depois e um 2026 muito volátil; reportamos tamanho de efeito com intervalo.
- *"Por que PAXG?"* Porque as taxas e atestações são públicas e permitem calcular a banda; o XAUT só está na Binance desde março de 2026.
- *"Dá para ganhar dinheiro?"* Pouco, e só com custos baixos e acesso. Oportunidade pequena e cada vez menor é o sinal de maturidade, e a simulação mostra que a arbitragem sozinha não sustenta uma mesa.
- *"Por que só dados gratuitos?"* Para o trabalho ser reproduzível por qualquer pessoa.

## 9. Riscos e limitações declaradas

- O ouro subiu e caiu muito em 2026, então o desempenho da carteira depende do período; a leitura é de perda máxima e estresse.
- Os primeiros anos do PAXG (a partir de agosto de 2020 na Binance) têm pouca liquidez: erros maiores ali fazem parte da tendência, mas as séries podem ter buracos e preços defasados.
- O perpétuo da Binance e o ouro à vista da Dukascopy não são o mercado regulado da CME.
- O preço de criação e resgate da Paxos não é observado: o ganho de B é limite superior. A Paxos mantém estoque pré-cunhado, então a oferta é medida pelos fluxos do estoque, e só até 24/06/2026.
- Os custos de corretora dominam o ganho líquido de A, C e D: uma simulação ilustrativa mostra que, com custo de ida e volta de 25 bps, só cerca de 2% dos fins de semana teriam ganho líquido positivo.
- O poder estatístico dos testes de tendência e de evento é baixo a moderado (seção 3.3).
- O download da Dukascopy pode ser bloqueado (erro 403); há plano B, com perda de resolução.
- O prêmio do ETF é estimado com horários diferentes (NAV pelo preço de Londres, cota na bolsa americana).
- Os cenários dependem de parâmetros estimados com poucos fins de semana e de suposições (por exemplo, o custo de uma mesa); a sensibilidade e o estresse inverso mostram o quanto cada uma pesa.
- Não há componente de aprendizado de máquina; dois dos três trabalhos premiados em 2025 usaram IA. Um monitor simples do erro de reabertura é a extensão natural.

## 10. Checklist de entrega

- [ ] PDF com no máximo 10 slides e a fonte em cada figura; envio pelo formulário oficial.
- [ ] Código e scripts (recomendados, não obrigatórios), em .txt e em repositório.
- [ ] Repositório com código e instruções para reproduzir.
- [ ] Nenhum dado bruto da Dukascopy no repositório.
- [ ] Nenhuma figura ilustrativa: tudo com dado real.
- [ ] Simulador rodado com a calibração real (`config/cal.json`); os números de `cenarios_demo` são ilustrativos e não podem aparecer nos slides.
- [ ] Cada resultado de cenário aparece com a frase "se X, então Y" e com a faixa de incerteza.
- [ ] Limitações no slide 10.
- [ ] Se alguém da equipe tiver vínculo com instituição representada na banca, avisar a organização.

---

## 11. Por que esta estratégia e não outra

Avaliei todas as estratégias discutidas contra os cinco critérios da banca e quatro fatores práticos. **As notas são julgamento meu, de 1 a 5, e não medição**; a banca de 2026 e as outras equipes são desconhecidas.

Legenda: **Rel** relevância do problema, **Mét** adequação metodológica, **Sol** qualidade da solução (aplicabilidade), **Cri** criatividade, **Imp** análise das implicações; **Cla** clareza para o jurado, **Via** viabilidade hoje com dados gratuitos, **Nul** resistência a um resultado nulo (a conclusão serve nos dois sentidos), **Dif** diferenciação no campo.

| Estratégia | Rel | Mét | Sol | Cri | Imp | **Soma (máx. 25)** | Cla | Via | Nul | Dif |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. ML clássico em cripto (volatilidade, carteira) | 3 | 3 | 4 | 2 | 2 | **14** | 5 | 5 | 5 | 1 |
| 2. Hedge cambial com stablecoins | 4 | 3 | 4 | 2 | 3 | **16** | 5 | 2 | 3 | 3 |
| 3. Fluxo de informação (entropia, fatores em bitmap) | 2 | 4 | 2 | 4 | 2 | **14** | 2 | 3 | 2 | 4 |
| 4. Carteira cripto com ouro tokenizado | 3 | 3 | 4 | 3 | 3 | **16** | 4 | 4 | 3 | 3 |
| 5. Token ou ETF: só o guia de decisão | 4 | 3 | 4 | 3 | 4 | **18** | 5 | 4 | 4 | 3 |
| 6. Arbitragem, maturidade e degraus (versão anterior) | 4 | 4 | 2 | 4 | 4 | **18** | 2 | 3 | 2 | 4 |
| 7. RWA ampliado (ouro, títulos e outros tokens) | 5 | 3 | 3 | 3 | 4 | **18** | 3 | 1 | 3 | 2 |
| 8. Versão da rodada anterior (hoje, evolui, cenários) | 5 | 4 | 4 | 4 | 5 | **22** | 3 | 3 | 3 | 4 |
| **9. Versão atual, com problema explícito, hipótese testável e versão garantida** | 5 | 4 | 4 | 4 | 5 | **22** | 4 | 4 | 4 | 4 |

**Leitura:**
- As estratégias 1 e 2 são claras, mas a 1 é a mais disputada (os pódios de 2022 a 2025 foram dominados por previsão e carteira em cripto) e a 2 depende de dados de livro de ofertas em reais que não são gratuitos.
- A 3 é original, mas é difícil de explicar e de aplicar.
- A 5 é a mais clara e prática, e foi incorporada à atual como o ponto de equilíbrio contra o ETF.
- A 6 tinha boa base e má história: a tese era abstrata e os números principais eram coeficientes.
- A 7 é a mais relevante, mas inviável hoje e mais próxima do trabalho que ficou em 3º lugar em 2025.
- A 8 era a melhor em conteúdo, mas o problema não estava explícito e a tese afirmava a conclusão antes da evidência.
- A 9 mantém o conteúdo da 8 e corrige isso: problema e pergunta explícitos, hipótese com regra de decisão e uma versão garantida para o caso de algo atrasar.

**Fragilidades que a versão atual ainda tem:**
1. Os números dos cenários dependem de uma calibração com poucos fins de semana; sem ela, nada vai para os slides.
2. O escopo é grande para um dia, e a versão garantida existe por isso.
3. Não há componente de aprendizado de máquina, que apareceu em dois dos três pódios de 2025; um monitor simples do erro de reabertura é a extensão natural.
4. O poder estatístico da tendência e dos eventos é baixo a moderado, e o texto é cuidadoso com isso.
5. Vi só uma equipe concorrente (outro tema, agentes de IA); a sobreposição real é desconhecida.

---

## 12. Glossário

- **Arbitragem:** comprar onde está barato e vender onde está caro o mesmo ativo.
- **Cenário:** conjunto de premissas sobre o futuro; o resultado vale "se as premissas valerem", não como previsão.
- **Estresse inverso:** pergunta o quanto uma suposição teria de mudar para a conclusão mudar.
- **Poça de lucro:** soma, em dólares por ano, do que a arbitragem rende depois dos custos.
- **Erro de reabertura:** diferença entre o preço do token e o do ouro no instante em que o mercado tradicional reabre.
- **Meia-vida:** tempo para o desalinhamento cair à metade.
- **NAV:** valor patrimonial por cota de um fundo.
- **Perpétuo:** futuro sem vencimento, com taxa de financiamento periódica.
- **Ponto-base:** 0,01%.
- **Stablecoin:** moeda digital que busca valer US$ 1.
- **Wrapper:** token que representa um ativo guardado fora da blockchain.
