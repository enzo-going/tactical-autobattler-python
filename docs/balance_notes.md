# Balance Notes

The current tournament format uses mirrored round-robin matchups. Each pair of
strategies plays in both player orders, which makes deterministic strategy
comparison less sensitive to first-player advantage.

## Current Strategy Identity

- `AggressiveBot`: early pressure, reachable weak targets, fast games.
- `BalancedBot`: mixed frontline/backline composition.
- `DefensiveBot`: durable opener, ranged follow-up, healing only after damage.
- `EconomyBot`: slower opening, later power turns.
- `RandomBot`: seeded stochastic baseline.

## Latest Reference Run

Command:

```bash
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --seed 11 --report-json reports/tournament-final-balanced.json
```

Observed standings:

```text
aggressive: 80W/40L/0D, win rate 0.667
balanced:   60W/60L/0D, win rate 0.500
economy:    60W/60L/0D, win rate 0.500
defensive:  40W/80L/0D, win rate 0.333
```

## Interpretation

The balance is not perfectly symmetrical, but each deterministic strategy now
has at least one meaningful winning matchup and tournaments avoid long draw
patterns. This is a reasonable portfolio-level balance target for the current
scope.
