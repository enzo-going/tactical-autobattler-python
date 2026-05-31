# Roadmap técnico

Este fork deve evoluir em microblocos, preservando o histórico acadêmico e
melhorando a qualidade de engenharia.

## Concluído no primeiro ciclo

- Separação entre domínio, engine, estratégias e CLI.
- Criação de pacote Python executável com `python -m battle_simulator`.
- Testes automatizados para regras essenciais.
- Simulação automática com bots.
- Relatório JSON opcional.
- Modo torneio para comparação inicial de estratégias.
- README reescrito com instruções atuais.

## Próximos ciclos

1. Balanceamento de jogo
   - Definir métricas: taxa de vitória, duração média e recursos não usados.
   - Expandir o modo torneio com mais estratégias.
   - Ajustar custo, vida, dano e renda com base nessas métricas.

2. Novas unidades
   - Unidade anti-tanque.
   - Médico ou engenheiro de reparo.
   - Artilharia com alto dano e baixa vida.

3. Persistência e análise
   - Exportar eventos completos em JSON Lines.
   - Criar agregador de estatísticas.
   - Comparar estratégias.

4. Interface
   - Melhorar modo interativo.
   - Criar interface textual mais clara.
   - Avaliar uma interface web simples no futuro.

## Critério de qualidade

Cada ciclo deve manter:

- testes passando;
- regras de jogo isoladas da interface;
- comandos documentados;
- commits pequenos e descritivos.
