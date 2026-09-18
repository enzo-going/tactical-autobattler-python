"""Ponte entre o pacote ``battle_simulator`` e a interface web.

Este modulo roda dentro do Pyodide, no navegador. Nao contem regras de jogo:
delega ao motor automatico (compartilhado com a CLI) ou a TacticalSession
(modo interativo web), e devolve JSON para o JavaScript.
"""

from __future__ import annotations

import json

from battle_simulator.cli import _build_report
from battle_simulator.engine import BattleEngine
from battle_simulator.models import Base, TroopFactory, TroopKind
from battle_simulator.tournament import DEFAULT_STRATEGIES, STRATEGIES, run_tournament
from battle_simulator.session import TacticalSession

_session: TacticalSession | None = None


def new_game(opponent: str, seed: int, rounds: int) -> str:
    global _session
    _session = TacticalSession(opponent, seed, rounds)
    return json.dumps(_session.state())


def game_command(payload: str) -> str:
    if _session is None:
        raise ValueError("Inicie uma partida primeiro.")
    return json.dumps(_session.command(json.loads(payload)))


def game_report() -> str:
    if _session is None:
        raise ValueError("Inicie uma partida primeiro.")
    return json.dumps(_session.report())


def catalog() -> str:
    """Estrategias disponiveis e ficha tecnica de cada unidade."""
    factory = TroopFactory()
    units = []
    for kind in TroopKind:
        troop = factory.create(kind)
        units.append(
            {
                "kind": kind.value,
                "role": troop.role.value,
                "lane": troop.lane.value,
                "max_hp": troop.max_hp,
                "attack": troop.attack,
                "defense": troop.defense,
                "speed": troop.speed,
                "range": troop.range,
                "cost": troop.cost,
            }
        )

    base = Base(name="preview")
    return json.dumps(
        {
            "strategies": sorted(STRATEGIES),
            "default_strategies": list(DEFAULT_STRATEGIES),
            "base_health": base.health,
            "base_resources": base.resources,
            "base_income": base.resource_income,
            "units": units,
        }
    )


def battle(strategy_one: str, strategy_two: str, rounds: int, seed: int) -> str:
    """Roda uma batalha e devolve o mesmo relatorio de ``--report-json``."""
    engine = BattleEngine(initiative_seed=seed)
    result = engine.run(
        STRATEGIES[strategy_one](seed),
        STRATEGIES[strategy_two](seed),
        max_rounds=rounds,
    )
    return json.dumps(_build_report(engine, result))


def tournament(strategies: str, simulations: int, rounds: int, seeds: str) -> str:
    """Roda um torneio round-robin a partir de nomes separados por virgula."""
    selected = tuple(name.strip() for name in strategies.split(",") if name.strip())
    selected_seeds = tuple(int(seed.strip()) for seed in seeds.split(",") if seed.strip())
    summary = run_tournament(simulations, rounds, strategies=selected, seeds=selected_seeds)
    return json.dumps(summary.to_dict())
