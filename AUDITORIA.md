# Auditoria crítica e decisão sobre o plano final

Revisão de 08/11/2026. Objeto: os dois planos recebidos e a avaliação anterior do assistente. Este arquivo preserva o parecer anterior à implementação. A execução posterior está documentada no [README](README.md), nos [resultados](results/INTERPRETACAO.md), nos [testes](results/pytest.xml) e na [integridade](results/QA_integrity.json). Assim, as pendências descritas abaixo devem ser lidas como o estado daquela etapa, não como ausência atual de código e resultados.

## 1. Parecer

O tema é pertinente ao Datathon e o desenho revisado é defensável como estudo aplicado de fidelidade, custos e condições de negociação do PAXG. As perguntas centrais agora podem ser respondidas mesmo com ausência de lucro, ausência de tendência ou acesso incompleto a uma rota.

A tese anterior, segundo a qual infraestrutura/adoção explicaria a maturidade em vez da competição, **não era identificada pelos testes propostos**. Essa tese e a regra de decisão H0 foram retiradas. A correção não é apenas substituir linguagem causal por palavras mais suaves: é retirar o contraste causal da pergunta principal e das decisões do simulador.

O plano continua condicionado à aquisição completa e ao QA. Ele não comprova retorno de arbitragem, superioridade do token, maturidade do mercado ou competitividade da equipe. Essas respostas não podem ser certificadas antes dos dados.

## 2. Correções da avaliação anterior

| Afirmação anterior | Reavaliação | Ajuste aplicado |
| --- | --- | --- |
| Tema adequado ao desafio | Mantida; amparada no evento e regulamento oficiais | Mantido o recorte de problema real com dados externos citados |
| PDF e scripts TXT | Mantida com precisão: TXT é a forma exigida dos scripts se houver, não apenas recomendação | Entrega corrigida nos dois documentos |
| Limite oficial de 10 slides não confirmado | Mantida; o PDF foi efetivamente baixado e lido nesta revisão | Dez slides é meta editorial; verificar material complementar da equipe |
| Ausência de ML seria fragilidade competitiva | Não é uma exigência metodológica ou do regulamento | Retirada como ponto fraco; escopo não ganha ML sem necessidade |
| “Originalidade alta” | Era julgamento, sem revisão bibliográfica suficiente | Há literatura próxima; contribuição definida como aplicação reproduzível, sem promessa de ineditismo |
| Todo desvio é erro do token | Crítica mantida | Adotado “desalinhamento contra referência”; checagem de sincronização e trajetória |
| Teste de sinal deve ser central | Qualificação: só é indispensável para afirmar poder preditivo/descoberta de preço | O núcleo deixou de fazer essa afirmação; previsão temporal é extensão |
| C exigiria sempre quatro execuções e estaria subestimada | **Correção da resposta anterior**: duas execuções capturam uma diferença com inventário pré-posicionado | Fórmula de dois fills preservada para troca pontual; ciclo de recomposição separado |
| A isenção de criação da Paxos teria terminado em setembro/2026 | **Correção da resposta anterior**: página consolidada mais recente estende a isenção até janeiro/2027 | Versão antiga retirada como fonte vigente; condições atuais não viram taxas históricas |
| Resgate atual entre 0,125% e 0,5% | Confirmado na página consolidada, com incidência marginal por atividade líquida | Corrigido o modelo conceitual e mantido como contexto, sem backtest retrospectivo |
| Uso de `max(pnl,0)` superestima rentabilidade | Mantido para um resultado que pretenda ser realizável; essa soma pode ser um diagnóstico irrealista se rotulada | P&L assinado no núcleo; sem seleção por lucro futuro |
| Pouca poça de lucro prova que não há capital profissional | Inferência inválida; mesa existente pode ter custo marginal baixo e outras receitas; competição também comprime lucro | Retirada a comparação com custo fixo de mesa como regra de tese |
| Falta código/simulador no repositório recebido | Confirmado: inicialmente havia só dois MDs e nem metadados Git | Afirmações de simulador pronto e dez testes passados foram retiradas |
| Aproximadamente 323 semanas, e não 340–370 | Tornada exata para o corte adotado: 323 candidatos de calendário, 30/08/2020–01/11/2026 | Número válido só será conhecido após cobertura e exclusões |
| Falta de liquidez/short/custos limita execução | Mantida, mas custo omitido não precisa ser exigido de uma rota que realmente não o usa | Custos por rota, por execução, hipótese de estoque e campos desconhecidos explícitos |

