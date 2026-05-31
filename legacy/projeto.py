from abc import ABCMeta, abstractmethod

class Base:
    __nome: str
    vida = int
    recurso = int

    def __init__(self, nome: str):
        self.__nome = nome
        self.vida = 10
        self.recurso = 0
    
    def receber_dano(self, dano: int):
        self.vida -= dano
        print(f"A base {self.__nome} recebeu {dano} de dano! Vida restante: {self.vida}")

class Tropas (metaclass = ABCMeta):
    def __init__(self, nome: str, vida: int, dano: int):
        self.nome = nome
        self.vida = vida
        self.dano = dano

    @abstractmethod
    def atirar_base(self, b: Base):
        pass

    @abstractmethod
    def atirar(self, alvo):
        pass

    def receber_dano(self, dano: int):
        self.vida -= dano
        print(f"A base {self.__nome} recebeu {dano} de dano! Vida restante: {self.vida}")

    def esta_viva(self):
        return self.vida > 0

class Soldado(Tropas):
    contador = 1
    
    def __init__(self):
        nome = f"Soldado{Soldado.contador}"
        Soldado.contador += 1
        super().__init__(nome, vida=3, dano=1)

    def atirar_base(self, b: Base):
        print(f"{self.nome} está atirando na base {b.nome}!")
        b.receber_dano(self.dano)

    def atirar(self, alvo: Tropas):
        print(f"{self.nome} está atirando em {alvo.nome}!")
        alvo.receber_dano(self.dano)


class Tanque(Tropas):
    contador = 1
    
    def __init__(self):
        nome = f"Tanque{Tanque.contador}"
        Tanque.contador += 1
        super().__init__(nome, vida=8, dano=3)

    def atirar_base(self, b: Base):
        print(f"{self.nome} está disparando na base {b.nome} com munição pesada!")
        b.receber_dano(self.dano)  

    def atirar(self, alvo: Tropas):
        print(f"{self.nome} está disparando contra {alvo.nome}!")
        alvo.receber_dano(self.dano) 


class Campo_de_batalha:
    def __init__(self, base1: Base, base2: Base):
        self.base1 = base1
        self.base2 = base2
        self.tropas1 = []
        self.tropas2 = []

    def adicionar_Tropas(self, base_num: int):
        
        while True:
            print(f"Adicionar tropas na base {base_num}\n")
            print("Escolha o modelo  da Tropa:\n")
            print("1 - Soldado\n")
            print("2 - Tanque\n")
            print("3 - Concluir\n")
            modelo = input("\nDigite o número da tropa: \n") 


            if modelo == "1":
                tropa = Soldado()
            elif modelo == "2":
                tropa = Tanque()
            elif modelo == "3":
                print("tropas adicionadas\n")
                break
            else:
                print("Número de tropa inválido\n")
                continue 

            if base_num == 1:
                self.tropas1.append(tropa)
            elif base_num == 2:
                self.tropas2.append(tropa)

    def remover_mortos(self):
        self.tropas1 = [t for t in self.tropas1 if t.esta_viva()]
        self.tropas2 = [t for t in self.tropas2 if t.esta_viva()]
 
 
if __name__ == "__main__":

    print("rodando...\n")
    
    base1 = Base("Azul")
    base2 = Base("Vermelho")

    campo = Campo_de_batalha(base1, base2)

    campo.adicionar_Tropas(1)

    print(f"Tropas1: {campo.tropas1}")
    