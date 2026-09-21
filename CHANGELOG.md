# Changelog

## Não lançado

### Interface

Nada disso saiu em versão ainda: as três passagens de cor desta rodada estão
resumidas aqui pelo estado final, não pelo caminho.

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
