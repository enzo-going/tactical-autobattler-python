# Roadmap

## Fase I — simulador (0.2, concluída)

- Pacote Python com modelos de POO, regras, efeitos e estratégias.
- CLI, simulações determinísticas, torneios espelhados e relatórios JSON.
- Testes automatizados, CI e publicação via GitHub Pages.
- Interface de replay usando o próprio pacote Python no navegador.

## Fase II — jogo interativo (0.3, concluída)

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
3. Ampliar cenários de treino e objetivos para testar diferentes formações.
4. Dar aos bots estilos próprios de combate e planejamento de várias ações;
   proteção, movimento e golpes finais básicos foram entregues na 0.7.
5. Feedback visual breve de dano e movimentação, sem bloquear comandos nem
   prejudicar quem prefere movimento reduzido.
6. Expandir verificações para Firefox, Safari e leitores de tela.

## Preparação tática (0.7, concluída)

- Formação editável sem custo entre combates, sem curar ou limpar efeitos.
- Devolução integral de recrutas da preparação atual; veteranos preservados.
- Previsão de dano, cura e efeitos calculada pelo motor antes da confirmação.
- Rival usa avanço, proteção e oportunidades de golpe final.
- [Medição do modo interativo](gameplay.md) com política de jogador fixa.

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
- Alcance contado em fileiras a partir de quem ataca, com a retaguarda subindo
  quando a vanguarda cai, e o Lanceiro como a arma de haste que golpeia da
  segunda linha (0.4).

- Recarga por arma: martelo pesado e conjuração esperam uma rodada (0.5).

Próximos passos na mesma direção — do lado das regras:

1. Cadência para as armas de alcance, junto com uma revisão da renda por rodada.
   Reavaliar após a correção das ordens automáticas. Na medição anterior: com o arco recarregando, a vazão de dano cai abaixo do ritmo
   de reforço e nenhuma batalha termina antes do limite de rodadas.
2. Unidades que ocupam dois espaços — cavalaria forte, mas vulnerável a lanças.
   A referência é explícita: cavalo morre para lança.
3. Facções com forças e fraquezas próprias, em vez de um só elenco espelhado.
4. Estados visíveis na arte: sangramento, escudo e atordoamento como marcas na
   figura, não apenas como texto embaixo dela.
5. Campanha: sequência de confrontos com um esquadrão que persiste entre
   partidas. Depende de salvar/retomar sessão, que já está na lista acima.

Pendência de equilíbrio: revisar composições depois da correção das ordens
automáticas. A conclusão anterior sobre o estilo defensivo era afetada por
ações transferidas entre tropas após baixas. Na [nova amostra de 600 batalhas](review-formation.md),
o defensivo vence 62,1%; o agressivo domina com 87,1%. Isso pede ajuste medido
próprio e não valida o equilíbrio do modo interativo.

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
