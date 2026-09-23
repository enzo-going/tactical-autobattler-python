# Médico: triagem

Até a 0.8, o Médico curava 2 de vida em um aliado e depois recarregava uma
rodada. Em 8.000 exércitos sorteados (teto 8, 20 rodadas, método em
[Ritmo](ritmo.md)), o lado que investia pelo menos 15 pontos percentuais a mais
no Médico do que o rival vencia **18,1%** das partidas: a pior compra do jogo,
em qualquer composição.

A causa não era o preço. A política de alvo concentra o dano no inimigo mais
fraco, então uma tropa ferida costuma cair na ação seguinte. Curar pouco, uma
vez a cada duas rodadas, não chega a tempo.

## O que foi medido

Todas as variantes sobre as regras da 0.8.0, com os mesmos 8.000 exércitos.
"Distância" é a diferença entre a melhor e a pior unidade nessa mesma métrica.

| Função do Médico | Médico | Tanque | Distância | Fortes destruídos |
| --- | ---: | ---: | ---: | ---: |
| 0.8: cura 2 em um aliado, recarrega | 18,1% | 85,3% | 67,2 | 50,8% |
| Cura 1 em todos os feridos, recarrega | 12,8% | 84,4% | 71,6 | 54,7% |
| Cura 2 em todos os feridos, recarrega | 18,8% | 85,6% | 66,8 | 50,6% |
| Cura 2 na fileira mais ferida, recarrega | 18,4% | 85,5% | 67,1 | 50,6% |
| Cura 1 em todos, sem recarga | 19,4% | 85,8% | 66,4 | 48,6% |
| Cura 3 em um, recarrega, estanca | 26,9% | 86,7% | 59,8 | 47,0% |
| Cura 2 em um, sem recarga, estanca | 38,4% | 86,3% | 59,7 | 43,0% |
| Cura 2 em um, sem recarga, estanca e desperta | 39,2% | 84,9% | 58,4 | 42,1% |
| Cura 3 em um, sem recarga | 39,3% | 85,1% | 60,1 | 42,4% |
| Cura 3 em um, sem recarga, estanca | 43,6% | 84,6% | 57,9 | 41,3% |
| **Cura 3 em um, sem recarga, estanca e desperta** | **44,6%** | **82,9%** | **56,1** | **40,6%** |

Curar em área rende menos que curar um: com o dano concentrado, raramente há
vários feridos vivos ao mesmo tempo. O que decide é salvar uma tropa por vez,
todas as rodadas.

## A regra

**Triagem:** o Médico trata um aliado por ação, sem recarga. Cura 3, estanca o
sangramento e desfaz o atordoamento — as armas do Arqueiro e do Tanque. Um
aliado sangrando ou atordoado é alvo mesmo com a vida cheia; escudo não conta.

A regra mora em `models.py` (`needs_triage`, `triage`, `triage_preview`) e vale
igual no motor automático e na sessão interativa. O evento `heal` leva
`metadata.cleansed`, e o replay remove esses efeitos. Identificadores:
`tactical-v5` e `auto-v4`.

Na sessão, o atordoamento pendente continua sendo consumido no início do
combate. A triagem desfaz o que cai durante a rodada numa tropa que já agiu —
é o que tiraria a ação dela na rodada seguinte.

## Resultado

| Exércitos sorteados, teto 8, 20 rodadas | 0.8.0 | 0.9.0 |
| --- | ---: | ---: |
| Médico | 18,1% | **44,6%** |
| Tanque | 85,3% | 82,9% |
| Guardião | 73,8% | 65,3% |
| Soldado | 52,0% | 45,9% |
| Arqueiro | 41,8% | 35,7% |
| Lanceiro | 32,1% | 26,8% |
| Distância entre a melhor e a pior | 67,2 | **56,1** |
| Fortes destruídos | 50,8% | 40,6% |
| Média de rodadas | 16,53 | 17,24 |

Na [medição interativa](gameplay.md) (60 sessões, limite de 12 rodadas), o
jogador programado, cuja composição mista inclui um Médico, passa de 25 para 35
vitórias; as esperas do rival caem de 104 para 27, porque o Médico dele não
recarrega mais. Partidas no limite: 31 para 32.

No torneio de bots o Equilibrado sobe de 37,5% para 75,0% e o Defensivo cai de
60,0% para 34,2%. Os bots são determinísticos — cada confronto tem uma ou duas
partidas distintas —, então isso descreve essas partidas, não o equilíbrio.

## O custo

**Curar prolonga o combate.** Fortes destruídos caem de 50,8% para 40,6% das
partidas: a triagem devolve parte do que a [linha rompida](ritmo.md) tinha
ganhado. É inerente a um curador que funciona; um Médico que não atrasa nada
também não salva ninguém.

**O Tanque continua dominante** (82,9%). A triagem responde ao atordoamento,
mas o golpe pesado ainda decide. Esse é o próximo ajuste de equilíbrio.

A medição usa uma política de alvo fixa e mede correlação entre composição e
vitória. Ela não substitui partidas com pessoas.
