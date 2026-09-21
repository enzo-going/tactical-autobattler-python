# Changelog

## 0.5.0 — Cadência

### Regras

- **Recarga por arma.** O martelo do Tanque e a conjuração do Médico gastam a
  rodada seguinte recarregando. Enquanto recarrega, a peça não golpeia nem cura,
  mas continua podendo proteger, reposicionar e esperar — a rodada não vira
  tempo morto. Vale também para o golpe no forte.
- Espada, escudo, lança e arco seguem agindo todas as rodadas. Dar cadência ao
  arco foi medido e reprovado: a vazão de dano cai abaixo do ritmo de reforço,
  o campo nunca esvazia e todas as batalhas passam a terminar no limite de
  rodadas. Fica para quando a renda por rodada for revista.
- Medido em 480 batalhas: as batalhas continuam terminando antes do limite
  (23,2 rodadas em média), a diferença entre quem abre a rodada e quem responde
  segue em 0,0 p.p. e o equilíbrio entre estilos não mudou.

### Interface

- A peça mostra **⟳ Recarregando** com as rodadas que faltam, e a ficha da
  unidade lista a cadência ao lado de ataque, defesa e alcance.
- Manual com a seção de recarga.

### Correções

- Havia dois serializadores de tropa, um no motor e outro na CLI, e só um
  conhecia os campos novos. O relatório passa a usar o do motor.

## 0.4.0 — Capítulo III: a linha decide

### Regras

- **O alcance passa a ser contado em fileiras, a partir de quem ataca.** Antes
  só a fileira do alvo contava, e uma espada guardada na retaguarda batia como a
  que estava na linha de choque. Agora vanguarda contra vanguarda é uma fileira,
  e da retaguarda até a vanguarda rival são duas: quem tem alcance 1 precisa
  estar na frente para lutar.
- A retaguarda sobe sozinha quando a vanguarda cai — a regra antiga de "sem
  vanguarda, todos alcançam o fundo" virou consequência da formação.
- **Lanceiro**, alcance 2, custo 4: golpeia a vanguarda rival sem sair da
  retaguarda. É a peça que torna a segunda fileira uma posição ofensiva.
- No modo automático, que não tem ordem de reposicionamento, quem não alcança
  gasta a ação avançando em vez de ficar parado.
- Medido em 480 batalhas: a vantagem de quem abre a rodada caiu de +16,7 p.p.
  para 0,0 — a posição passou a pesar mais que a iniciativa.

### Interface

- Manual com a seção de alcance e formação, no lugar do texto que descrevia a
  regra antiga.
- Os módulos Python que o navegador busca em tempo de execução passam a carregar
  versionados: sem isso, quem já tinha aberto o jogo continuava jogando com o
  motor antigo em cache.
- **Paleta neutra.** As superfícies perdem a matiz própria — ardósia em vez do
  oliva antigo e do marrom que veio depois. A única cor que sobra na tela é a
  que significa alguma coisa: azul é o seu lado, vermelho é o rival, latão é
  recurso.
- **A peça vira face de carta**: janela de arte no topo, faixa do time, nome,
  atributos, vida e estado. O fundo da janela identifica a espécie, para as
  unidades se distinguirem de longe.
- **A carta é outro plano, não outro tom.** A mesa é escura e a peça é clara,
  16:1 entre uma e outra; dentro dela a escala inverte e o texto miúdo ganha o
  contraste de papel impresso. Antes a carta estava a 1,2:1 do tabuleiro — no
  papel aprovada pelo WCAG, no olho uma mancha só.
- **Faixa do time** no topo de cada peça, em luminâncias diferentes entre azul e
  vermelho, para o lado não depender só da matiz.
- **Laboratório alinhado** à mesma escala. A barra de vida lá passa a usar a cor
  do lado: com o azul valendo "vida cheia", uma unidade vermelha inteira
  aparecia azul. O aviso de vida baixa e crítica continua em latão e vermelho.
- Contraste conferido par a par, em três famílias: texto sobre a superfície,
  superfície contra superfície e um lado contra o outro.
- **O campo vira cenário.** O tabuleiro deixa de ser uma grade e passa a ser uma
  paisagem em SVG, com as quatro linhas de formação viradas uma para a outra,
  como nos auto-battlers de formação de navegador que inspiraram o projeto.
- **Elenco original em vetor**: um desenho por função, com equipamento que
  identifica o papel e cor de pano que identifica o exército. As figuras
  respiram paradas, reagem ao golpe e à cura; o botão Animações desliga tudo.
- O laboratório usa o mesmo elenco no replay e no manual, sobre o mesmo cenário.
- Números de dano sobem sobre a tropa atingida, em vez de só aparecerem no
  diário de combate.

### Documentação

- Roadmap ganha a fase III, que registra a direção de jogo de cartas com
  criaturas e move campanha para lá.

## 0.3.0 — Capítulo II: sob seu comando

### Jogo

- A entrada web passa a ser uma partida interativa contra o computador.
- `TacticalSession` em Python com fases explícitas e comandos validados.
- Recrutamento e posição manuais; uma ação por tropa por rodada.
- Ataque, proteção, cura, reposicionamento e espera com confirmação de alvo.
- Respostas alternadas, oito tropas por lado e retaguarda exposta após a
  eliminação da vanguarda.
- Fim de partida, desempate e exportação de comandos reproduzíveis.

### Interface

- Tabuleiro com paleta terrosa, fontes locais e peças SVG.
- Layout para celular, alvos por botão, foco visível e manual.
- Abertura recolhida durante o combate e diário com histórico expansível.
- Tratamento de carregamento/falha do Python e opção de tentar novamente.

### Compatibilidade e documentação

- Replay e torneios preservados em `simulator.html`, com paleta alinhada.
- Regras e comandos anteriores da CLI preservados. O modo textual interativo
  continua usando as regras históricas, diferentes da nova sessão web.
- Build local e Pages unificados em `tools/build_site.py`.
- 25 testes de sessão/ponte e teste opcional de navegador real.
- README, guia de transição e roadmap atualizados para a nova fase.
- Empacotamento explícito de `battle_simulator`, permitindo instalação normal
  e editável sem incluir `web` ou `legacy` como pacotes.
- CI em Python 3.10 e 3.12 verifica também os comandos instalados fora dos fontes.
- Manual e relatório esclarecem o desempate por dano de golpes, sem sangramento,
  e a ausência de renda após o fim da partida.

Detalhes das diferenças entre modos em [Fase II](docs/phase-two.md).

## 0.2.0 — Base de simulação

- Pacote de domínio, motor automático, estratégias, CLI e torneios.
- Relatórios estruturados, eventos e snapshots por rodada.
- Interface web com Pyodide, replay e GitHub Pages.
- Testes e workflows automatizados.
