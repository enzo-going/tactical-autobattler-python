# Tactical Auto-Battler Simulator

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![OOP](https://img.shields.io/badge/OOP-Design-blueviolet?style=flat)
![Tests](https://img.shields.io/badge/Tests-unittest-green?style=flat)
![Dependencies](https://img.shields.io/badge/Dependencies-none-brightgreen?style=flat)

Simulador tático auto-battler em Python puro, focado em demonstrar arquitetura OOP limpa. Sem dependências externas em runtime.

---

## Mecânicas

**5 tipos de unidade:** Soldier, Archer, Guardian, Medic, Tank — cada uma com ataque, defesa, HP, velocidade, alcance e custo.

**4 efeitos de combate:** Shield, Bleed, Stun, Heal.

**2 lanes de posicionamento:** front e back — a posição afeta quem pode atacar quem.

**5 estratégias de bot:**

| Estratégia | Comportamento |
|---|---|
| Aggressive | Prioriza vitória rápida, unidades de alto dano |
| Balanced | Composição mista |
| Defensive | Foco em durabilidade |
| Economy | Gasto tardio, acúmulo de recursos |
| Random | Seleção aleatória |

---

## Modo torneio

Confrontos espelhados para eliminar viés de ordem — cada par de estratégias joga em ambas as posições e os pontos são acumulados.

---

## Como executar

```bash
git clone https://github.com/enzo-going/tactical-autobattler-python.git
cd tactical-autobattler-python
python main.py --mode auto --rounds 20
python main.py --mode tournament --simulations 20
python main.py --mode auto --export results.json
```

---

## Saída

Relatórios exportados em JSON com metadados da partida, estatísticas de recrutamento, dano total e log de eventos.

---

## Testes

```bash
python -m unittest discover tests/
```

Cobertura via `unittest` com validação no CI (GitHub Actions).
