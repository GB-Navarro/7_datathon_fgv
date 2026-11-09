# Plano de implementação da entrega v2

Data: 08/11/2026, 18h50 (Brasília). Prazo de envio: 23h59. Base: [plano-ajustes-paxg-datathon.md](plano-ajustes-paxg-datathon.md).

A entrega atual (10 slides + 5 de suplementar) fica congelada e continua sendo a versão enviável. A v2 só substitui a atual se passar em todos os critérios de aceite da seção 6 até as 23h15.

---

## 1. O plano de ajustes faz sentido? Avaliação item a item

| Item | Veredito | Evidência | O que muda em relação à proposta |
| --- | --- | --- | --- |
| 1.1 "110 bps" no slide 6 | **Correto** | 110,0 = 44 × 40,01 / 16 vale para custos originais. No cenário intermediário (o do slide), 44 × 21,97 / 16 = **60,4 bps**. | Calcular o limiar a partir do cenário exibido, por código. |
| 1.2 "−11,0 bps em 1 h" × Fig. 3 | **Parcial** | Não há erro de cálculo. São métricas diferentes. A Fig. 3 é a variação média do desvio *com sinal* desde sexta (+14,2 → +9,8). O −11,0 é a variação média do desvio *absoluto* da reabertura para +1 h, nos mesmos 301 fins de semana (T7_paired_changes.csv). | Manter o número e rotular as duas métricas: "desvio com sinal" na Fig. 3 e "\|desvio\|" no cartão. |
| 1.3 "ainda explica 64%" | **Correto** | O R² sobe de 54% (reabertura) para 64% (+7 h). "Ainda" sugere queda. | Trocar por "chega a 64%". Explicar que o ruído da reabertura se dissipa e o desvio volta para perto do nível de sexta. |
| 1.4 Tese "arbitragem de horas não paga" | **Correto** | Testamos só a operação de convergência na reabertura do fim de semana (sinal em +1 h; saída em 1, 6 ou 24 h). | Usar "a arbitragem na reabertura do fim de semana, com saída em até 24 h, não paga" no slide 2, no slide 6 e na conclusão. |
| 2.1 XAUT como teste fora da amostra | **Correto, com dois ajustes** | Bitfinex `tXAUT:USD` e `tXAUT:UST` têm candles de hora desde set/2020 (sondagem feita). A Kraken lista XAUTUSD. A negociação é esparsa: 26 de 72 horas em jun/2023. | (a) A regra não usa custo de criação nem de resgate, só custos de negociação. O "ajuste da taxa do Tether" não se aplica, mas o spread e a taxa da Bitfinex são maiores e entram como segundo cenário. (b) É um teste fora da amostra *entre ativos*, no mesmo período, e não um teste em datas novas. Dizer isso no slide. |
| 2.2 Emissão e resgate on-chain | **Correto, com ressalvas** | O Blockscout (`eth.blockscout.com/api`, sem chave) devolveu 911 eventos de emissão do PAXG desde set/2020. A consulta de resgates estourou o tempo e vai em blocos menores. Os nós públicos de Ethereum recusaram consultas históricas. | (a) A Paxos emite em lotes para a tesouraria, então a data da emissão não é a data da compra do cliente. Usar dados semanais e defasagens. (b) Desde jun/2025 o PAXG também existe em Solana, então a oferta no Ethereum deixa de ser a oferta total. Testar também até mai/2025. (c) O resultado é associação, não causa. |
| 2.3 Fundir slides 5 e 6 | **Discordo** | Os dois não contam a mesma história. O slide 5 descreve o preço no fim de semana (pergunta 1); o slide 6 testa uma operação (pergunta 2). Fundir tira da banca a evidência de que a reabertura herda a sexta. | O espaço para os itens novos sai de outro lugar. O XAUT e o modelo de regimes entram como linhas na tabela do slide 8. A emissão líquida substitui a Fig. 2 no slide 4, e a Fig. 2 vai para o suplementar. Continuam 10 slides. |
| 3.1 Gradient boosting + SHAP | **Faz sentido, mas não hoje** | Exige dados novos (funding de perpétuos, BTC, prêmio do USDT) e tem cerca de 320 semanas de amostra. O risco de sobreajuste é alto e há pouco tempo. | Fica para a final (16/11), com treino só no passado e comparação contra regressão linear, como o plano pede. |
| 3.2 Modelo de regimes (HMM) | **Correto, com um ponto que faltou** | Probabilidades filtradas evitam usar observações futuras, mas parâmetros estimados com a amostra inteira também usam o futuro. Um ajuste leva cerca de 4 s (sondagem feita). | Reestimar a cada mês só com o passado (janela expansiva) e filtrar com os parâmetros congelados. Ordenar os regimes pela média para não trocar rótulos entre reestimações. |
| 3.3 Literatura | **Parcial** | Lyons e Viswanath-Natraj (2023) já estão citados. Petajisto (2017, *Financial Analysts Journal* 73(1)) sobre ETFs acrescenta. | Posicionar o trabalho entre as duas literaturas, **sem alegar ineditismo**: Cong, Mayer e Rabetti (2026) já estudam ouro tokenizado, e a auditoria inicial proíbe essa alegação. |
| 3.4 Conta em reais | **Faz sentido, mas não hoje** | Regras de IOF e IR sobre criptoativos e ETFs mudaram em 2025–2026 e precisam de fonte oficial. | Fica como slide reserva para a final, com citação da Receita Federal. |

