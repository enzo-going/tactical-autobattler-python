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

O alvo declarado é um jogo de cartas com criaturas: a peça no campo precisa
parecer uma carta com bicho dentro, e não uma linha de tabela. É a referência
que orienta as decisões de interface daqui para frente.

Já entregue:

- Face de carta no tabuleiro: janela de arte, faixa do time, ficha técnica e
  barra de vida, em vez de retrato miúdo ao lado do nome.
- Fundo de arte por espécie, para as unidades se distinguirem de longe.

Próximos passos na mesma direção:

1. Arte própria por unidade, maior que a silhueta de 32 px de hoje, com pose e
   contorno reconhecíveis em miniatura.
2. Mais espécies, e variações dentro da mesma função, para o recrutamento ter
   escolha de verdade em vez de uma opção por papel.
3. Estados visíveis na arte — sangramento, escudo e atordoamento como marcas na
   carta, não apenas como texto embaixo dela.
4. Campanha: sequência de confrontos com um esquadrão que persiste entre
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