## 3. Pontos fracos do projeto e soluções

### Identificação econômica

Competição e infraestrutura não são explicações mutuamente exclusivas. Custo menor pode melhorar a arbitragem; arbitragem eficiente pode deixar pouco ganho observado. Uma regressão de aproximadamente duas dezenas de trimestres, com proxies de fluxo e muitos controles, não separa esses mecanismos. Intervalo incluindo zero não demonstra ausência de efeito.

**Correção:** perguntas observacionais como núcleo; tendência como associação; eventos como contexto; nenhuma conclusão causal da antiga H0. Se futuramente houver uma pergunta causal, ela exigirá fonte de variação e desenho próprios.

### Informação, referência e sincronização

Uma série contínua e outra fechada não fornecem automaticamente um preço verdadeiro comparável durante o fim de semana. Mesmo na reabertura, a primeira cotação pode ter spread largo e a última transação do token pode ser antiga. Usar candles da mesma hora não resolve tudo.

**Correção:** identificar a referência específica e seus horários; separar `b_0`, `b_1h` e `b_7h`; marcar idade de negócio desconhecida; auditar minutos recentes; conferir individualmente extremos. A medida horária é uma aproximação declarada, sem rótulo de erro puro.

### Moeda de cotação e cobertura

O início da série Binance foi verificado no ZIP: 28/08/2020 às 12:00 UTC. Porém, os endpoints Coinbase atuais não retornaram candles na janela de agosto/2020 testada. O projeto anterior pressupunha uma cobertura que ainda não havia sido medida. Um proxy USDC=USD pode confundir o desvio das duas stablecoins.

**Correção:** amostra primária em USD apenas onde q foi observado; extensão com paridade suposta separada; descoberta de cobertura por fonte; nenhuma imputação através de gaps ou resgate artificial de histórico ausente.

### Custos, posição e perdas

Fechar um par de posições de quantidades fixas gera P&L com preços, não simplesmente queda do desvio absoluto. O tamanho definido por volume da hora seguinte usa informação futura. O Corwin-Schultz com t e t+1 também usa dado futuro se tratado como sinal disponível em t.

**Correção:** P&L por uma unidade em cada perna, sinais antes das entradas, execução no minuto seguinte, sizing com passado, taxas sobre cada fill e spreads sem duplicação. Conservar perdas, saídas faltantes e financiamento desconhecido. Volume percentual é hipótese de capacidade, não liquidez comprovada.

### Benchmark do investidor

GLD é um benchmark útil, mas usar apenas seu custo anual pode exagerar a vantagem de carregamento do token. GLDM custa menos. Usar cotação de broker para ETF contra NAV em outro horário também introduz ruído de comparação.

**Correção:** comparar custos com GLD e GLDM; retirar do núcleo o prêmio ETF calculado com proxy de NAV; usar spread oficial de bolsa ou grade suposta. Incluir tamanho da posição, custos fixos, caminho de custódia e todos os casos de cruzamento, inclusive vantagem que se reverte.

### Estatística e cenários

Mais linhas horárias não eliminam dependência temporal. O p95 de uma pequena subamostra de estresse é baseado em pouquíssimos extremos. As simulações de poder e os números ilustrativos dos cenários não puderam ser reproduzidos porque o código referido não estava presente.

**Correção:** blocos semanais, contagens e intervalos; tendência trimestral simples com amostra mínima; retirada de percentuais de poder não reproduzidos. Cenários usam caminhos conjuntos e premissas explícitas, sem fabricar ruído positivo independente ou extrapolar ano de maturidade. Se a amostra for pequena, usar sensibilidade determinística.

### Oferta, mudanças de rede e execução primária

O controlador atual não identifica necessariamente todos os estoques e controladores históricos. Movimentação de estoque não equivale a compra de cliente. Oferta truncada em junho não deve ser reconciliada com totalSupply de novembro. Sem a cotação da Paxos, nem todo “limite superior” de lucro é um limite matemático garantido.

