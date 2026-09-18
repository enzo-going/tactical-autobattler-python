# Changelog

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

Detalhes das diferenças entre modos em [Fase II](docs/phase-two.md).

## 0.2.0 — Base de simulação

- Pacote de domínio, motor automático, estratégias, CLI e torneios.
- Relatórios estruturados, eventos e snapshots por rodada.
- Interface web com Pyodide, replay e GitHub Pages.
- Testes e workflows automatizados.
