# Biblioteca de design da BitFlow

**Direção escolhida: Áureo, revisão 2.0.** O conceito atual é o intervalo entre lastro e preço, aplicado a um caderno de ensaio e registro de apuração. Veja [AUREO.md](AUREO.md) e o [HTML atualizado](01-aureo.html).

Abra [index.html](index.html) no navegador para comparar as propostas. Todos os recursos estão nesta pasta; mantenha `assets/` junto dos HTMLs. Não é necessário servidor ou acesso à internet.

| Sistema | HTML | Símbolo em SVG | Papel principal |
| --- | --- | --- | --- |
| Áureo | [01-aureo.html](01-aureo.html) | [Marca de intervalo](assets/aureo-symbol.svg) | Tese, abertura, credibilidade editorial |
| Vértice | [02-vertice.html](02-vertice.html) | [Referência comum](assets/vertice-symbol.svg) | Método, evidência, custos e comparações |
| Meridiano | [03-meridiano.html](03-meridiano.html) | [Janela de mercado](assets/meridiano-symbol.svg) | Tempo, acesso 24/7 e narrativa |

Cada direção tem oito lâminas: capa; identidade/paleta; tipografia/componentes; método; fidelidade; convergência; manutenção; conclusão. As lâminas de identidade são parte do estudo visual, não uma proposta de inseri-las na apresentação científica final.

Use as setas ou os botões inferiores para navegar. `G` abre a visão geral; `F` alterna tela cheia; `Home` e `End` vão ao início e ao fim. A navegação superior permite comparar as direções. O botão de impressão exporta os oito slides em 16:9, sem a interface. Para imprimir, habilite os gráficos de fundo no navegador.

O planejamento completo está em [PLANO.md](PLANO.md), e as cores, famílias e dimensões em [tokens.json](tokens.json). As escolhas visuais podem ser reaplicadas ao gerador de slides do projeto após a seleção da direção. O PDF científico original não é alterado por este estudo.

Os exemplos numéricos são gerados a partir das tabelas existentes por `python slides/design-systems/build.py`, executado da raiz do repositório. As fontes são distribuídas localmente sob SIL Open Font License; os cinco textos de licença estão em `assets/fonts/OFL-*.txt`. Origem: repositório oficial [google/fonts](https://github.com/google/fonts), diretórios `ofl/manrope`, `ofl/dmserifdisplay`, `ofl/spacegrotesk`, `ofl/instrumentserif` e `ofl/ibmplexmono`.

`previews/` contém as capas, pranchas de contato e um comparativo. `QA_design.json` registra a conferência de navegação, impressão, fontes, contraste e layout no navegador. Os arquivos HTML também funcionam com abertura direta por `file://`.

Para consultar os exemplos em formato de apresentação: [Áureo PDF](previews/aureo.pdf), [Vértice PDF](previews/vertice.pdf) e [Meridiano PDF](previews/meridiano.pdf). Cada arquivo tem oito páginas. O [ZIP dos sistemas](bitflow-design-systems.zip) reúne os HTMLs, recursos e documentação.

A verificação opcional usa `requirements-design.txt`. Execute `python slides/design-systems/check_design.py` e, em seguida, `python slides/design-systems/make_previews.py`. No Windows, a verificação utiliza o Chrome instalado no caminho padrão; nos outros ambientes, instale o navegador do Playwright. Não é necessário instalar essas dependências para visualizar os sistemas.
