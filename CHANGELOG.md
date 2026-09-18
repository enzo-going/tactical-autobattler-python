# Changelog

## Não lançado

### Interface

- Paleta refeita: as superfícies passam a ser neutras quentes, sem o desvio de
  matiz para o verde que pintava fundo, painéis, cartas e botões.
- Cor volta a ter significado: azul é o seu lado, terracota é o rival, latão é
  recurso e foco. O laboratório segue a mesma regra — o "comandante azul" era
  azul só no nome, porque o token `--blue` guardava um verde-oliva.
- Contraste conferido par a par: texto principal 15,8:1 sobre o fundo,
  secundário 8,6:1, rótulos miúdos 6,3:1 e bordas de controle em 3:1.
- Carta e tabuleiro deixam de ser dois tons do mesmo marrom: a mesa é escura e
  as peças são de papel, 14,6:1 entre uma e outra. A tinta dentro da carta é
  escura, então o texto miúdo ganha o contraste de papel impresso.
- Cada peça recebe uma faixa do time no topo — azul ou vermelha —, de modo que
  o lado se lê antes de qualquer texto, e não só pela cor do retrato.

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