---

## 2. Regra de não destruição da entrega atual

**Arquivos congelados.** Nenhum passo da v2 escreve, renomeia ou apaga estes arquivos:

```text
slides/entrega.pdf              slides/entrega.html
slides/entrega_suplementar.pdf  slides/relatorio_final.*   slides/material_suplementar.*
entrega/preco_da_promessa.zip   entrega/manifest.json
results/  (todos os arquivos existentes)
src/report_v5.py  src/report_v5_pages.py  src/report_v5_build.py  src/rotation.py  src/regime.py
scripts_txt/  (conteúdo atual)
```

**Como garantir.**

1. **Fase 0, snapshot.** Copiar os PDFs, o HTML, o ZIP e o manifesto atuais para `entrega/v1_final_2026-11-08/` e gravar `entrega/v1_final_2026-11-08/hashes_v1.json` com o SHA-256 de cada arquivo congelado (incluindo `results/*`).
2. **Caminhos separados.** Todo resultado novo vai para `results/v2/` (T17 XAUT, T18 on-chain, T19 regimes). Dados brutos novos vão para `data/raw/bitfinex_xaut/` e `data/raw/blockscout/`. Os slides vão para `slides/entrega_v2.pdf`, `slides/entrega_v2.html` e `slides/entrega_v2_suplementar.pdf`; ficam em `slides/` para reaproveitar as fontes. O pacote vai para `entrega/v2/preco_da_promessa_v2.zip`, e os TXT para `entrega/v2/scripts_txt/`.
3. **Código por cópia.**
   - Módulos novos: `src/v2_xaut.py`, `src/v2_onchain.py`, `src/v2_regimes.py`, `src/v2_report_pages.py` (cópia de `report_v5_pages.py` com as edições), `src/v2_report_build.py` e `src/v2_package.py`.
   - `report_v5_*` continua intacto, para que a v1 siga reproduzível.
   - O gerador v2 escreve o QA em `results/v2/QA_presentation_v2.json` e nunca em `results/QA_presentation.json`.
4. **Comandos proibidos durante a v2.** `python run_all.py --all`, `--figures`, `--v5` e `--package`, porque regravam arquivos da v1. Os testes rodam com `python -m pytest -q --junitxml results/v2/pytest_v2.xml`.
5. **Verificação final.** Recalcular os SHA-256 da Fase 0 e exigir igualdade total antes de declarar a v2 pronta.

---

## 3. Pré-registro: regras fixadas antes de baixar dados novos

Escrito antes de ver qualquer dado do XAUT, da emissão ou dos regimes. O resultado é reportado seja qual for.

