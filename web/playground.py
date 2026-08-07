"""Ponte entre o pacote ``battle_simulator`` e a interface web.

Este modulo roda dentro do Pyodide, no navegador. Ele nao contem regras de
jogo: apenas chama o mesmo codigo usado pela CLI e devolve JSON para o
JavaScript da pagina. Assim a interface web e a linha de comando nunca
divergem.
"""

from __future__ import annotations

import json

from battle_simulator.cli import _build_report
from battle_simulator.engine import BattleEngine
from battle_simulator.models import Base, TroopFactory, TroopKind
from battle_simulator.tournament import DEFAULT_STRATEGIES, STRATEGIES, run_tournament


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

    return json.dumps(
        {
            "strategies": sorted(STRATEGIES),
            "default_strategies": list(DEFAULT_STRATEGIES),
            "base_health": Base(name="preview").health,
            "units": units,
        }
    )


def battle(strategy_one: str, strategy_two: str, rounds: int, seed: int) -> str:
    """Roda uma batalha e devolve o mesmo relatorio de ``--report-json``."""
    engine = BattleEngine()
    result = engine.run(
        STRATEGIES[strategy_one](seed),
        STRATEGIES[strategy_two](seed),
        max_rounds=rounds,
    )
    return json.dumps(_build_report(engine, result))


def tournament(strategies: str, simulations: int, rounds: int, seed: int) -> str:
    """Roda um torneio round-robin a partir de nomes separados por virgula."""
    selected = tuple(name.strip() for name in strategies.split(",") if name.strip())
    summary = run_tournament(simulations, rounds, seed=seed, strategies=selected)
    return json.dumps(summary.to_dict())
