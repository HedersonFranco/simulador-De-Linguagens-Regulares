# -*- coding: utf-8 -*-
"""
Núcleo do simulador: definição formal de um AFN-ε e os algoritmos implementados
manualmente (fecho-ε, passo de leitura e simulação de uma palavra).

Definição formal:

    M = (Q, Σ, δ, q0, F)

    Q   conjunto finito de estados
    Σ   alfabeto finito (ε não pertence a Σ)
    δ   Q × (Σ ∪ {ε}) → P(Q)    função de transição: devolve um CONJUNTO de estados
    q0  estado inicial (q0 ∈ Q)
    F   conjunto de estados finais (F ⊆ Q)

Restrição do enunciado: nenhuma biblioteca de Teoria da Computação, Teoria dos
Grafos ou Autômatos é usada. Aqui aparecem apenas `dataclasses` (registros de
dados) e as estruturas básicas da linguagem (set, frozenset, dict, list, tuple).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

# Marcador interno do movimento vazio. Todo símbolo de Σ é um único caractere
# "comum" e ε é proibido em Σ, logo ε nunca é confundido com um símbolo lido.
EPSILON = "ε"

# Grafias aceitas para ε nos arquivos de entrada (sem diferenciar maiúsculas).
GRAFIAS_EPSILON = ("ε", "λ", "eps", "epsilon", "lambda")

Conjunto = FrozenSet[str]
Aresta = Tuple[str, str]  # (origem, destino) de uma transição-ε


class ErroDefinicao(Exception):
    """Definição de autômato inválida ou arquivo de entrada mal formado."""


def eh_grafia_epsilon(texto: str) -> bool:
    """True se `texto` é uma das grafias aceitas para ε (ε, λ, eps, epsilon, lambda)."""
    return texto.strip().lower() in GRAFIAS_EPSILON


def _sem_repeticao(itens: Iterable[str]) -> Tuple[str, ...]:
    """Remove repetições preservando a ordem de declaração."""
    vistos = set()
    resultado = []
    for item in itens:
        if item not in vistos:
            vistos.add(item)
            resultado.append(item)
    return tuple(resultado)


# --------------------------------------------------------------------------
# Registros que guardam o rastro da computação (usados pela camada de saída)
# --------------------------------------------------------------------------
@dataclass
class Passo:
    """Um passo da computação: a leitura de UM símbolo da palavra."""

    indice: int                   # posição do símbolo na palavra (começa em 1)
    simbolo: str                  # símbolo lido
    ativos_antes: Conjunto        # estados ativos antes da leitura
    movidos: Conjunto             # δ(ativos_antes, símbolo), ainda SEM o fecho-ε
    ativos_depois: Conjunto       # ε-fecho(movidos): novo conjunto de estados ativos
    arestas_epsilon: List[Aresta]  # transições-ε usadas para calcular o fecho
    simbolo_valido: bool          # False se o símbolo não pertence a Σ


@dataclass
class Computacao:
    """Resultado completo (e rastreável) da simulação de UMA palavra."""

    palavra: str
    ativos_iniciais: Conjunto                 # ε-fecho({q0})
    arestas_epsilon_iniciais: List[Aresta]
    passos: List[Passo]
    ativos_finais: Conjunto                   # estados ativos após o último símbolo
    intersecao: Conjunto                      # ativos_finais ∩ F
    aceita: bool                              # True se e somente se intersecao ≠ ∅


# --------------------------------------------------------------------------
# O autômato
# --------------------------------------------------------------------------
class AFNEpsilon:
    """
    AFN-ε M = (Q, Σ, δ, q0, F).

    `transicoes` é um iterável de triplas (origem, símbolo, destinos), onde
    `símbolo` pertence a Σ ou é EPSILON, e `destinos` é um iterável de estados.
    Triplas com a mesma (origem, símbolo) são unidas: δ devolve um conjunto.
    """

    def __init__(self, estados, alfabeto, inicial, finais, transicoes,
                 nome: str = "", descricao: str = ""):
        self.nome = nome
        self.descricao = descricao
        self.estados: Tuple[str, ...] = _sem_repeticao(estados)    # Q (ordem de declaração)
        self.alfabeto: Tuple[str, ...] = _sem_repeticao(alfabeto)  # Σ
        self.inicial: str = inicial                                # q0
        self.finais: Conjunto = frozenset(finais)                  # F
        self._ordem: Dict[str, int] = {q: i for i, q in enumerate(self.estados)}
        self._simbolos: Conjunto = frozenset(self.alfabeto)
        self.delta: Dict[Tuple[str, str], Conjunto] = {}           # (q, a) -> δ(q, a)
        self._validar_componentes()
        self._montar_delta(transicoes)

    # ----------------------------- validação -----------------------------
    def _validar_componentes(self) -> None:
        if not self.estados:
            raise ErroDefinicao("o conjunto de estados Q não pode ser vazio.")
        for q in self.estados:
            if not isinstance(q, str) or q == "" or any(c.isspace() or c == "," for c in q):
                raise ErroDefinicao(
                    f"nome de estado inválido: {q!r} (use texto não vazio, sem espaços nem vírgulas).")
        if not self.alfabeto:
            raise ErroDefinicao("o alfabeto Σ não pode ser vazio.")
        for s in self.alfabeto:
            if not isinstance(s, str) or len(s) != 1:
                raise ErroDefinicao(
                    f"símbolo inválido no alfabeto: {s!r} (cada símbolo deve ser um único caractere).")
            if s.isspace() or s in ",#" or eh_grafia_epsilon(s):
                raise ErroDefinicao(
                    f"o caractere {s!r} é reservado (espaço, vírgula, '#', 'ε' e 'λ') "
                    "e não pode ser símbolo de Σ.")
        if self.inicial not in self._ordem:
            raise ErroDefinicao(f"o estado inicial {self.inicial!r} não pertence a Q.")
        fora = sorted(q for q in self.finais if q not in self._ordem)
        if fora:
            raise ErroDefinicao(
                "estados finais que não pertencem a Q: " + ", ".join(repr(q) for q in fora) + ".")

    def _montar_delta(self, transicoes) -> None:
        acumulado: Dict[Tuple[str, str], set] = {}
        for origem, simbolo, destinos in transicoes:
            if isinstance(destinos, str):
                destinos = [destinos]
            destinos = list(destinos)
            rotulo = f"({origem}, {simbolo} -> {', '.join(destinos)})"
            if origem not in self._ordem:
                raise ErroDefinicao(f"transição {rotulo}: o estado de origem {origem!r} não pertence a Q.")
            if simbolo != EPSILON and simbolo not in self._simbolos:
                raise ErroDefinicao(
                    f"transição {rotulo}: o símbolo {simbolo!r} não pertence a Σ "
                    "(para transição vazia use ε, eps ou lambda).")
            for destino in destinos:
                if destino not in self._ordem:
                    raise ErroDefinicao(
                        f"transição {rotulo}: o estado de destino {destino!r} não pertence a Q.")
                acumulado.setdefault((origem, simbolo), set()).add(destino)
        self.delta = {chave: frozenset(alvos) for chave, alvos in acumulado.items()}

    # ------------------------------ utilidades ---------------------------
    def ordenar(self, conjunto: Iterable[str]) -> List[str]:
        """Ordena estados pela ordem de declaração em Q (saída sempre determinística)."""
        return sorted(conjunto, key=self._ordem.__getitem__)

    def transicao(self, estado: str, simbolo: str) -> Conjunto:
        """δ(estado, símbolo) — conjunto vazio quando não há transição definida."""
        return self.delta.get((estado, simbolo), frozenset())

    # --------------------------- algoritmos do AFN-ε ----------------------
    def fecho_epsilon(self, conjunto: Iterable[str],
                      arestas: Optional[List[Aresta]] = None) -> Conjunto:
        """
        ε-fecho de um CONJUNTO de estados: todos os estados alcançáveis a partir
        deles seguindo ZERO ou mais transições-ε.

        Algoritmo (busca em largura sobre o grafo formado só pelas transições-ε):
            1. fecho ← conjunto                    (0 transições: todo estado alcança a si mesmo)
            2. fila  ← estados de conjunto
            3. enquanto a fila não acabou:
                   atual ← próximo da fila
                   para cada destino em δ(atual, ε):
                       se destino ∉ fecho: acrescente-o a fecho e ao fim da fila
            4. devolva fecho

        O teste "destino ∉ fecho" garante a terminação mesmo com ciclos de ε
        (cada estado entra na fila no máximo uma vez). Custo: O(|Q| + #transições-ε).

        Se `arestas` for uma lista, nela são anotadas as transições-ε que
        descobriram cada novo estado (usado apenas para mostrar o processo).
        """
        fila = self.ordenar(conjunto)
        fecho = set(fila)
        posicao = 0
        while posicao < len(fila):
            atual = fila[posicao]
            posicao += 1
            for destino in self.ordenar(self.transicao(atual, EPSILON)):
                if destino not in fecho:
                    fecho.add(destino)
                    fila.append(destino)
                    if arestas is not None:
                        arestas.append((atual, destino))
        return frozenset(fecho)

    def mover(self, conjunto: Iterable[str], simbolo: str) -> Conjunto:
        """δ(S, a) = união de δ(q, a) para todo q ∈ S (SEM aplicar o fecho-ε)."""
        alcancados = set()
        for estado in conjunto:
            alcancados |= self.transicao(estado, simbolo)
        return frozenset(alcancados)

    def simular(self, palavra: str) -> Computacao:
        """
        Simula o AFN-ε sobre `palavra`, acompanhando o CONJUNTO de estados ativos.

            ativos₀ = ε-fecho({q0})
            ativosᵢ = ε-fecho( δ(ativosᵢ₋₁, aᵢ) )      para cada símbolo aᵢ lido
            aceita  ⇔  ativosₙ ∩ F ≠ ∅

        Um símbolo fora de Σ não tem transição alguma: o conjunto de estados
        ativos fica vazio e a palavra é rejeitada (w ∉ Σ*, logo w ∉ L(M)).
        """
        arestas_iniciais: List[Aresta] = []
        ativos = self.fecho_epsilon({self.inicial}, arestas_iniciais)
        ativos_iniciais = ativos
        passos: List[Passo] = []
        for indice, simbolo in enumerate(palavra, start=1):
            valido = simbolo in self._simbolos
            # Cuidado: só consultamos δ para símbolos de Σ. Assim um 'ε' digitado
            # dentro da palavra não é confundido com o movimento vazio.
            movidos = self.mover(ativos, simbolo) if valido else frozenset()
            arestas: List[Aresta] = []
            novos = self.fecho_epsilon(movidos, arestas)
            passos.append(Passo(indice, simbolo, ativos, movidos, novos, arestas, valido))
            ativos = novos
        intersecao = ativos & self.finais
        return Computacao(palavra, ativos_iniciais, arestas_iniciais, passos,
                          ativos, intersecao, bool(intersecao))

    def reconhece(self, palavra: str) -> bool:
        """Atalho: True se `palavra` ∈ L(M)."""
        return self.simular(palavra).aceita
