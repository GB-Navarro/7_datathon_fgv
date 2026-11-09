# O preço da promessa: fidelidade, custos e acesso 24/7 no PAXG

**Revisão v3 implementada:** o núcleo descrito abaixo foi preservado. A extensão retrospectiva acrescenta contrastes pareados, cinco previsões temporais e sensibilidade de cobertura cambial, documentadas em [MODELAGEM_REVISAO.md](auditoria/MODELAGEM_REVISAO.md), [REFINAMENTO.md](results/REFINAMENTO.md) e [config/refinement.json](config/refinement.json). A tese distingue ajuste observado, previsibilidade e captura econômica; os modelos lineares não demonstraram melhora sobre a persistência. A apresentação científica final usa Áureo v2, com dez slides principais e três anexos, em [HTML](slides/entrega.html) e [PDF](slides/entrega.pdf).

Plano final revisado em **08/11/2026**. A especificação executável está em [projeto_agentes (1).md](<projeto_agentes (1).md>), os parâmetros em [config/params.json](config/params.json) e a avaliação crítica em [AUDITORIA.md](AUDITORIA.md). As versões anteriores estão preservadas em `historico/`.

O plano foi implementado para a equipe **BitFlow: Gabriel Navarro, Lorenzo Cavalcante e Rodrigo Menin**. Os resultados reais estão em [INTERPRETACAO.md](results/INTERPRETACAO.md), a apresentação em [entrega.pdf](slides/entrega.pdf) e a reprodução no [README](README.md). Os exemplos algébricos abaixo continuam ilustrativos; não foram promovidos a resultados de mercado.

Na execução, o ouro exigiu volume/atividade para remover barras sintéticas; Bitfinex forneceu a referência USD desde 2020; o sinal de convergência usa minutos concluídos. O mínimo de 78 trajetórias conjuntas não foi atingido (55 válidas), então foi aplicada a sensibilidade determinística prevista, sem reduzir o limiar depois dos resultados. A descrição restante documenta o desenho e seus critérios.

## 1. O problema e a contribuição

O PAXG oferece exposição a ouro físico com negociação em mercados cripto. O investidor, porém, enfrenta três perguntas práticas: quanto o preço se afasta de uma referência de ouro; quanto custa entrar, manter e sair; e quais condições de acesso são necessárias para explorar uma diferença observada.

**Pergunta central:** quão fiel é o PAXG ao ouro quando ambos negociam, o que acontece quando a referência reabre e quanto o acesso 24/7 custa sob diferentes condições de negociação?

**Hipótese de trabalho:** boa fidelidade em horários comuns pode coexistir com desalinhamentos relevantes e custos altos em determinadas condições. A existência de uma diferença de preço não assegura lucro após execução e financiamento. A hipótese admite qualquer direção de resultado.

**Frase para o jurado:** “Separamos fidelidade ao ouro, custo do acesso 24/7 e retorno de convergência sob condições explícitas de negociação.”

O destinatário principal é um investidor que já dispõe de dólares e acesso aos mercados comparados. Emissores e plataformas podem usar os resultados para identificar atritos. As implicações brasileiras serão discutidas como extensão, sem estimar impostos, câmbio e acesso local que não foram medidos.

Há literatura sobre o tema. A contribuição é uma aplicação reproduzível que combina sincronização, custos, robustez e decisão de uso. Não afirmar “ninguém mediu direito” nem prometer ineditismo acadêmico. Ver [literatura consultada](auditoria/fontes_verificadas.md).

## 2. O que podemos concluir

Uma diferença na reabertura é um **desalinhamento em relação à cotação de referência**, que também está sujeita a spread, baixa liquidez e atualização assíncrona. Ela pode conter informação antecipada, prêmio de liquidez, risco de acesso ou ruído. Não será chamada automaticamente de erro do token.

Uma simulação lucrativa será descrita como **resultado condicional aos preços, custos e acesso assumidos**. Não será apresentada como arbitragem sem risco ou recomendação de operação disponível a qualquer investidor.

