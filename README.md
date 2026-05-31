# Tactical Auto-Battler Simulator

Mini tactical auto-battler simulator written in Python.

This repository is a standalone portfolio project. It started from a small
academic OOP exercise and was redesigned into a compact simulation engine with
tactical units, front/back lanes, combat effects, automated strategies and
round-robin tournament reports.

The goal is not to be a full game. The goal is to show clean Python/OOP
architecture, deterministic simulations, test coverage and readable project
structure without external runtime dependencies.

## Concepts

- Python 3.10+.
- Object-oriented design.
- `dataclasses`, `Enum` and small domain classes.
- Battle engine separated from CLI output.
- Tactical unit attributes: attack, defense, HP, speed, range, cost and role.
- Simple `front` / `back` lane model.
- Combat effects: `shield`, `bleed`, `stun` and `heal`.
- Automated bot strategies.
- Round-robin tournaments.
- Structured JSON reports.
- Tests with `unittest`.
- GitHub Actions validation.

## Usage

Run commands from the repository root.

Automatic simulation:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11
```

Short automatic simulation:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet
```

Automatic simulation with JSON report:

```bash
python -m battle_simulator --mode auto --rounds 20 --seed 11 --quiet --report-json reports/battle.json
```

Round-robin tournament:

```bash
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --seed 11 --report-json reports/tournament-balance.json
```

Interactive mode:

```bash
python -m battle_simulator --mode interactive --rounds 20
```

Run tests:

```bash
python -m unittest discover -s tests
```

Compile modules:

```bash
python -m compileall battle_simulator tests
```

## Battle Model

Each unit has:

- `attack`: base damage.
- `defense`: damage reduction, with minimum damage preserved.
- `max_hp` and `current_hp`: maximum and current health.
- `speed`: action priority inside each round.
- `range`: whether the unit can reach the front or back lane.
- `cost`: recruitment cost.
- `role`: tactical role used by the engine and strategies.

The battlefield intentionally uses only two lanes:

- `front`: easier to reach and usually occupied by durable units.
- `back`: safer position for ranged and support units.

This keeps the project small while still demonstrating positioning, targeting
and range rules.

## Units

- `Soldier`: cheap frontline unit.
- `Archer`: ranged backline attacker that applies `bleed`.
- `Guardian`: defensive frontline unit that can apply `shield`.
- `Medic`: support unit that heals damaged allies.
- `Tank`: expensive frontline unit with strong attack and `stun`.

## Strategies

- `AggressiveBot`: buys fewer units per round, focuses reachable weak targets
  and tries to end fights quickly.
- `BalancedBot`: builds a mixed composition with frontline and backline units.
- `DefensiveBot`: favors durable units and protection.
- `EconomyBot`: delays some spending to buy stronger turns later.
- `RandomBot`: uses seeded randomness.

Tournament output includes:

- wins;
- losses;
- draws;
- win rate;
- draw rate;
- average rounds;
- average damage dealt;
- average damage taken.

## JSON Example

Battle reports include match metadata, strategies, recruitment counts, damage
and structured events:

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

Tournament reports include `standings` per strategy and detailed matchup
results.

## Architecture

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

Main responsibilities:

- `models.py`: bases, units, lanes, roles and effects.
- `engine.py`: battle rules, turns, targeting, range, effects and events.
- `strategies.py`: automated bot strategies.
- `tournament.py`: round-robin matchups and aggregate metrics.
- `cli.py`: command-line interface and JSON export.
- `tests/`: regression coverage for the core rules.

## History

The original version was a small academic OOP exercise with interactive scripts.
Those files are preserved in `legacy/` as historical reference. The current
standalone repository is a redesigned simulator with a proper package structure,
automated tests, CI and richer battle rules.

## Current Limitations

- Balance is intentionally lightweight and still heuristic.
- The battlefield has two lanes, not a full grid.
- Bot strategies are deterministic heuristics, not machine learning agents.
- Strategy selection via CLI is still a planned improvement.
- Interactive mode is secondary to automated simulations.

## Next Steps

- Allow choosing strategies from CLI arguments.
- Export complete event logs as JSON Lines.
- Add resource-efficiency and survivor metrics.
- Improve interactive mode ergonomics.
- Add a simple visualization without mandatory external dependencies.
