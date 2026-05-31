# Roadmap técnico

Este fork deve evoluir em microblocos, preservando o histórico acadêmico e
melhorando a qualidade de engenharia sem transformar o simulador em algo
desnecessariamente complexo.

## Concluído

- Separação entre domínio, engine, estratégias, torneios e CLI.
- Criação de pacote Python executável com `python -m battle_simulator`.
- Preservação dos scripts acadêmicos originais em `legacy/`.
- Testes automatizados para regras essenciais.
- GitHub Actions para testes e compilação.
- Simulação automática com bots.
- Tropas adicionais: `Archer` e `Guardian`.
- Estratégia adicional: `AggressiveBot`.
- Relatório JSON opcional.
- Modo torneio com métricas por confronto.
- README reescrito com foco de portfólio.

## Próximos ciclos

1. Balanceamento de jogo
   - Rodar torneios com mais seeds.
   - Observar taxa de vitória, duração média e empates.
   - Ajustar custo, vida, dano e renda com base nessas métricas.

2. Estratégias
   - Permitir seleção de estratégias via CLI.
   - Adicionar uma estratégia defensiva explícita.
   - Comparar estratégias contra a mesma ordem de seeds.

3. Persistência e análise
   - Exportar eventos completos em JSON Lines.
   - Criar relatório agregado com mais métricas.
   - Medir recursos finais e tropas sobreviventes.

4. Interface
   - Melhorar prompts do modo interativo.
   - Criar uma interface textual mais organizada.
   - Avaliar interface visual simples no futuro.

## Critério de qualidade

Cada ciclo deve manter:

- testes passando;
- regras de jogo isoladas da interface;
- comandos documentados;
- sem dependências externas obrigatórias;
- commits pequenos e descritivos.