Uma tendência de redução do desalinhamento permite falar em melhora observada de fidelidade. Não identifica sua causa. Competição, infraestrutura e adoção interagem; pouca renda de arbitragem pode inclusive ser consequência de competição eficiente. A antiga conclusão “infraestrutura, não competição” e sua regra H0 foram retiradas.

## 3. As cinco entregas do núcleo

| Entrega | Pergunta respondida | Conteúdo |
| --- | --- | --- |
| Fidelidade e reabertura | Quanto o PAXG se afasta da referência? | Desvio em horários comuns, desalinhamento ao reabrir, uma hora e sete horas depois, amostra e cobertura |
| Risco de preço | Quando os desvios são maiores? | Mediana, p95, frequências acima de 25/50/100 bps, datas extremas e qualidade dos preços |
| Custos e convergência | Que custo elimina o ganho aparente? | Grade de custos; simulação com sinais definidos antes da entrada quando houver dados adequados; perdas preservadas |
| Token versus ETFs | Quanto custa manter exposição? | PAXG contra **GLD e GLDM**, por prazo, tamanho e cenário de negociação |
| Matriz de decisão e sensibilidade | Para quem o token atende à necessidade? | Acesso fora do horário, fidelidade observada, custo, limitações e cenários condicionais |

O pacote permanece completo se a simulação de execução não passar pelos critérios de qualidade: apresenta a convergência observada e a grade de atritos, sem publicar lucro realizável.

## 4. Dados, janela e amostras

A janela pretendida vai de **28/08/2020 12:00 UTC a 08/11/2026 00:00 UTC, sem incluir o instante final**. O último fim de semana histórico elegível é o de 01/11/2026. Há **323 candidatos de calendário**, antes de excluir feriados, falhas, conversão monetária ausente ou dados insuficientes. O domingo de entrega não entra na amostra principal.

Usaremos PAXG/USDT da Binance, XAUUSD bid/ask da Dukascopy e uma cotação observada de USDT/USD onde houver cobertura. A amostra principal em dólares usa somente a interseção válida. Uma extensão antiga com a hipótese USDT=USD será identificada e exibida separadamente; não será misturada aos resultados principais. PAXG/USD de uma segunda corretora é robustez opcional.

Os endpoints Coinbase existem hoje, mas os testes não retornaram dados em agosto de 2020. A cobertura será descoberta no download. `1/USDCUSDT` não substitui automaticamente USDT/USD: isso importaria o risco do USDC para a medida.

Uma amostra horária de ouro bid e ask já foi baixada com sucesso na revisão. O arquivo completo de seis anos e as janelas de minutos ainda precisam ser validados. Todas as datas extremas serão conferidas individualmente, sem apagar uma observação apenas por ser extrema.

## 5. Como medir

Em horários em que ambos negociam, calcularemos a diferença logarítmica entre o PAXG convertido em dólares e o XAUUSD. Na reabertura, compararemos o último preço anterior do token com a primeira cotação válida da referência e repetiremos a medida depois de 1h e 7h.

Os dados horários dão uma medida aproximada: o último negócio de uma vela pode ter ocorrido antes do fim dela. Por isso, uma checagem em minutos nos 26 fins de semana válidos mais recentes avaliará quanto a sincronização muda os resultados. Se faltarem timestamps de negócios, a antiguidade exata do preço continuará declarada como desconhecida.

O risco de preço será mostrado com distribuição, intervalos por blocos e número de observações. “Estresse” usará um limiar calculado com o passado do salto da referência; não será descrito como causa do desalinhamento. Riscos de custódia, resgate e contraparte aparecerão como documentais, sem serem ranqueados artificialmente contra bps de desvio.

## 6. Convergência e custos

A estratégia condicional observa o sinal uma hora depois da reabertura. A entrada ocorre apenas no minuto seguinte e a saída seis horas após a entrada. O sinal escolhe comprar o token relativamente barato ou vender o relativamente caro, com uma perna oposta em ouro.

Vender token exige estoque ou empréstimo. Operar ouro exige instrumento, conta, margem e financiamento. A referência da Dukascopy não comprova essas condições para todo participante. O plano registra o que é observado, o que é hipótese e o que é desconhecido. Sem empréstimo/financiamento documentado, a saída é uma sensibilidade, não “lucro líquido executável”.

