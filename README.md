# Tactical Auto-Battler Simulator

[![Tests](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/tests.yml/badge.svg)](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/tests.yml)
[![Pages](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/pages.yml/badge.svg)](https://github.com/enzo-going/tactical-autobattler-python/actions/workflows/pages.yml)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/Depend%C3%AAncias-nenhuma-brightgreen?style=flat)

### ▶️ [Testar no navegador](https://enzo-going.github.io/tactical-autobattler-python/)

Sem clonar, sem instalar: o próprio pacote `battle_simulator` roda no navegador
via [Pyodide](https://pyodide.org/). Escolha as estratégias, rode batalhas ou
torneios round-robin e baixe o relatório JSON.

---

Mini simulador tático auto-battler escrito em Python.

Este repositório é um projeto de portfólio independente. Começou como um pequeno
exercício acadêmico de POO e foi redesenhado em um motor de simulação compacto,
com unidades táticas, linhas de frente e fundo, efeitos de combate, estratégias
automatizadas e relatórios de torneio round-robin.

O objetivo não é ser um jogo completo. O objetivo é mostrar arquitetura
Python/POO limpa, simulações determinísticas, cobertura de testes e estrutura de
projeto legível, sem nenhuma dependência externa em tempo de execução.

> **Idioma:** a documentação e a interface web estão em pt-BR; o código-fonte
> mantém identificadores em inglês, seguindo a convenção padrão de projetos
> Python.

## Conceitos

- Python 3.10+.
- Design orientado a objetos.
- `dataclasses`, `Enum` e classes de domínio enxutas.
- Motor de batalha separado da saída da CLI.
- Atributos táticos: ataque, defesa, HP, velocidade, alcance, custo e papel.
- Modelo simples de linhas `front` / `back`.
- Efeitos de combate: `shield`, `bleed`, `stun` e `heal`.
- Estratégias automatizadas (bots).
- Torneios round-robin.
- Relatórios JSON estruturados.
- Testes com `unittest`.
- Validação via GitHub Actions.

## Interface web

A página em [enzo-going.github.io/tactical-autobattler-python](https://enzo-going.github.io/tactical-autobattler-python/)
carrega os arquivos `.py` deste repositório dentro do Pyodide e chama exatamente
as mesmas funções que a CLI usa — nenhuma regra de jogo é reimplementada em
JavaScript, e nada roda em servidor. Ela oferece:

- **Batalha** — tela de deploy com os dois comandantes, rodadas e seed; a
  batalha vira um replay animado numa arena com bases, linhas de frente e fundo,
  barras de HP, efeitos e números de dano. O campo é reconstruído a partir dos
  eventos do relatório, com controles de play/pause, velocidade, pulo de rodada
  e linha do tempo. No fim aparecem o desfecho, o destaque da partida, o log
  completo e o mesmo JSON de `--report-json`.
- **Torneio** — round-robin espelhado com pódio, classificação e matriz de
  confrontos em mapa de calor.
- **Manual** — ficha técnica das unidades lida de `battle_simulator/models.py` em
  tempo real, mais efeitos de combate e o resumo de cada estratégia.

O deploy é feito pelo workflow [`pages.yml`](.github/workflows/pages.yml), que
só publica depois que os testes passam. Os fontes da página ficam em
[`web/`](web/).

## Uso pela linha de comando

Rode os comandos a partir da raiz do repositório.

Instale em modo editável se quiser os comandos de console:

```bash
python -m pip install -e .
```

Simulação automática:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11
```

O comando de console instalado é equivalente:

```bash
tactical-autobattler --mode auto --rounds 20 --seed 11
```

Simulação automática curta:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet
```

Simulação automática com relatório JSON:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet --report-json reports/battle.json
```

Escolher estratégias na simulação automática:

```bash
python -m battle_simulator --mode auto --strategy-one aggressive --strategy-two defensive --rounds 30
```

Torneio round-robin:

```bash
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --seed 11 --report-json reports/tournament-balance.json
```

Torneio com estratégias selecionadas:

```bash
python -m battle_simulator --mode tournament --strategies aggressive,balanced,economy --simulations 20 --rounds 30
```

Torneio mostrando só a classificação, sem a linha de cada confronto:

```bash
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --summary-only
```

Listar estratégias disponíveis:

```bash
python -m battle_simulator --list-strategies
```

Modo interativo:

```bash
python -m battle_simulator --mode interactive --rounds 20
```

Rodar os testes:

```bash
python -m unittest discover -s tests
```

Compilar os módulos:

```bash
python -m compileall battle_simulator tests
```

## Modelo de batalha

Cada unidade tem:

- `attack`: dano base.
- `defense`: redução de dano, preservando um dano mínimo.
- `max_hp` e `current_hp`: vida máxima e atual.
- `speed`: prioridade de ação dentro da rodada.
- `range`: se a unidade alcança a linha de frente ou também o fundo.
- `cost`: custo de recrutamento.
- `role`: papel tático usado pelo motor e pelas estratégias.

O campo de batalha usa intencionalmente apenas duas linhas:

- `front`: mais fácil de alcançar, normalmente ocupada por unidades resistentes.
- `back`: posição mais segura para unidades de alcance e suporte.

Isso mantém o projeto pequeno e ainda demonstra posicionamento, seleção de alvo
e regras de alcance.

## Unidades

- `Soldier` (Soldado): unidade barata de linha de frente.
- `Archer` (Arqueiro): atacante de fundo com alcance, aplica `bleed`.
- `Guardian` (Guardião): unidade defensiva de frente, pode aplicar `shield`.
- `Medic` (Médico): unidade de suporte que cura aliados feridos.
- `Tank` (Tanque): unidade cara de frente, ataque forte e `stun`.

## Estratégias

- `AggressiveBot`: compra menos unidades por rodada, foca alvos fracos ao
  alcance e tenta encerrar a partida rápido.
- `BalancedBot`: monta composição mista entre frente e fundo.
- `DefensiveBot`: prioriza unidades resistentes e proteção.
- `EconomyBot`: adia parte dos gastos para comprar turnos mais fortes depois.
- `RandomBot`: usa aleatoriedade com seed.

O modo torneio roda confrontos round-robin espelhados, então cada par joga nas
duas ordens. Isso reduz o viés de ordem de jogador ao comparar estratégias
determinísticas.

A saída do torneio inclui:

- vitórias;
- derrotas;
- empates;
- taxa de vitória;
- taxa de empate;
- média de rodadas;
- dano médio causado;
- dano médio sofrido.

## Exemplo de JSON

Os relatórios de batalha incluem metadados da partida, estratégias, contagem de
recrutamentos, dano e eventos estruturados:

```json
{
  "winner": "Blue",
  "rounds_played": 12,
  "strategies": {
    "player_one": "balanced",
    "player_two": "random"
  },
  "units_recruited": {
    "player_one": 8,
    "player_two": 7
  },
  "damage": {
    "player_one": {
      "dealt": 42,
      "received": 31
    }
  },
  "events": [
    {
      "type": "unit_attack",
      "round": 3,
      "actor": "Archer 1",
      "target": "Guardian 1",
      "amount": 1
    }
  ]
}
```

Os relatórios de torneio incluem `standings` por estratégia e o detalhe dos
confrontos.

## Arquitetura

```text
.github/workflows/
  tests.yml
  pages.yml
battle_simulator/
  __main__.py
  cli.py
  engine.py
  models.py
  strategies.py
  tournament.py
web/
  index.html
  style.css
  app.js
  playground.py
docs/
  academic_context.md
  balance_notes.md
  initial_audit.md
  roadmap.md
legacy/
  projeto.py
  projeto2.0.py
  projeto2.1.py
  projeto3.0.py
tests/
  test_engine.py
pyproject.toml
```

Responsabilidades principais:

- `models.py`: bases, unidades, linhas, papéis e efeitos.
- `engine.py`: regras de batalha, turnos, seleção de alvo, alcance, efeitos e
  eventos.
- `strategies.py`: estratégias automatizadas.
- `tournament.py`: confrontos round-robin e métricas agregadas.
- `cli.py`: interface de linha de comando e exportação JSON.
- `web/`: interface no navegador (Pyodide) — apresentação apenas, sem regras de
  jogo.
- `tests/`: cobertura de regressão das regras principais.

Notas adicionais ficam em `docs/`, incluindo o resumo de balanceamento e o
roadmap técnico.

## Histórico

A versão original era um pequeno exercício acadêmico de POO com scripts
interativos. Esses arquivos estão preservados em `legacy/` como referência
histórica. O repositório atual é um simulador redesenhado, com estrutura de
pacote, testes automatizados, CI e regras de batalha mais ricas.

## Limitações atuais

- O balanceamento é intencionalmente leve e ainda heurístico.
- O campo de batalha tem duas linhas, não um grid completo.
- As estratégias são heurísticas determinísticas, não agentes de aprendizado de
  máquina.
- O modo interativo é secundário em relação às simulações automáticas.

## Próximos passos

- Exportar logs completos de eventos em JSON Lines.
- Adicionar métricas de eficiência de recursos e sobreviventes.
- Melhorar a ergonomia do modo interativo.
- Adicionar visualização de rodada a rodada na interface web.
