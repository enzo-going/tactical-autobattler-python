# Battle Simulator Python POO

Simulador de batalha por turnos escrito em Python, com foco em Programação
Orientada a Objetos, separação de responsabilidades e testes automatizados.

Este repositório é um fork de um trabalho acadêmico de POO. A versão original
foi preservada em `legacy/`, enquanto a implementação principal foi
reorganizada como um pacote Python mais limpo e pronto para portfólio.

## Tecnologias e conceitos

- Python 3.10+.
- Programação Orientada a Objetos.
- Classes abstratas e herança.
- `dataclasses` e `Enum`.
- Engine desacoplada da interface de console.
- Estratégias automatizadas para simulação.
- Testes com `unittest`.
- GitHub Actions para validação contínua.
- Exportação de relatórios em JSON.

O projeto não exige dependências externas obrigatórias.

## Como rodar

Execute os comandos a partir da raiz do repositório.

Simulação automática:

```bash
python -m battle_simulator --mode auto --rounds 30 --seed 7
```

Simulação automática com relatório JSON:

```bash
python -m battle_simulator --mode auto --rounds 30 --quiet --report-json reports/battle.json
```

Modo torneio, comparando estratégias em vários confrontos:

```bash
python -m battle_simulator --mode tournament --simulations 100 --rounds 30 --report-json reports/tournament.json
```

Modo interativo:

```bash
python -m battle_simulator --mode interactive --rounds 30
```

Rodar testes:

```bash
python -m unittest discover -s tests
```

Compilar módulos Python:

```bash
python -m compileall battle_simulator tests
```

## Tropas

- `Soldier`: unidade barata, frágil e de baixo dano.
- `Archer`: unidade ofensiva de dano médio e baixa vida.
- `Guardian`: unidade defensiva, resistente e de baixo dano.
- `Tank`: unidade cara, resistente e com maior dano.

## Estratégias

- `BalancedBot`: monta um exército misto.
- `RandomBot`: recruta e escolhe alvos com aleatoriedade controlada por seed.
- `AggressiveBot`: prioriza unidades ofensivas e foca alvos mais fracos.

O modo `tournament` executa confrontos entre estratégias e calcula vitórias,
derrotas, empates e média de rounds por confronto.

## Estrutura do projeto

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

## O que foi refatorado

A versão acadêmica original era composta por scripts interativos na raiz do
repositório. A versão atual preserva esses arquivos em `legacy/` e move a
implementação principal para um pacote testável.

Principais mudanças:

- separação entre modelos de domínio, engine de batalha, CLI, estratégias e
  torneios;
- remoção da dependência direta de `input()` e `print()` nas regras centrais;
- criação de testes automatizados para regras de batalha;
- adição de simulações automáticas e torneios comparativos;
- geração opcional de relatórios JSON;
- workflow de CI para rodar testes e compilação.

## Próximos passos

- Melhorar o balanceamento com métricas de várias seeds.
- Adicionar novas estratégias e permitir seleção via CLI.
- Exportar o log completo de eventos em JSON Lines.
- Melhorar o modo interativo.
- Avaliar uma interface visual simples sem comprometer a simplicidade do
  projeto.
