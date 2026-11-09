# Plano de ajustes — PAXG × Ouro (Datathon FGV EESP 2026)

Prazo de entrega: **08/11/2026, 23h59**. Se a entrega já foi feita, tudo
abaixo vira material para a apresentação da final (16/11) e para responder
perguntas da banca.

Os itens estão em três blocos, por urgência. Dentro de cada bloco, por
esforço crescente.

---

## Bloco 1 — Correções obrigatórias (minutos, sem dado novo)

Nada aqui exige coleta. São erros que a banca consegue pegar de cabeça.

- [ ] **Slide 6, "110 bps".** Esse número só vale no cenário de custos
  originais (40×44/16). No cenário intermediário, que é o mostrado no
  slide, o valor correto é ≈ 60 bps. Recalcular e trocar.
- [ ] **Slide 5, "−11,0 bps em 1h".** Não bate com a Fig. 3 (+14,2 → +9,8,
  ou seja −4,4). Checar qual métrica gerou o −11,0 e, se for outra coisa
  (ex.: média vs. mediana, janela diferente), legendar explicitamente.
- [ ] **Slide 5, "ainda explica 64%".** R² sobe de 54% para 64% — é alta,
  não queda. Trocar "ainda" por "chega a" ou reescrever a frase.
- [ ] **Tese central.** Trocar "a arbitragem de horas não paga" por algo
  como "a arbitragem na reabertura do fim de semana, com saída em até 24h,
  não paga". A generalização atual é maior que o teste feito.

---

## Bloco 2 — Reforços de alto retorno (horas, dado que vocês já têm ou é fácil de puxar)

### 2.1 Teste fora da amostra: mesma regra aplicada ao XAUT
**Por quê:** é a resposta mais direta à crítica de que a banda (±19) e o
cenário de custos foram escolhidos depois de ver os dados. Rodar a
*mesma* regra, sem reestimar nada, em um ativo que vocês não usaram para
calibrar nada é um teste de verdade.

**Como:**
1. Puxar PAXG/USDT já existe; adicionar XAUT/USDT (Binance ou Kraken,
   mesma hora de corte 15h–20h UTC).
2. Rodar exatamente a regra do slide 7 (±19 bps, mesmos custos
   proporcionais — ajustar só a taxa de criação/resgate do Tether, que é
   maior que a da Paxos).
3. Reportar o resultado seja ele qual for. Se funcionar, é o melhor slide
   do trabalho. Se não funcionar, é um achado sobre o emissor, não um
   problema — dizer isso com todas as letras.

**Entregável:** 1 slide novo ou 1 linha extra na tabela de robustez do
slide 8.

### 2.2 Dados on-chain de emissão/resgate (mint/burn)
**Por quê:** hoje a explicação para o nível ("atrito na arbitragem") é
citada (Shleifer-Vishny, Makarov-Schoar) mas não testada — o próprio
slide 4 admite isso. Dados de mint/burn transformam a citação em teste.

**Como:**
1. PAXG é ERC-20; eventos `Transfer` de/para o endereço zero (`0x000...0`)
   são mint/burn. Etherscan (API gratuita) ou Dune Analytics já têm
   dashboards prontos de supply do PAXG — usar como atalho se o tempo
   apertar.
2. Agregar por dia: mint líquido (criação − resgate).
3. Testar a hipótese simples: mint líquido correlaciona com o nível do
   desvio (negativamente, se a arbitragem de criação estiver funcionando
   — desvio positivo deveria puxar mais resgate, por exemplo).
4. Bônus barato: checar se a resposta é lenta (lag de dias), o que reforça
   a história de atrito.

**Entregável:** 1 gráfico (mint líquido × desvio) + 1-2 frases de
interpretação. Não precisa de modelo, só correlação e um gráfico de
dispersão ou série temporal dupla.

### 2.3 Consolidar slides 5 e 6
Os dois contam a mesma história (curto prazo não paga). Fundir em um
libera espaço no pitch de 10 slides para os itens novos sem estourar o
limite.

---

## Bloco 3 — Se sobrar tempo (mais trabalho, maior diferencial)

### 3.1 Gradient boosting + SHAP para explicar o nível
**Por quê:** é o uso de ML que agrega, porque testa uma pergunta que o
deck deixa em aberto, em vez de decorar o trabalho com um rótulo de IA.

**Como:**
1. Variável-alvo: variação semanal do nível estimado (já existe, do
   modelo de componentes não observados).
2. Preditores: mint líquido (2.2), funding do perpétuo de ouro/PAXG na
   Binance, retorno do BTC, prêmio do USDT, volume do PAXG, volatilidade
   do ouro.
3. **Obrigatório:** avaliação walk-forward (treina só com o passado) e
   comparação com uma regressão linear simples nas mesmas variáveis.
4. Reportar SHAP só se o modelo bater a regressão linear. Se não bater,
   reportar isso — "as variáveis de mercado cripto explicam X% do nível,
   e o modelo não linear não acrescenta poder preditivo" é um resultado
   honesto e incomum no histórico do Datathon.

**Entregável:** 1 slide com SHAP summary plot (ou a frase de "não bateu
a linear", se for o caso) + nota metodológica no material suplementar.

### 3.2 Regime-switching (HMM) como regra alternativa de rotação
**Por quê:** data os regimes de prêmio/desconto com probabilidade, em vez
de olhar o gráfico; e dá uma segunda regra de rotação sem banda escolhida
a dedo, para comparar com a de ±19.

**Como:**
1. HMM de 3 estados (prêmio / neutro / desconto) no desvio diário.
2. Usar **apenas probabilidades filtradas** (nunca suavizadas — estas
   usam o futuro e invalidariam o teste).
3. Regra: ir ao PAXG quando P(desconto) filtrada > 50%, voltar ao GLDM
   quando P(prêmio) filtrada > 50%.
4. Reportar como mais uma linha na tabela de robustez do slide 8, não
   como estratégia nova e separada.

**Entregável:** 1 linha na tabela existente, com ciclos, % positivas e
bps/ano, igual às outras linhas da tabela.

### 3.3 Reforço de literatura
Adicionar 1 referência de cada lado:
- Petajisto (2017) sobre desvios de preço em ETFs.
- Lyons & Viswanath-Natraj (2023) sobre o que sustenta a paridade de
  stablecoins.

Objetivo: posicionar o trabalho entre as duas literaturas na frase de
abertura, sustentando a alegação de ineditismo.

### 3.4 Slide reserva: conta em reais
IOF, IR sobre ganho de capital em token vs. ETF, custo de câmbio.
Não entra no limite de 10 slides — fica como material suplementar para
responder se a banca perguntar (FGV tem prêmio de cidadania financeira,
é provável que perguntem).

---

## Se o tempo for muito curto

Ordem de prioridade por retorno sobre esforço:

1. Bloco 1 inteiro (são minutos).
2. 2.1 — XAUT fora da amostra.
3. 2.2 — mint/burn on-chain.
4. 3.2 — HMM (mais rápido de rodar que 3.1).
5. 3.1 — boosting + SHAP.
6. 3.3 e 3.4 — literatura e slide de reais.

Os itens 2.1 e 2.2 juntos já permitem dizer na final: "testamos a regra
fora da amostra em outro token e usamos dados on-chain para checar a
hipótese de atrito na arbitragem" — cobre criatividade sem perder rigor.