**Correção:** on-chain e B saem do núcleo. A extensão exige reconciliação no mesmo período/rede, análise de endereços e premissas de cotação/acesso; emissão primária e transferências internas permanecem conceitos separados.

### Tamanho do projeto e narrativa

O MVP anterior ainda era um conjunto de pesquisas distintas: arbitragem, oferta, carteira, previsão, ETFs, eventos e cenários de adoção. A soma de requisitos de dados e QA era incompatível com a margem de prazo declarada.

**Correção:** cinco entregas centrais, fontes reduzidas, fases com gates, cortes explícitos e PDF mínimo completo mesmo sem a simulação de execução. Não há dependência de on-chain ou de um resultado favorável. A entrega final pode ter oito slides consistentes.

## 4. Afirmações que foram retiradas por falta de sustentação suficiente

- “Ninguém mediu direito”, “ouro tokenizado é o caso mais líquido de RWA” e avaliações de concorrência não apoiadas por uma revisão suficiente.
- Dados agregados de USD 178 bilhões, 97% de concentração e menos de 2% em DeFi, assim como exemplos específicos de preço de março/2026, não reproduzidos nesta auditoria. Não foram declarados falsos; foram retirados por não serem necessários ao núcleo e exigirem verificação própria.
- Percentuais de poder estatístico, resultados do `cenarios_demo`, multiplicadores de estresse inverso e a existência de dez testes de um simulador não fornecido.
- Equivalência entre volume negociado, profundidade do livro e capacidade de capital profissional.
- “Não detectar resposta da oferta sugere poucos agentes”, “sem tendência o mercado não amadureceu” e “pouco lucro implica infraestrutura como causa”.
- Qualquer afirmação de que todo ouro tradicional fecha no fim de semana em 2026. A reabertura analisada é a da referência escolhida; há outros instrumentos com negociação de fim de semana.

## 5. O que foi efetivamente verificado

As fontes e os resultados pontuais estão em [fontes_verificadas.md](auditoria/fontes_verificadas.md). O regulamento foi salvo e lido; o primeiro ZIP Binance foi aberto em memória; produtos e candles Coinbase foram consultados; ouro bid/ask recente foi baixado; o XLSX GLD respondeu; versões de Python/Node e ajuda da CLI foram executadas.

O utilitário [verificar_plano.mjs](auditoria/verificar_plano.mjs) confere fórmulas, casos de fronteira e consistência documental. Executar com `node auditoria/verificar_plano.mjs`. O modo opcional `--sample-dir CAMINHO` confere as duas amostras Dukascopy baixadas nesta revisão; elas não fazem parte da distribuição do repositório.

Resultado desta revisão: **19 verificações passaram**, incluindo a amostra com 69 observações em cada lado e ask >= bid nos open/close alinhados. Sem o argumento de amostra, as 18 verificações documentais/algébricas são reproduzíveis com os arquivos entregues. São checagens desta revisão, não os testes ainda pendentes do pipeline empírico.

Essas verificações distinguem viabilidade de acesso de validade de resultado. Não foram baixadas as séries completas, reconstruídos livros históricos, identificados arbitradores ou executados os testes futuros do pipeline.

## 6. Condições para considerar o projeto final sólido

| Condição | Situação após esta revisão |
| --- | --- |
| Pergunta delimitada e relevante | Atendida no desenho |
| Conclusões compatíveis com identificação | Atendida após retirar H0 causal |
| Contabilidade de preços/custos coerente | Especificada e checada algebricamente |
| Fontes principais acessíveis em testes pontuais | Atendida para as amostras consultadas |
| Cobertura histórica e sincronização completas | Pendente da implementação |
| P&L executável, empréstimo e financiamento | Não demonstrados; só haverá simulação condicional enquanto faltarem dados |
| Inferência e robustez empíricas | Pendentes da implementação |
| Entrega viável em escopo reduzido | Planejada com gates e cortes; depende das horas restantes e do QA |
| Reprodutibilidade e ausência de números inventados | Requisitos explícitos; resultados ainda não produzidos |

O plano corrigido está pronto para orientar a implementação. Sua solidez é a de um desenho verificável, com falhas tratadas e resultados possíveis nos dois sentidos. O estudo só estará empiricamente validado depois de passar os gates de dados e resultados definidos na especificação.