**XAUT (T17).**
- **Fonte:** Bitfinex `tXAUT:USD`, candles de 1 h, de 28/08/2020 a 08/11/2026. Checagem com `tXAUT:UST` × USDT/USD da Bitfinex.
- **Ouro:** o mesmo XAUUSD da Dukascopy já usado, com o mesmo alinhamento de fechamento de barra (o candle da Bitfinex é marcado na abertura).
- **Sessão:** dias úteis da NYSE, barras com fechamento das 15h às 20h UTC, só barras com negócio de XAUT e ouro ativo. O dia entra com pelo menos 4 barras, o mesmo critério do PAXG. Como sensibilidade declarada, só por causa da liquidez esparsa, também roda com pelo menos 2.
- **Regra:** idêntica à do slide 7, com faixa ±19, atraso de 1 pregão, custos intermediários e GLDM como referência. Sem reestimar nada.
- **Segundo cenário:** custos de varejo da Bitfinex. A taxa por execução será conferida na página oficial de taxas antes de rodar, e o spread vem do próprio dado (alta − baixa da hora, mediana). A faixa é igual ao custo do ciclo, como a regra define.
- **Relato:** ciclos, % positivos, bps/ano, IC 90% (blocos de 6 meses), cobertura de dias e placebo com 1.000 sorteios. Se der negativo, o slide diz que a regra não se transfere para o XAUT e discute liquidez e emissor.

**Emissão líquida do PAXG (T18).**
- **Fonte:** Blockscout, eventos `Transfer` do contrato `0x45804880De22913dAFE09f4980848ECE6EcbAf78` de e para o endereço zero, buscados em blocos de 250 mil.
- **Série:** emissão líquida semanal em onças, contra o desvio médio semanal.
- **Testes:** (a) correlação entre o desvio da semana *t* e a emissão líquida das semanas *t+1* a *t+4*; (b) regressão da emissão líquida em defasagens de 1 a 4 semanas do desvio, e o inverso. Erros HAC, amostra completa e só até mai/2025.
- **Leitura pré-definida:**
  - prêmio seguido de emissão e desconto seguido de resgate são compatíveis com o canal de arbitragem;
  - resposta fraca ou lenta é compatível com atrito;
  - nenhuma das leituras é causal.

**Regimes (T19).**
- **Modelo:** Markov com três regimes de média e variância no desvio diário (`statsmodels.MarkovRegression`).
- **Estimação:** reestimar no primeiro pregão de cada mês só com dados anteriores, com o mínimo de 500 pregões antes de começar, e filtrar o mês com os parâmetros congelados.
- **Regra:** ir ao PAXG quando P(desconto) filtrada > 50% e voltar ao GLDM quando P(prêmio) filtrada > 50%, com custos intermediários e atraso de 1 pregão.
- **Relato:** uma linha na tabela do slide 8. A rotação por regimes começa só depois do mínimo de 500 pregões; a comparação com a faixa ±19 usa o mesmo período.

---

## 4. Fases, tempos e cortes

| Fase | Início | Duração | Entregável | Corte se atrasar |
| --- | --- | --- | --- | --- |
| 0. Snapshot da v1 e hashes | 19h00 | 10 min | `entrega/v1_final_2026-11-08/` | Obrigatória |
| 1. Correções do Bloco 1 e Petajisto | 19h10 | 20 min | `src/v2_report_pages.py` | Obrigatória |
| 2. XAUT | 19h30 | 60 min | `results/v2/T17_*` + teste sem dado futuro | Obrigatória |
| 3. Emissão on-chain | 20h30 | 45 min (limite rígido) | `results/v2/T18_*` + figura | Se às 21h15 não houver série completa, fica para a final |
| 4. Regimes | 21h15 | 40 min | `results/v2/T19_*` + teste sem dado futuro | Primeiro corte se às 21h30 a Fase 2 não tiver acabado |
| 5. Montagem do deck v2 | 21h55 | 45 min | `slides/entrega_v2*.pdf` | Obrigatória |
| 6. QA, pacote v2 e conferência de hashes | 22h40 | 25 min | `entrega/v2/` | Obrigatória |
| 7. Decisão de envio | 23h15 | — | v2 ou v1 | — |

Ordem de corte, do menos para o mais importante: 3.1 e 3.4 (já fora), Fase 4 e Fase 3. As fases 0, 1, 2, 5 e 6 são o mínimo da v2.

---

## 5. Onde cada mudança entra no deck (continua com 10 slides)

