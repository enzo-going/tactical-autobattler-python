# Ritmo: linha rompida e dano excedente

A 0.8 muda como o combate chega ao forte. Até a 0.7, o forte só recebia golpe
quando o outro lado não tinha **nenhuma** tropa viva. Com 6 suprimentos por
rodada e teto de 8 tropas, a linha era sempre reposta: o campo quase nunca
esvaziava e a partida terminava no desempate.

## O problema, medido

Os torneios do laboratório não mostravam isso, por três motivos:

- **Os bots são determinísticos.** Em 6.400 batalhas entre os quatro bots fixos
  houve 29 partidas distintas; a seed só troca quem abre a rodada. Mais
  simulações repetem as mesmas partidas.
- **O motor automático não tem teto de tropas.** O limite de 8 existe na sessão
  interativa; no laboratório os exércitos chegam a dezenas de peças, e um lado
  acaba varrido.
- **O laboratório costuma rodar 30 rodadas**; o jogo usa 20.

Por isso a medição usou **exércitos de composição sorteada**: cada lado recebe
pesos aleatórios (Dirichlet, α = 0,8) sobre os seis tipos de tropa e compra por
eles a cada rodada, com teto de 8 e a mesma política de alvo dos bots
(`_attack_orders`). Foram 8.000 batalhas por versão, de 20 rodadas, com as
mesmas seeds antes e depois: cada batalha compara os mesmos dois exércitos.

## A regra

- **Linha rompida.** Sem ninguém vivo na vanguarda inimiga, a própria vanguarda
  pode golpear o forte. A retaguarda inimiga continua defendendo e segue ao
  alcance da sua retaguarda. No jogo, a vanguarda escolhe entre o forte e os
  alvos que já alcançava; no laboratório, ela vai ao forte.
- **Dano excedente.** O que sobra de um golpe letal, depois de defesa e escudo,
  atravessa até o forte. Um Tanque (ATQ 5) que derruba um Soldado com 1 de vida
  (DEF 1) causa 1 na tropa e 3 no forte.

As duas regras moram em `models.py` (`can_assault_base`, `overflow_damage`) e
valem igual no motor automático e na sessão interativa. O excedente é um
`base_attack` com `metadata.overflow`, e o ataque pela brecha leva
`metadata.line_broken`. Os identificadores passam a `tactical-v4` e `auto-v3`.

## Resultado

| Exércitos sorteados, teto 8, 20 rodadas | 0.7.1 | 0.8.0 |
| --- | ---: | ---: |
| Forte destruído | 9,3% | **50,8%** |
| Decidida no desempate | 90,2% | 49,2% |
| Média de rodadas | 19,42 | 16,53 |
| Quem abre a rodada vence | 49,3% | 50,1% |

A [medição interativa](gameplay.md) (60 sessões, política de jogador fixa,
limite de 12 rodadas) muda pouco: partidas no limite de 34 para 31, média de
9,88 para 9,33 rodadas, e o rival vence 35 em vez de 30. O torneio dos bots no
laboratório fica praticamente igual (agressivo com 87,1% nas duas versões),
porque ali o teto não existe e o campo já esvaziava.

## O que a regra não resolve

**O equilíbrio muda de dono.** Medido pela taxa de vitória do lado que investe
pelo menos 15 pontos percentuais a mais em uma unidade do que o rival:

| Unidade | 0.7.1 | 0.8.0 |
| --- | ---: | ---: |
| Lanceiro | 76,3% | 32,1% |
| Tanque | 65,1% | 85,3% |
| Guardião | 45,2% | 73,8% |
| Arqueiro | 60,1% | 41,8% |
| Soldado | 34,5% | 52,0% |
| Médico | 13,9% | 18,1% |

Antes, a retaguarda cheia de lanceiros dominava. Agora ela deixa a vanguarda
fina e o forte exposto, e quem segura a linha — Tanque e Guardião — passa a
decidir. A regra ganhou o propósito da vanguarda; o próximo ajuste precisa
reduzir a distância entre as unidades, e não só trocar quem lidera.

A 0.9 redesenhou o Médico a partir desta medição: ver [Médico: triagem](triagem.md).

Ajustes só de número não bastaram na simulação: sobre a linha rompida, Tanque
com ATQ 4, Guardião custando 5 ou Médico custando 3 mudaram em menos de 3 pontos
a distância entre a melhor e a pior unidade. O Médico continua a pior compra em
todas as variantes, inclusive sem recarga — o problema é o que ele faz, não o
preço.

A medição usa uma política de alvo fixa e mede correlação entre composição e
vitória. Ela não substitui partidas com pessoas.
