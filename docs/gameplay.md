# Jogabilidade: preparação, informação e resposta rival

A 0.7 prioriza decisões do jogador. Na 0.6, uma compra equivocada não podia ser
devolvida, corrigir a formação custava uma ação de combate e o alvo só mostrava
a vida atual. O rival também esperava sempre que não podia atacar ou curar.

## O que mudou

Na preparação, selecionar uma tropa abre seus controles junto ao campo.
Reposicionar é gratuito; recrutas daquela preparação podem ser devolvidos pelo
custo pago. Isso permite experimentar combinações com os mesmos suprimentos.
Ao começar o combate, a devolução é bloqueada e mover volta a custar uma ação.
Veteranos podem trocar de linha, mas preservam vida, efeitos e recarga: não há
venda de feridos para recomprar tropas curadas. IDs nunca são reutilizados.

No combate, cada alvo mostra a consequência imediata do golpe: dano, vida
restante, eliminação e efeitos. A cura mostra o valor efetivo, limitado à vida
máxima. O mesmo cálculo Python que resolve dano produz a previsão, sem gastar
escudo. Ela não inclui a resposta rival, sangramento futuro ou uma rodada inteira.

O rival mantém a ordem por velocidade, mas reconhece golpes finais antes de
curar, protege um aliado quando um escudo impede uma ameaça letal pendente e
avança quando uma arma pronta não alcança ninguém. Durante a recarga, protege
a si mesmo contra ameaças e sangramento, evitando escudo redundante. Todos os
estilos ainda compartilham essa política de combate; suas compras são diferentes.

## Comparação controlada

`tools/measure_gameplay.py` executa **sessões interativas**, não torneios do
laboratório. Usa cinco oponentes, três compras programadas (soldados, arqueiros
ou composição mista), seeds 0, 1, 11 e 12, limite de 12 rodadas. Total: 60
partidas por versão. A política do jogador e os parâmetros são idênticos.
Ela não usa devoluções nem formação grátis, isolando a mudança de decisões rivais.

```bash
python tools/measure_gameplay.py --output _site/gameplay-after.json
# Extraia battle_simulator da tag v0.6.0 em uma pasta separada para comparar:
python tools/measure_gameplay.py --source _site/gameplay-baseline --output _site/gameplay-before.json
```

| Medida | 0.6.0 | 0.7.0 |
| --- | ---: | ---: |
| Vitórias do jogador programado | 30 | 30 |
| Vitórias rivais | 28 | 30 |
| Empates | 2 | 0 |
| Média de rodadas | 9,82 | 9,88 |
| Partidas no limite de 12 rodadas | 34 | 34 |
| Ordens rivais de espera | 198 | 107 |
| Ordens rivais de proteção | 0 | 279 |

As formações compradas pelos bots nessa amostra não exigiram avanço: essa
situação é coberta por teste dirigido de tropa de alcance 1 atrás da vanguarda.
Testes também cobrem defesa que evita morte, golpe excessivo que o escudo não
salvaria, recarga, previsão com escudo e reprodução dos novos comandos.

A amostra sugere menos turnos desperdiçados sem alongamento expressivo, mas
não mede diversão nem prova equilíbrio entre estilos. Mais da metade das
partidas ainda chega ao limite. Uma mudança futura de ritmo precisa comparar
renda, reforços e condições de vitória, com partidas humanas além da simulação.

## Próximas melhorias, em ordem

1. **Salvar e retomar:** perder a partida ao recarregar é a maior fricção restante.
2. **Cenários curtos de treino:** objetivos que ensinem alcance, proteção e recarga.
3. **Rivais com estilos de combate distintos:** hoje a diferença principal é a compra.
4. **Ritmo e condições de vitória:** medir confrontos que atingem o limite antes de
   mudar renda ou dano; não presumir que mais unidades resolverá isso.
5. **Campanha e facções:** construir sobre persistência e encontros já interessantes.

Custos, atributos, renda e regras automáticas do laboratório não mudaram nesta etapa.
