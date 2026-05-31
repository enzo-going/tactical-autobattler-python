# Tactical Auto-Battler Simulator

Mini simulador tático de batalhas automáticas em Python.

O projeto nasceu como fork de um trabalho acadêmico de Programação Orientada a
Objetos. A versão original foi preservada em `legacy/`; a implementação atual
foi redesenhada como uma pequena engine de simulação com unidades, lanes,
efeitos de combate, estratégias automatizadas e torneios comparativos.

O objetivo não é criar um jogo completo, mas demonstrar arquitetura Python/POO
limpa em um projeto de portfólio.

## Conceitos usados

- Python 3.10+.
- Programação Orientada a Objetos.
- `dataclasses`, `Enum` e classes especializadas.
- Engine desacoplada da interface de console.
- Unidades com atributos táticos: ataque, defesa, vida, velocidade, alcance,
  custo e papel.
- Campo simples com `front` e `back lane`.
- Efeitos de combate: `shield`, `bleed`, `stun` e `heal`.
- Estratégias automatizadas.
- Torneio round-robin.
- Relatórios JSON estruturados.
- Testes com `unittest`.
- GitHub Actions para validação contínua.

O projeto não exige dependências externas obrigatórias.

## Como rodar

Execute os comandos a partir da raiz do repositório.

Simulação automática:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11
```

Simulação automática com saída curta:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet
```

Simulação automática com relatório JSON:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet --report-json reports/battle.json
```

Torneio round-robin:

```bash
python -m battle_simulator --mode tournament --simulations 10 --rounds 20 --seed 11 --report-json reports/tournament.json
```

Modo interativo:

```bash
python -m battle_simulator --mode interactive --rounds 20
```

Rodar testes:

```bash
python -m unittest discover -s tests
```

Compilar módulos Python:

```bash
python -m compileall battle_simulator tests
```

## Modelo de batalha

Cada unidade possui:

- `attack`: dano base.
- `defense`: redução de dano recebido, com dano mínimo.
- `max_hp` e `current_hp`: vida máxima e vida atual.
- `speed`: prioridade de ação dentro da rodada.
- `range`: alcance para atingir `front` ou `back lane`.
- `cost`: custo de recrutamento.
- `role`: função tática da unidade.

O campo usa duas posições simples:

- `front`: linha de frente, mais fácil de alcançar.
- `back`: retaguarda, exige maior alcance.

Essa escolha evita um grid 2D complexo, mas já permite testar alcance,
posicionamento e papéis diferentes.

## Unidades

- `Soldier`: unidade barata de linha de frente.
- `Archer`: atacante de retaguarda com alcance maior e efeito de `bleed`.
- `Guardian`: defensor resistente que aplica `shield`.
- `Medic`: suporte de retaguarda que cura aliados feridos.
- `Tank`: unidade cara de linha de frente, com ataque forte e `stun`.

## Estratégias

- `AggressiveBot`: prioriza dano, tanques e arqueiros.
- `BalancedBot`: tenta montar uma composição mista.
- `DefensiveBot`: prioriza guardiões, suporte e sobrevivência.
- `EconomyBot`: economiza recursos antes de comprar unidades mais caras.
- `RandomBot`: usa aleatoriedade controlada por seed.

O modo `tournament` executa confrontos round-robin entre estratégias e calcula:

- vitórias;
- derrotas;
- empates;
- taxa de vitória;
- média de rounds;
- dano médio causado;
- dano médio recebido.

## Exemplo de JSON

Relatórios de batalha incluem metadados da partida, estratégias, unidades
recrutadas, dano e eventos relevantes:

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

Relatórios de torneio incluem `standings` por estratégia e resultados por
confronto.

## Arquitetura

```text
.github/workflows/
  tests.yml
battle_simulator/
  __main__.py
  cli.py
  engine.py
  models.py
  strategies.py
  tournament.py
docs/
  academic_context.md
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

- `models.py`: unidades, bases, lanes, papéis e efeitos.
- `engine.py`: regras de batalha, turnos, alcance, efeitos e eventos.
- `strategies.py`: bots automatizados.
- `tournament.py`: round-robin e métricas agregadas.
- `cli.py`: interface de linha de comando e exportação JSON.
- `tests/`: validação das regras principais.

## Relação com a versão original

A versão acadêmica original era composta por scripts interativos na raiz do
repositório. Ela continua em `legacy/` para preservar o histórico do fork.

A versão atual refatora o projeto para:

- separar domínio, engine, CLI, estratégias e torneios;
- remover a dependência de `input()` e `print()` nas regras centrais;
- permitir simulações automatizadas e reproduzíveis;
- gerar relatórios estruturados;
- validar regras com testes;
- manter o projeto simples o suficiente para estudo e portfólio.

## Limitações

- O balanceamento ainda é experimental.
- O campo usa apenas duas lanes, não um mapa completo.
- Estratégias são heurísticas simples, não IA avançada.
- O modo interativo ainda é secundário em relação ao modo automático.

## Próximos passos

- Permitir escolher estratégias pela CLI.
- Exportar eventos completos em JSON Lines.
- Adicionar métricas de sobrevivência e uso de recursos.
- Melhorar a ergonomia do modo interativo.
- Criar uma visualização simples sem adicionar dependências obrigatórias.