| Slide | Mudança na v2 |
| --- | --- |
| 2 | Tese com "arbitragem na reabertura do fim de semana, com saída em até 24 h". Frase de posicionamento entre a literatura de ETFs (Petajisto, 2017) e a de stablecoins (Lyons e Viswanath-Natraj, 2023), sem alegar ineditismo. |
| 4 | A Fig. 2 (horas a até 25 bps) vai para o suplementar. Se a Fase 3 entrar, a figura de emissão líquida × desvio entra no lugar, com 1 a 2 frases. Se não entrar, a Fig. 2 continua. |
| 5 | Rótulos "desvio com sinal" (Fig. 3) e "\|desvio\|" (cartão do −11,0). "Chega a 64%". |
| 6 | Título "Arbitragem na reabertura". Risco 3 com o limiar do cenário exibido (60,4 bps), calculado por código. |
| 8 | Linhas novas na tabela: "XAUT, mesma regra (Bitfinex)", "XAUT, custos da Bitfinex" e, se a Fase 4 entrar, "Regimes (HMM, filtrado)". Se o XAUT der resultado forte, entra uma frase de leitura; se der negativo, a frase diz isso. |
| 10 | Conclusão com a tese restrita e uma frase sobre o XAUT, seja qual for o resultado. |
| Suplementar | A6 novo, com metodologia e tabelas de XAUT, emissão e regimes. A Fig. 2 migra para A2. |

---

## 6. Critérios de aceite da v2

1. Os SHA-256 de todos os arquivos congelados da seção 2 batem com `hashes_v1.json`.
2. Testes novos sem dado futuro passam:
   - XAUT: alterar dados depois do dia *t* não muda decisões antes de *t*;
   - regimes: a probabilidade filtrada do dia *t* não muda quando os dados depois de *t* são alterados, incluindo a reestimação.

   A suíte inteira passa e o resultado vai para `results/v2/pytest_v2.xml`.
3. O QA de layout da v2 não acusa nada abaixo de 850 px nem fora da margem, nos 10 slides e no suplementar.
4. Todo número novo do deck é lido de `results/v2/` ou de `results/`. A extração do PDF confere os números-chave entre os slides.
5. A varredura de linguagem fica limpa: sem "não é X, é Y", sem palavras de efeito, sem menção a IA.
6. Revisão visual dos 10 slides e do suplementar a 80 dpi.

Se qualquer critério falhar às 23h15, envia-se a v1 congelada.

---

## 7. Validação deste plano

| Risco do plano | Mitigação | Checado agora? |
| --- | --- | --- |
| Apagar ou alterar a v1 | Snapshot com hashes, caminhos separados, código por cópia, comandos proibidos e conferência final | Desenho conferido contra `report_v5_build.py` e `report.py`, que hoje regravam `slides/entrega.pdf`, `results/QA_presentation.json` e o ZIP. Por isso a v2 usa geradores próprios. |
| Dado de XAUT indisponível | Bitfinex respondeu com candles de 2020, 2023 e 2026; Kraken lista o par | Sim, sondagem às 21h47 UTC |
| Liquidez esparsa do XAUT invalidar o teste | Critério de cobertura igual ao do PAXG, mais a sensibilidade pré-declarada; cobertura reportada | Sim: 26 de 72 horas em jun/2023 |
| Dado on-chain indisponível | Blockscout sem chave funcionou para emissões; resgates em blocos menores | Parcial: emissões sim (911 eventos); resgates a confirmar na Fase 3 |
| Interpretação errada de emissão e resgate | Dados semanais, defasagens, corte em mai/2025 por causa de Solana, leitura pré-definida e sem causalidade | Ressalvas registradas a partir de `auditoria/fontes_verificadas.md` |
| Uso de dado futuro no HMM | Reestimação mensal só com o passado e filtro com parâmetros congelados | Tempo de ajuste medido: cerca de 4 s para 800 dias |
| Ajustar a regra depois de ver o XAUT | Pré-registro desta seção 3, escrito antes do download | Sim, este documento |
| Estourar o limite de 10 slides | Itens novos entram como linhas e figura substituta; nada de slide novo | Sim, seção 5 |
| Ficar sem tempo | Cortes por fase e v1 pronta como fallback | Sim, seção 4 |
| Corrigir algo que não estava errado | O −11,0 é outra métrica; só o rótulo muda | Sim, conferido em `T7_paired_changes.csv` |

**Números já conferidos para o Bloco 1.** Limiar no cenário original: 110,0 bps. Limiar no cenário intermediário: 60,4 bps. Mudança média de \|desvio\| da reabertura para 1 h: −11,0 bps. Variação média do desvio com sinal desde sexta: +14,2 na reabertura e +9,8 em 1 h. R² da sexta: 54% na reabertura e 64% em 7 h.
