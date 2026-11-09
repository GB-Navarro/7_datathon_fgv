# Plano da entrega v3

Data: 08/11/2026, 22h10 (Brasília). Prazo: 23h59. A v1 (`slides/entrega.pdf`) e a v2 (`slides/entrega_v2.pdf`) continuam intactas e enviáveis; a v3 vai para `slides/entrega_v3*.pdf`, `results/v3/` e `entrega/v3/`.

## O que foi pedido e como cada ponto é atendido

| Pedido | Como a v3 atende |
| --- | --- |
| Metodologia mal descrita | Dois slides de metodologia: (I) fluxograma do pipeline, do preço ao resultado, com as regras contra dado futuro; (II) os três modelos do desvio (componentes não observados, correção de erro, regimes de Markov) e as duas operações testadas, lado a lado. |
| HMM não aparece | O slide de metodologia II mostra como o HMM é estimado (reestimação mensal, filtro sem futuro). O Resultado 1 traz a figura das probabilidades filtradas de desconto e prêmio. O slide de robustez traz a regra por regimes contra a faixa fixa. |
| Storytelling mais claro, uma história por página | Estrutura de artigo, como no PDF de referência: motivação e hipóteses (H1, H2, H3), dados, metodologia, um resultado por hipótese, robustez e discussão. Cada slide de resultado começa pela hipótese que testa e termina com a leitura. |
| Estilo de escrita igual, sem cara de IA | Mesmo tom das versões anteriores: frases diretas, números com unidade, sem frases de efeito, sem "não é X, é Y". |
| Copiar o layout e o desenho do PDF de referência | Fundo areia, título em fonte slab pesada, rótulo de seção em mono vermelho ("I · MOTIVAÇÃO E PROBLEMA"), régua preta grossa sob o cabeçalho, caixas com borda preta, painel escuro com sombra deslocada em vermelho, faixa de números grandes, capa com moldura e selo circular, última página escura. |
| Manter vários gráficos e acrescentar fluxogramas | Todos os gráficos da v2 são reaproveitados com a nova paleta. Entram uma figura nova (probabilidades do HMM) e dois fluxogramas (pipeline e reestimação do HMM). |

## Estrutura (10 slides)

1. Capa: título, pergunta, resumo com os números principais e selo "+130 bps/ano".
2. I · Motivação, fundamentação e hipóteses.
3. II · Dados, medida e checagens.
4. III · Metodologia I: do preço ao resultado (fluxograma).
5. III · Metodologia II: os modelos do desvio e as duas operações.
6. IV · Resultado 1 (H1): o desvio tem dois ritmos (nível, ruído e regimes do HMM).
7. IV · Resultado 2 (H2): a reabertura não paga a arbitragem.
8. IV · Resultado 3 (H3): a rotação captura o nível.
9. IV · Resultado 4: robustez (custos, atraso, regimes, XAUT e placebo).
10. V · Discussão, implicações e conclusões (página escura).

A pergunta "token ou ETF" vira um painel no slide 8 (3,9 e 15,6 meses até empatar em custo; desvio-padrão de 81 bps da variação do desvio em 12 meses) e a conclusão 5 do slide 10. Os gráficos dessa pergunta ficam no material suplementar, que é o da v2.

## Revisão depois da validação independente (22h20–22h35)

O revisor considerou a v3 melhor que a v2 e apontou correções, todas aplicadas:
- evidência de token × ETF no slide 8;
- XAUT descrito como "teste em outro token";
- separação entre o que foi fixado antes e o que foi definido depois dos resultados;
- título do slide 9 sem exagero;
- causa do resgate tratada como hipótese;
- meias-vidas explicadas;
- R² da reabertura em decimal, para não confundir com os 64%;
- rótulos fora das linhas dos gráficos;
- equações em linhas separadas;
- unidade no placebo e na capa;
- rodapés sem caminhos internos;
- letras maiores nos slides 2 e 10, e uma frase de fechamento da tese.

## Validação do plano

| Risco | Mitigação |
| --- | --- |
| Tempo: cerca de 1h40 | Só reorganização e estilo; nenhum número novo além das probabilidades do HMM, que já estão em `results/v2/T19_regimes_probabilidades.csv`. Se às 23h25 a v3 não passar no QA, a recomendação é enviar a v2. |
| Alterar v1 ou v2 | Código novo em `src/v3_deck.py`. As cores dos gráficos são trocadas só na memória do processo, sem editar os módulos antigos. Conferência de hashes da v1 no fim. |
| Fonte slab indisponível | Baixar Alfa Slab One (OFL, Google Fonts) para a pasta de fontes; se falhar, usar DM Serif Display. |
| Página densa | Uma hipótese por slide de resultado; QA automático de estouro e revisão visual dos 10 slides. |
| Números inconsistentes | Todos lidos dos mesmos arquivos da v2; conferência por extração do PDF. |
