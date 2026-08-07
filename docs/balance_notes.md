# Notas de balanceamento

O formato atual de torneio usa confrontos round-robin espelhados. Cada par de
estratégias joga nas duas ordens de jogador, o que torna a comparação entre
estratégias determinísticas menos sensível à vantagem de quem começa.

## Identidade atual das estratégias

- `AggressiveBot`: pressão inicial, alvos fracos ao alcance, partidas rápidas.
- `BalancedBot`: composição mista entre linha de frente e fundo.
- `DefensiveBot`: abertura resistente, complemento de alcance, cura só depois de
  levar dano.
- `EconomyBot`: abertura mais lenta, turnos fortes mais tarde.
- `RandomBot`: baseline estocástico com seed.

## Última execução de referência

Comando:

```bash
python -m battle_simulator --mode tournament --simulations 20 --rounds 30 --seed 11 --report-json reports/tournament-final-balanced.json
```

Classificação observada:

```text
aggressive: 80V/40D/0E, taxa de vitória 0.667
balanced:   60V/60D/0E, taxa de vitória 0.500
economy:    60V/60D/0E, taxa de vitória 0.500
defensive:  40V/80D/0E, taxa de vitória 0.333
```

O mesmo resultado pode ser reproduzido na
[interface web](https://enzo-going.github.io/tactical-autobattler-python/), aba
**Torneio**, com 20 simulações, 30 rodadas e seed 11.

## Interpretação

O balanceamento não é perfeitamente simétrico, mas cada estratégia
determinística tem ao menos um confronto favorável relevante e os torneios
evitam sequências longas de empate. É um alvo razoável de balanceamento para o
escopo atual de portfólio.

## Ponto em aberto

Na tabela de confrontos, o lado que age primeiro vence a grande maioria dos
pares. O round-robin espelhado compensa isso na classificação agregada, mas a
vantagem de iniciativa em si ainda não foi tratada nas regras — é o próximo item
natural da análise de balanceamento.
