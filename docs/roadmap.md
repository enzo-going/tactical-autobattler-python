# Roadmap técnico

Este projeto evoluiu de um pequeno exercício acadêmico de POO para um simulador
tático auto-battler independente. A prioridade atual é manter o projeto enxuto,
legível e útil como peça de portfólio Python.

## Concluído

- Estrutura de pacote com `python -m battle_simulator`.
- CLI para simulações automáticas, modo interativo e torneios.
- Seleção de estratégia por argumentos da CLI.
- Modelo tático com ataque, defesa, HP, velocidade, alcance, custo e papel.
- Sistema simples de linhas de frente/fundo.
- Efeitos de combate: `shield`, `bleed`, `stun` e `heal`.
- Estratégias automatizadas com estilos distintos.
- Torneio round-robin espelhado para reduzir o viés de ordem de jogador.
- Relatórios JSON estruturados.
- Testes unitários das regras principais, estratégias, relatórios e torneio.
- Workflow do GitHub Actions para testes e compilação.
- README e metadados de projeto independentes.
- Interface web (Pyodide) publicada no GitHub Pages, reaproveitando o mesmo
  pacote Python.

## Barra de qualidade atual

Toda mudança relevante deve manter:

- testes unitários passando;
- `compileall` passando;
- nenhuma dependência externa obrigatória em tempo de execução;
- comandos da CLI documentados;
- regras de batalha isoladas do código de apresentação — incluindo `web/`, que
  só formata resultados;
- relatórios gerados ignorados pelo Git.

## Próximas melhorias

1. Análise de balanceamento
   - Rodar torneios com vários grupos de seed.
   - Acompanhar se alguma estratégia se torna dominante ao longo do tempo.
   - Ajustar as heurísticas antes de mexer nos atributos das unidades.
   - Investigar a vantagem de iniciativa apontada em `balance_notes.md`.

2. Relatórios
   - Exportação opcional de eventos em JSON Lines.
   - Snapshots por rodada.
   - Métricas de eficiência de recursos e valor das unidades sobreviventes.

3. Polimento da CLI
   - Opção compacta `--summary-only`.
   - Melhorar os prompts do modo interativo e a seleção de alvo.

4. Apresentação
   - Visualização rodada a rodada na interface web, consumindo os snapshots.
   - Página de documentação explicando o loop de batalha.
   - Relatórios de exemplo em um diretório `examples/` versionado.
