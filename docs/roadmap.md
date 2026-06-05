# Technical Roadmap

This project has evolved from a small academic OOP exercise into a standalone
tactical auto-battler simulator. The current priority is to keep the project
small, readable and useful as a Python portfolio piece.

## Completed

- Package structure with `python -m battle_simulator`.
- CLI for automatic simulations, interactive play and tournaments.
- Strategy selection through CLI arguments.
- Tactical model with attack, defense, HP, speed, range, cost and role.
- Simple front/back lane system.
- Combat effects: `shield`, `bleed`, `stun` and `heal`.
- Automated strategies with distinct styles.
- Mirrored round-robin tournament to reduce player-order bias.
- Structured JSON reports.
- Unit tests for core rules, strategies, reports and tournament behavior.
- GitHub Actions workflow for tests and compilation.
- Standalone README and project metadata.

## Current Quality Bar

Every meaningful change should keep:

- unit tests passing;
- `compileall` passing;
- no mandatory external runtime dependencies;
- CLI commands documented;
- battle rules isolated from presentation code;
- generated reports ignored by Git.

## Next Improvements

1. Balance analysis
   - Run tournaments across several seed groups.
   - Track whether a strategy becomes dominant over time.
   - Tune strategy heuristics before changing unit stats.

2. Reporting
   - Add optional JSON Lines event export.
   - Add per-round snapshots.
   - Track resource efficiency and surviving unit value.

3. CLI polish
   - Add a compact `--summary-only` report option.
   - Improve interactive prompts and target selection.

4. Presentation
   - Add a small docs page explaining the battle loop.
   - Add example report files under a versioned `examples/` directory.
