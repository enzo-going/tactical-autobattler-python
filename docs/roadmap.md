# Roadmap

## Fase I — simulador (0.2, concluída)

- Pacote Python com modelos de POO, regras, efeitos e estratégias.
- CLI, simulações determinísticas, torneios espelhados e relatórios JSON.
- Testes automatizados, CI e publicação via GitHub Pages.
- Interface de replay usando o próprio pacote Python no navegador.

## Fase II — jogo interativo (0.3, implementada nesta versão)

- Sessão entre comandos, com preparação, combate, revisão e desfecho.
- Recrutamento manual, duas linhas e limite de oito tropas.
- Seleção de unidade, ordem e alvo; respostas alternadas do rival.
- Ataque, proteção, cura, reposicionamento e espera.
- Tabuleiro responsivo, peças SVG, manual e diário de combate.
- Exportação de decisões e reprodução determinística pela API Python.
- Laboratório preservado e documentação das diferenças de regras.

Veja os critérios e detalhes em [Fase II](phase-two.md).

## Próxima prioridade — jogar, observar, ajustar

1. Playtests: duração, clareza, utilidade das unidades e vantagem de abrir a
   rodada. Medir o modo interativo separadamente do simulador.
2. Salvar/retomar sessão com versão de esquema e migração de regras explícitas.
3. Desfazer compras durante a preparação.
4. Melhorar o bot: proteção, movimento e estilos próprios de combate.
5. Feedback visual breve de dano e movimentação, sem bloquear comandos nem
   prejudicar quem prefere movimento reduzido.
6. Expandir verificações para Firefox, Safari e leitores de tela.

## Fase III — as peças ganham vida (direção)

A referência são os auto-battlers de formação que rodavam no navegador: dois
exércitos parados frente a frente, em fileiras, com a batalha resolvida pela
composição do esquadrão e pelo tempo de cada arma. A peça no campo precisa
parecer uma criatura em pé na linha, e não uma linha de tabela — é isso que
orienta as decisões de interface daqui para frente.

Já entregue:

- Cenário desenhado em SVG no lugar da grade, com as quatro linhas de formação
  viradas uma para a outra.
- Elenco original em vetor, um desenho por função, com equipamento indicando o
  papel e cor de pano indicando o exército.
- Reação visível: respiração parada, golpe, dano e cura, com interruptor para
  desligar o movimento.

Próximos passos na mesma direção — agora do lado das regras, não do desenho:

1. Alcance por fileira: lança e pique atingindo duas linhas à frente, o que dá
   sentido tático a posicionar fundo e frente.
2. Tempo de recarga por arma, e conjuração mais lenta que o golpe comum, para a
   ordem das ações virar decisão em vez de consequência da velocidade.
3. Unidades que ocupam dois espaços — cavalaria forte, mas vulnerável a lanças.
4. Facções com forças e fraquezas próprias, em vez de um só elenco espelhado.
5. Estados visíveis na arte: sangramento, escudo e atordoamento como marcas na
   figura, não apenas como texto embaixo dela.
6. Campanha: sequência de confrontos com um esquadrão que persiste entre
   partidas. Depende de salvar/retomar sessão, que já está na lista acima.

## Depois, se fizer sentido

- Interface textual usando a mesma `TacticalSession` da web.
- Pequenos cenários com objetivos diferentes de destruir a base.
- Terrenos e obstáculos, após validar o valor das duas linhas atuais.
- Áudio opcional e progressão entre partidas.

Multiplayer não faz parte desta entrega. Campanha passou para a fase III.

## Barra de qualidade

Regras e validação permanecem em Python. O pacote continua sem dependências
externas de runtime; Pyodide é a dependência do navegador. Mudanças devem
preservar testes, documentar diferenças entre modos e manter o build local
igual ao do GitHub Pages. Recursos futuros não devem ser apresentados como
já disponíveis.
