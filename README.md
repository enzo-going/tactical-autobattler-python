# Battle Simulator Python POO

Simulador de batalha em Python com foco em Programação Orientada a Objetos.

O projeto nasceu como um trabalho acadêmico simples e este fork está sendo
evoluído para uma base mais organizada, testável e apresentável como portfólio.
Os arquivos `projeto*.py` foram preservados como histórico da implementação
original.

## O que existe agora

- Pacote Python em `battle_simulator/`.
- Modelo de domínio separado da interface de console.
- Bases com vida, recursos e renda por rodada.
- Tropas com custo, vida e dano.
- Dois tipos de tropa:
  - `Soldier`: barato, frágil e com baixo dano.
  - `Tank`: caro, resistente e com dano maior.
- Engine de batalha por turnos.
- Bots para simulação automática.
- CLI com modo automático e modo interativo.
- Relatório JSON para análise posterior.
- Testes automatizados com `unittest`.

## Como executar

Modo automático:

```bash
python -m battle_simulator --mode auto --rounds 30 --seed 7
```

Gerar relatório JSON:

```bash
python -m battle_simulator --mode auto --rounds 30 --quiet --report-json reports/battle.json
```

Modo interativo:

```bash
python -m battle_simulator --mode interactive --rounds 30
```

Rodar testes:

```bash
python -m unittest discover -s tests
```

## Estrutura

```text
battle_simulator/
  __main__.py
  cli.py
  engine.py
  models.py
  strategies.py
tests/
  test_engine.py
docs/
  academic_context.md
  initial_audit.md
projeto*.py
```

## Direção técnica

O objetivo deste fork é transformar o script original em um simulador real,
mantendo o valor didático de POO:

- classes pequenas e com responsabilidade clara;
- regras de jogo testáveis sem depender de `input()` e `print()`;
- interface de console desacoplada da engine;
- espaço para novas tropas, estratégias, mapas e balanceamento;
- evolução incremental com commits pequenos.

## Próximos passos sugeridos

- Adicionar novas unidades com papéis diferentes.
- Criar sistema de habilidades especiais.
- Persistir histórico das batalhas em JSON.
- Criar relatório de estatísticas por simulação.
- Adicionar interface visual simples.
