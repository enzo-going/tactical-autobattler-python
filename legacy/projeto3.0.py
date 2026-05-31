from abc import ABC, abstractmethod


class Base:
    __nome: str
    vida: int
    recurso: int


    def __init__(self, nome: str):
        self.__nome = nome
        self.vida = 10
        self.recurso = 10
        #self.recursos.mao_de_obra
        #self.aço
        #self.tugstenio
        #self.combustivel
        #self.aluminio
        #self.borracha




    def receber_dano(self, dano: int):
        self.vida -= dano


    def gastar_recurso(self, modelo: str):
        tropa = None
        if modelo == "1":
            tropa = Soldado()
        elif modelo == "2":
            tropa = Tanque()
       
        if self.recurso >= tropa.recurso:
            self.recurso -= tropa.recurso


    def reset_recurso(self):
        self.recurso += 7


    def get_nome(self):
        return self.__nome


    def __str__(self):
        txt = f"Base ({self.__nome} Vida ({self.vida} Recursos ({self.recurso})))"
        return txt




class Tropas(ABC):
    def __init__(self, nome: str, vida: int, dano: int, recurso: int):
        self.nome = nome
        self.vida = vida
        self.dano = dano
        self.recurso = recurso


    @abstractmethod
    def atirar_base(self, b: Base):
        pass


    @abstractmethod
    def atirar(self, alvo):
        pass


    def receber_dano(self, dano: int):
        self.vida -= dano


    def esta_viva(self):
        return self.vida > 0




class Soldado(Tropas):
    contador = 1


    def __init__(self):
        nome = f"Soldado{Soldado.contador}"
        Soldado.contador += 1
        super().__init__(nome, vida=3, dano=1, recurso = 2)


    def atirar_base(self, b: Base):
        b.receber_dano(self.dano)


    def atirar(self, alvo: Tropas):
        alvo.receber_dano(self.dano)




class Tanque(Tropas):
    contador = 1


    def __init__(self):
        nome = f"Tanque{Tanque.contador}"
        Tanque.contador += 1
        super().__init__(nome, vida=8, dano=3, recurso = 5)


    def atirar_base(self, b: Base):
        b.receber_dano(self.dano)


    def atirar(self, alvo: Tropas):
        alvo.receber_dano(self.dano)


#class anti-tanque
#class Engenheiro
#class anti-aerea
#class médico
#class


class Campo_de_batalha:
    def __init__(self, base1: Base, base2: Base):
        self.base1 = base1
        self.base2 = base2
        self.tropas1 = []
        self.tropas2 = []


    def adicionar_Tropas(self, base_num: int, modelo: str):
        tropa = None
        if modelo == "1":
            tropa = Soldado()
        elif modelo == "2":
            tropa = Tanque()


        if tropa:
            if base_num == 1:
                if base1.recurso < tropa.recurso:
                    print("\nRecursos insuficientes!!!")
                else:
                    self.tropas1.append(tropa)
            elif base_num == 2:
                if base2.recurso < tropa.recurso:
                    print("\nRecursos insuficientes!!!")
                else:
                    self.tropas2.append(tropa)


    def remover_mortos(self):
        self.tropas1 = [t for t in self.tropas1 if t.esta_viva()]
        self.tropas2 = [t for t in self.tropas2 if t.esta_viva()]


    def ataque(self, atacante: Tropas, alvo: Tropas):
        atacante.atirar(alvo)


    def mostrar_campo(self):
        print("---Campo de batalha atual---")
        print("Base 1: ")
        for t in self.tropas1:
            print(f"{t.nome}[{t.vida}]")
        print("Base 2: ")
        for t in self.tropas2:
            print(f"{t.nome}[{t.vida}]")




if __name__ == "__main__":
    print("rodando...\n")


    base1 = Base("Azul")
    base2 = Base("Vermelho")
    campo = Campo_de_batalha(base1, base2)


    rodada = 1
    while base1.vida > 0 and base2.vida > 0:
        print(f"\n===== RODADA {rodada} =====\n")


        if input("\nBase 1 quer adicionar tropas? (s/n) ") == "s":
            while True:
                print("\nAdicionar tropas na base 1")
                print(f"Base 1 tem {base1.recurso} recursos")
                print("1 - Soldado (2 de custo)")
                print("2 - Tanque (5 de custo)")
                print("3 - Concluir")
                modelo = input("Digite o número da tropa: ")


                if modelo == "3":
                    print("Tropas adicionadas\n")
                    break
                campo.adicionar_Tropas(1, modelo)
                base1.gastar_recurso(modelo)


        if input("\nBase 2 quer adicionar tropas? (s/n) ") == "s":
            while True:
                print("\nAdicionar tropas na base 2")
                print(f"Base 2 tem {base2.recurso} recursos")
                print("1 - Soldado (2 de custo)")
                print("2 - Tanque (5 de custo)")
                print("3 - Concluir")
                modelo = input("Digite o número da tropa: ")


                if modelo == "3":
                    print("Tropas adicionadas\n")
                    break
                campo.adicionar_Tropas(2, modelo)
                base2.gastar_recurso(modelo)


        print("\nRodada de ataque da Base 1!!!")
        for tropa in campo.tropas1:
            if not campo.tropas2:  
                print(f"{tropa.nome} está atacando diretamente a base inimiga!")
                tropa.atirar_base(base2)
                if base2.vida > 0:
                    print(f"Base Inimiga com {base2.vida} de vida!!!")
                else:
                    print("Base inimiga destruida!!!")
            else:
                print(f"\nTurno de {tropa.nome}")
                print("Escolha um dos Alvos da Base 2\n")
                for index, t in enumerate(campo.tropas2):
                    print(f"{index + 1} - {t.nome}[{t.vida}]")
                escolha = int(input("Tropa a ser atacada: ")) - 1
                alvo = campo.tropas2[escolha]
                campo.ataque(tropa, alvo)




        if base2.vida <= 0:
            print("\nA Base 2 foi destruída! Base 1 vence!")
            break


        print("\nRodada de ataque da Base 2!!!")
        for tropa in campo.tropas2:
            if not campo.tropas1:
                print(f"{tropa.nome} está atacando diretamente a base inimiga!")
                tropa.atirar_base(base1)
                if base1.vida > 0:
                    print(f"Base Inimiga com {base1.vida} de vida!!!")
                else:
                    print("Base inimiga destruida!!!")
            else:
                print(f"\nTurno de {tropa.nome}")
                print("Escolha um dos Alvos da Base 1\n")
                for index, t in enumerate(campo.tropas1):
                    print(f"{index + 1} - {t.nome}[{t.vida}]")
                escolha = int(input("Tropa a ser atacada: ")) - 1
                alvo = campo.tropas1[escolha]
                campo.ataque(tropa, alvo)


        campo.remover_mortos()
        base1.reset_recurso()
        base2.reset_recurso()


        if base1.vida <= 0:
            print("\nA Base 1 foi destruída! Base 2 vence!")
            break
        if base2.vida <= 0:
            print("\nA Base 2 foi destruída! Base 1 vence!")
            break


        campo.mostrar_campo()
        rodada += 1
