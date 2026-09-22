# Tactical Auto-Battler

[![Tests](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/tests.yml/badge.svg)](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/tests.yml)
[![Pages](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/pages.yml/badge.svg)](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/pages.yml)

Um pequeno jogo tático em turnos feito em Python. Recrute um esquadrão, forme a
linha e abra caminho até o forte adversário. As tropas ficam de pé no campo, em
vanguarda e retaguarda, cada função com arte própria.

**[Jogar no navegador](https://enzo-going.github.io/tactical-autobattler-python/)** ·
[Laboratório de simulação](https://enzo-going.github.io/tactical-autobattler-python/simulator.html) ·
[A transição para a fase II](docs/phase-two.md)

> A versão publicada acompanha `main`. Mudanças em uma branch/PR só aparecem
> no site após merge e conclusão do workflow Pages. Para testar uma branch,
> siga as instruções locais abaixo.

![Dois exércitos em formação no campo de batalha, com vanguarda e retaguarda de cada lado](docs/images/campo.svg)

<sub>O cenário e o elenco acima são os arquivos do próprio jogo, compostos por `tools/make_key_art.py`.</sub>

## O campo

A partida acontece sobre um cenário desenhado à mão em SVG — serra, neblina e um
forte em ruínas entre os dois estandartes — e não sobre uma grade neutra. Cada
lado ocupa duas linhas de formação, vanguarda e retaguarda, viradas uma para a
outra: a leitura do campo é a mesma dos auto-battlers de formação de navegador
que inspiraram o projeto.

O elenco é vetorial e original, um desenho por função — soldado, arqueiro,
guardião, médico, tanque e lanceiro —, com equipamento que identifica o papel e a cor do
pano identificando o exército. As figuras respiram paradas, reagem ao golpe e à
cura, e o botão **Animações** desliga tudo isso para quem preferir o campo
imóvel. Nada disso depende de imagem externa: são os mesmos arquivos que o
laboratório usa no replay.

## Capítulo II — sob seu comando

Na versão 0.2, a interface calculava a partida inteira e apresentava um replay.
O jogador escolhia duas estratégias e assistia. A versão **0.3** retoma a ideia
de um jogo por turnos: a partida existe como uma sessão em Python e espera por
uma ordem a cada decisão. Nenhum cronômetro avança o campo.

| Antes: simulador | Agora: modo principal |
| --- | --- |
| Escolher dois bots | Comandar um esquadrão contra um bot |
| Assistir à sequência pronta | Escolher unidade, ação e alvo |
| Recrutamento automático | Comprar reforços e decidir a linha |
| Cura e proteção automáticas | Decidir quando atacar, curar ou proteger |
| Play, pause e velocidade | Preparação, ações alternadas e revisão |
| Relatório de uma simulação | Histórico de comandos e estado da partida |

O laboratório continua disponível com simulações, replays e torneios. Os dois
modos compartilham alcance por fileiras e recarga; diferem em alternância,
recrutamento e ordens automáticas. Seus resultados medem balanceamentos distintos.

A [documentação da fase II](docs/phase-two.md) registra decisões de arquitetura,
diferenças de regras, contrato de comandos e processo de migração.

## Como jogar

1. **Prepare.** Comece com 10 suprimentos e recrute até 8 unidades. Escolha a
   vanguarda ou a retaguarda, ou mantenha a posição recomendada.
2. **Dê ordens.** Entre em combate, selecione uma unidade pronta, escolha uma
   ação e confirme o alvo. O rival responde com uma unidade. Cada peça age
   uma vez por rodada, inclusive os recrutas recém-chegados.
3. **Reorganize.** Quando todas as unidades agirem, confira o resultado da
   rodada. Se a partida continuar, ambos recebem 6 suprimentos e o jogo espera
   você avançar.
4. **Vença.** Elimine as tropas para atacar o forte rival. Destruir a base vence
   a partida. No limite de rodadas, vence a base com mais vida; em igualdade,
   conta o dano de golpes causado (sem sangramento). Persistindo a igualdade,
   há empate.

| Unidade | Custo | Alcance | Recarga | O que oferece |
| --- | ---: | :---: | :---: | --- |
| Soldado | 2 | 1 | — | Linha de frente barata |
| Arqueiro | 3 | 2 | — | Atinge de longe e causa sangramento |
| Guardião | 4 | 1 | — | Resiste a golpes e pode proteger um aliado |
| Médico | 5 | 2 | 1 rodada | Cura 2 de vida; a conjuração demora |
| Tanque | 5 | 1 | 1 rodada | Golpe pesado que atordoa o alvo |
| Lanceiro | 4 | 2 | — | Golpeia a vanguarda rival sem sair da retaguarda |

Todas as peças podem atacar, proteger a si mesmas, trocar de linha ou esperar.
Cada ordem consome a ação.

O alcance é contado **em fileiras, a partir de onde a tropa está**: frente
contra frente é 1, fundo contra frente é 2, e fundo contra fundo é 3. Se um lado
não tem vanguarda viva, sua retaguarda conta como frente para medir a distância,
sem mudar a posição de recrutamento. Reforçar a vanguarda volta a proteger o fundo.

Uma arma de alcance 1 atrás de aliados na frente precisa avançar para atingir
as tropas rivais. No jogo você dá a ordem **Reposicionar**; no laboratório o
avanço é automático e gasta a ação. Armas de alcance 2 podem atingir o fundo
rival quando estão na própria frente, ou a frente rival quando estão atrás.

Cada arma também tem a sua **cadência**. O martelo do Tanque e a conjuração do
Médico gastam a rodada seguinte recarregando — nessa rodada a peça ainda pode
proteger, reposicionar ou esperar, mas não golpear nem curar. Por isso o
esquadrão rende mais quando mistura cadências: enquanto o martelo recarrega, a
linha de frente sustenta o dano.

É a formação e o tempo, e não só a ficha da unidade, que decidem a batalha.

A seed define quem abre a primeira rodada; a prioridade alterna nas seguintes.
Os estilos rivais mudam as compras. Durante o combate, todos usam a mesma
heurística: unidade mais rápida disponível, cura se possível, ataque ao alvo
alcançável com menos vida. Você escolhe livremente a ordem de suas peças.

## Rodar localmente

Requer **Python 3.10+**. O pacote de jogo usa somente a biblioteca padrão.

```bash
python tools/build_site.py
python -m http.server 8765 --bind 127.0.0.1 --directory _site
```

Abra [localhost:8765](http://localhost:8765). Refaça o build depois de editar os
fontes. Abrir `web/index.html` diretamente como arquivo não funciona: os módulos
Python precisam ser servidos por HTTP.

O navegador carrega Python por [Pyodide](https://pyodide.org/), via CDN, na
primeira visita. Isso exige conexão. A partida roda localmente na aba, sem
backend, conta ou envio das decisões a um servidor.

## Interface

O campo usa verde oliva, tons de terra, fontes do sistema e silhuetas em SVG.
A abertura recolhe ao entrar em combate para dar espaço ao tabuleiro. Abaixo de
800 pixels, os comandos ficam sob o campo; em telas pequenas, as peças se
organizam em duas colunas. Alvos também aparecem como botões no painel, sem
depender de arrastar peças, hover ou precisão do mouse.

Há foco de teclado visível, rótulos de vida e ações, avisos de turno anunciados
por leitores de tela, manual e preferência de movimento reduzido. O diário
mostra os seis eventos mais recentes e permite abrir todo o histórico.

## Arquitetura Python / POO

```text
battle_simulator/
  models.py       # Base, Troop, subclasses, efeitos, linhas e fábrica
  engine.py       # Motor automático, dano, eventos e snapshots
  session.py      # Sessão interativa: fases, comandos e ações válidas
  strategies.py   # Políticas de compra e planos dos bots
  tournament.py   # Confrontos e métricas do laboratório
  cli.py          # Simulador, modo textual histórico e exportação
web/
  index.html      # Jogo principal
  game.js         # Controles, apresentação e tradução dos eventos
  game.css        # Tabuleiro e interface responsiva
  playground.py   # Ponte JSON entre navegador e pacote Python
  simulator.html  # Laboratório preservado
  app.js          # Replays e torneios
  style.css       # Estilos do laboratório
tools/
  build_site.py   # Mesmo build local e no GitHub Pages
tests/
  test_engine.py  # Regressões do simulador
  test_session.py # Regras e comandos do jogo interativo
  browser_smoke.py # Verificação opcional com navegador real
```

`TacticalSession` compõe `BattleEngine` e os objetos de domínio existentes.
A interface recebe estado, eventos e ações válidas; não calcula dano, alcance,
recursos ou vitória em JavaScript. Identificadores são em inglês; interface e
documentação estão em pt-BR.

## Simulador e linha de comando

Os comandos anteriores continuam funcionando:

```bash
python -m battle_simulator --mode auto --strategy-one aggressive --strategy-two defensive --rounds 20 --seed 11
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --seeds 3,7,11 --summary-only
python -m battle_simulator --mode auto --quiet --report-json reports/battle.json
python -m battle_simulator --list-strategies
python -m battle_simulator --mode interactive --rounds 20
```

O último comando é a interface textual **histórica** do simulador. O novo ciclo
de ações alternadas está na interface web e na API Python `TacticalSession`.
Não foi feita uma migração silenciosa das regras da CLI.

Instalação opcional dos comandos `tactical-autobattler` e `battle-simulator`:

```bash
python -m pip install -e .
```

Para instalar uma cópia sem vínculo com os fontes, use `python -m pip install .`.
Só o pacote `battle_simulator` é instalado; a interface web e os scripts
históricos permanecem no repositório.

## Testes

```bash
python -m unittest discover -s tests
python -m compileall battle_simulator tests web/playground.py tools
node --check web/game.js
node --check web/app.js
node --check web/characters.js
node --check web/replay-state.js
node --test tests/replay.test.cjs
```

Node executa as verificações de JavaScript e compara o replay com snapshots
do motor Python, inclusive depois de buscar outra posição na linha do tempo.
O CI verifica Python 3.10 e 3.12, incluindo a instalação e a execução dos
comandos de console fora da pasta dos fontes.
Os testes Python cobrem modos anteriores, comandos inválidos, custos, limite
de esquadrão, alcance, alvos estáveis, habilidades, efeitos, renda, desempate,
fim de partida e reprodução determinística do histórico.

O CI também joga uma partida real em Chromium. Para executar localmente:

```bash
python -m pip install playwright==1.63.0
python tools/build_site.py
python tests/browser_smoke.py
```

Por padrão usa Edge instalado. Para Chromium, execute
`python -m playwright install chromium` e defina `BROWSER_CHANNEL=chromium`
no ambiente. Ele percorre uma partida real com Pyodide, exportação, reinício,
seis larguras de tela, ações no celular e o laboratório. Playwright é uma
dependência de desenvolvimento, não do jogo. O script abre e encerra seu próprio
servidor; `SITE_URL` permite verificar uma publicação existente. Capturas e
relatório ficam em `_site/qa` e nos artefatos do CI.

## Limites desta versão

- A partida vive na memória da aba. Recarregar começa outra; não há autosave.
- O JSON registra configuração, comandos e snapshots, mas ainda não há botão
  de importar ou retomar. A reprodução em Python está em
  [phase-two.md](docs/phase-two.md#relatórios-e-reprodução).
- O mapa tem duas linhas por lado, sem deslocamento em grid.
- Ainda não há campanha, multiplayer, áudio ou progressão persistente.
- O equilíbrio interativo precisa de playtests; métricas antigas de torneio
  não validam automaticamente as novas regras.

## Histórico e próximos passos

O projeto começou como exercício acadêmico de POO. Os scripts originais estão
em `legacy/`. A primeira reorganização criou o simulador com bots, testes e
torneios. A fase atual transforma essa base em um jogo controlado pelo jogador.

[Transição para a fase II](docs/phase-two.md) · [Changelog](CHANGELOG.md) ·
[Roadmap](docs/roadmap.md) · [Contexto acadêmico](docs/academic_context.md) ·
[Contribuição](CONTRIBUTING.md)