Custos serão contabilizados por execução. Uma posição de convergência com duas pernas e sua liquidação envolve quatro execuções. Uma diferença entre corretoras pode ser capturada com duas execuções se houver estoques pré-posicionados; recompor o inventário é outra etapa e pode consumir o ganho. Não confundir esses casos.

Não haverá seleção das semanas lucrativas usando o futuro. Todas as operações sinalizadas entram no balanço, inclusive perdas e casos sem saída observável, que serão identificados como não avaliáveis. Capacidade baseada em percentual de volume será uma hipótese, nunca profundidade comprovada de livro.

## 7. Token versus ETF

A comparação incluirá o GLD, com taxa anual de 40 bps, e o GLDM, com 10 bps, conforme os emissores. Comparar apenas com GLD produziria uma conclusão limitada a um ETF relativamente mais caro. [GLD](https://www.spdrgoldshares.com/usa/gld/) · [GLDM](https://www.ssga.com/us/en/individual/etfs/spdr-gold-minishares-gldm)

O cenário atual de armazenamento do token usa zero; taxas de negociação, spreads e retirada serão observadas quando possível e, caso contrário, serão hipóteses explícitas. A condição atual da Paxos não será aplicada retroativamente a seis anos de operações. [Condições vigentes](https://support.paxos.com/articles/5590384005-pax-gold-paxg-overview)

O equilíbrio de custos é aproximadamente `12 × custo adicional de ida e volta / economia anual de manutenção`, com todos os termos em bps. **Exemplo puramente algébrico:** 25 bps de ida e volta no token e 3 no ETF resultam em 6,6 meses contra GLD e 26,4 contra GLDM, se as demais condições forem iguais. O exemplo não é uma estimativa de mercado.

O painel mostrará também os casos em que não há cruzamento, a igualdade já ocorre no início ou o token é mais caro em todo o horizonte. Menor custo não será traduzido automaticamente em melhor investimento, pois os produtos têm riscos e direitos diferentes.

## 8. Evolução e cenários

O amadurecimento será medido como evolução descritiva da mediana e do p95 do desvio em horários comuns. Serão usados trimestres completos, cobertura comparável e ajuste simples pela volatilidade da referência. Muitas horas correlacionadas não equivalem ao mesmo número de observações independentes.

O simulador será pequeno e virá depois do núcleo: reamostrará blocos conjuntos de semanas recentes, preservando os sinais, a convergência, a liquidez e os regimes que aparecem juntos nos dados. O horizonte é um ano condicional.

| Cenário | Premissa explícita |
| --- | --- |
| Referência | Repetição estatística da amostra recente, com incerteza |
| Menor atrito | Mesmos caminhos de preço, custos variáveis reduzidos à metade |
| Estresse | Desvios e custos variáveis duplicados, volume reduzido à metade e custo hipotético de armazenamento de 20 bps/ano |

Esses multiplicadores são exercícios de sensibilidade, não efeitos estimados de uma tecnologia ou evento. O simulador não prevê em que ano o mercado amadurecerá. Se não houver amostra recente suficiente, haverá apenas uma tabela de sensibilidade determinística.

## 9. O que ficou para depois

Carteira BTC/ETH, financiamento de perpétuos, ranking de papéis, regressões de fluxos on-chain, soma das rotas A/B/C, estudo de evento causal, tamanho de uma mesa profissional e cenário de adoção DeFi saíram do núcleo.

As extensões podem entrar no material suplementar apenas depois que os resultados principais estiverem concluídos. A negociação de ouro no fim de semana já possui alternativas em 2026, inclusive 1OZ da CME e perpétuos; o PAXG não será anunciado como o único sinal disponível. [CME](https://www.cmegroup.com/notices/electronic-trading/2026/07/20260713.html)

Não adicionaremos ML apenas porque apareceu em trabalhos vencedores. Um modelo simples com preço e custo bem definidos é suficiente para a pergunta proposta.

## 10. Execução e cortes

O prazo oficial é **08/11/2026 às 23h59 de Brasília**. A meta é enviar até 22h. A escolha de até 10 slides é editorial; o regulamento consultado não fixa esse número. Havendo instruções complementares à equipe, elas precisam ser confrontadas com esta versão. Scripts existentes devem ser enviados também em TXT. [Regulamento](https://eesp.fgv.br/sites/default/files/uploads/regulamento-do-desafio-de-dados-de-moedas-digitais-fgv-2026_0.pdf)

O plano de trabalho começa em T0, o início efetivo da implementação, e deve caber nas horas restantes:

| Tempo desde T0 | Entrega | Condição de avanço |
| --- | --- | --- |
| 0–30 min | Ambiente, parâmetros e amostras de fontes | Ouro e token acessíveis; cobertura monetária identificada |
| 30–120 min | Downloads principais e mapa de qualidade | UTC, unidades, ausência de duplicatas e lacunas explicadas |
| 2–3h | Painéis e três fins de semana conferidos à mão | Datas, sinais, preços e identidade algébrica reconciliados |
| 3–4h30 | Fidelidade, risco e custo GLD/GLDM | Resultados com cobertura, unidades e hipóteses |
| 4h30–5h30 | Simulação condicional, tendência e sensibilidade | Apenas componentes que passam os critérios de dados |
| 5h30–7h | Matriz de decisão, figuras e PDF | Cada número rastreado à saída correspondente |
| 7–8h | Revisão, leitura do PDF e empacotamento | Sem números ilustrativos ou conclusões além da evidência |

Às **19h** encerra-se análise nova; até **20h30**, PDF preliminar; até **21h30**, revisão e pacote; **22h**, envio. O limite de relógio prevalece sobre a tabela relativa. Se T0 for tardio, cortar primeiro extensões, depois cenários estocásticos, depois inferência de tendência e a simulação por minutos. Não sacrificar qualidade, fontes ou revisão final para manter uma análise extra.

Se faltar ouro intradiário confiável após 45 minutos de tentativas, reduzir o estudo a fidelidade em dias úteis e custos. Não substituir silenciosamente XAUUSD por futuro contínuo nem chamar análise diária de arbitragem na reabertura. Se a extensão em dólares tiver pouca cobertura, apresentar explicitamente a amostra menor e a sensibilidade à conversão.

## 11. Apresentação de até 10 slides

| Slide | Mensagem e entrega |
| --- | --- |
| 1 | Pergunta, decisão prática e contribuição delimitada |
| 2 | Dados, cobertura e por que reabertura requer sincronização |
| 3 | Fidelidade em horários comuns |
| 4 | Desalinhamento ao reabrir, 1h e 7h depois |
| 5 | Cauda, situações de estresse e riscos documentais |
| 6 | Quanto atrito elimina o ganho; simulação condicional se validada |
| 7 | PAXG versus GLD e GLDM por tamanho e prazo |
| 8 | Evolução observada e sensibilidade, com seus limites |
| 9 | Matriz de decisão: necessidade, acesso, custo e evidência |
| 10 | Resposta, limitações, fontes e próximos passos |

Uma redução a 8 slides junta 3/4 e 8/9. Os títulos finais acompanham os dados: “não detectamos melhora” e “não identificamos retorno robusto sob as hipóteses” são resultados legítimos. Não haverá título predeterminado sobre lucro pequeno, ausência de competição ou superioridade do token.

## 12. Quando o projeto estará pronto

- [ ] Cobertura efetiva e exclusões publicadas por fonte e por resultado.
- [ ] Todas as comparações monetárias têm conversão observada ou hipótese explícita.
- [ ] Medida horária identificada como aproximação e checada em minutos onde disponível.
- [ ] Custos por execução sem spread em duplicidade e sem perdas descartadas.
- [ ] GLD e GLDM incluídos; equilíbrio descrito como equilíbrio de custos.
- [ ] Tendências e cenários sem alegação causal ou previsão de maturidade.
- [ ] Nenhum resultado ou teste atribuído a código que não existe.
- [ ] PDF, scripts TXT, fontes e instruções de reprodução conferidos.

A revisão deixou um desenho metodológico defensável e um escopo executável com cortes claros. Sua validação empírica depende da qualidade e da cobertura que o pipeline ainda vai medir.
