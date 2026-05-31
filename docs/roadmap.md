# Roadmap técnico

Este fork evoluiu de um script acadêmico de POO para um mini tactical
auto-battler simulator. A prioridade continua sendo clareza de arquitetura,
testabilidade e simplicidade suficiente para portfólio.

## Concluído

- Separação entre domínio, engine, estratégias, torneios e CLI.
- Criação de pacote Python executável com `python -m battle_simulator`.
- Preservação dos scripts acadêmicos originais em `legacy/`.
- Testes automatizados para regras essenciais.
- GitHub Actions para testes e compilação.
- Modelo tático com ataque, defesa, vida, velocidade, alcance, custo e papel.
- Campo simples com `front` e `back lane`.
- Efeitos de combate: `shield`, `bleed`, `stun` e `heal`.
- Estratégias com estilos distintos: agressiva, balanceada, defensiva,
  econômica e aleatória.
- Relatório JSON estruturado com eventos e estatísticas.
- Torneio round-robin com métricas por estratégia.
- README reescrito com a nova identidade do projeto.

## Próximos ciclos

1. Balanceamento de jogo
   - Rodar torneios com mais seeds.
   - Observar taxa de vitória, duração média, dano e empates.
   - Ajustar custo, vida, dano, defesa e renda com base nessas métricas.

2. CLI
   - Permitir selecionar estratégias por argumento.
   - Permitir selecionar lista de estratégias para torneio.
   - Melhorar o modo interativo sem misturar lógica de regra na CLI.

3. Persistência e análise
   - Exportar eventos completos em JSON Lines.
   - Criar relatório agregado com recursos finais e tropas sobreviventes.
   - Adicionar snapshots por rodada.

4. Interface
   - Criar uma visualização textual mais clara do campo.
   - Avaliar interface visual simples no futuro.

## Critério de qualidade

Cada ciclo deve manter:

- testes passando;
- regras de jogo isoladas da interface;
- comandos documentados;
- sem dependências externas obrigatórias;
- commits pequenos e descritivos.
