# -*- coding: utf-8 -*-
"""
Apresentação no terminal: mostra o autômato carregado e, para cada palavra, o
passo a passo da computação (estados ativos iniciais, símbolo lido, novo conjunto
de estados ativos e o veredito ACEITA/REJEITADA com a sua justificativa).

Esta camada só FORMATA: toda a lógica de simulação fica em `automato.py`.
"""

from __future__ import annotations

import sys
import textwrap
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .automato import AFNEpsilon, Computacao, EPSILON

LARGURA = 72
RECUO = " " * 6


@dataclass(frozen=True)
class Estilo:
    """Símbolos usados na saída (há uma versão só com ASCII para terminais limitados)."""

    eps: str
    vazio: str
    inter: str
    diferente: str
    delta: str
    sigma: str
    marca_inicial: str
    marca_final: str


ESTILO_UNICODE = Estilo(eps="ε", vazio="∅", inter="∩", diferente="≠", delta="δ",
                        sigma="Σ", marca_inicial="→", marca_final="*")
ESTILO_ASCII = Estilo(eps="eps", vazio="{}", inter="inter", diferente="!=", delta="delta",
                      sigma="Sigma", marca_inicial=">", marca_final="*")
_AMOSTRA = "εΣδ∅∩≠→"


def configurar_saida() -> None:
    """Evita que um caractere não codificável derrube o programa (vira '?')."""
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def escolher_estilo(forcar_ascii: bool = False) -> Estilo:
    """Unicode (ε, ∅, ∩...) quando o terminal consegue exibi-lo; senão, ASCII."""
    if forcar_ascii:
        return ESTILO_ASCII
    codificacao = getattr(sys.stdout, "encoding", None)
    if codificacao:
        try:
            _AMOSTRA.encode(codificacao)
        except (UnicodeEncodeError, LookupError):
            return ESTILO_ASCII
    return ESTILO_UNICODE


# ------------------------------------------------------------ formatação
def _conj(automato: AFNEpsilon, conjunto: Iterable[str], estilo: Estilo) -> str:
    """{q0, q1} na ordem de declaração de Q; ∅ para o conjunto vazio."""
    elementos = automato.ordenar(conjunto)
    if not elementos:
        return estilo.vazio
    return "{" + ", ".join(elementos) + "}"


def _rotulo_palavra(palavra: str, estilo: Estilo) -> str:
    return f"{estilo.eps} (palavra vazia)" if palavra == "" else f'"{palavra}"'


def _titulo(texto: str) -> None:
    print("=" * LARGURA)
    print(f" {texto}")
    print("=" * LARGURA)


def _imprimir_arestas(arestas, estilo: Estilo, recuo: str = RECUO) -> None:
    """Mostra por quais transições-ε o fecho foi calculado (só quando houve alguma)."""
    if arestas:
        usadas = ", ".join(f"{origem} -{estilo.eps}-> {destino}" for origem, destino in arestas)
        print(f"{recuo}{estilo.eps}-transições percorridas: {usadas}")


def _tabela(automato: AFNEpsilon, estilo: Estilo) -> List[str]:
    simbolos = list(automato.alfabeto) + [EPSILON]
    cabecalho = [""] + [estilo.eps if s == EPSILON else s for s in simbolos]
    linhas = []
    for estado in automato.estados:
        marca = (estilo.marca_inicial if estado == automato.inicial else " ") + \
                (estilo.marca_final if estado in automato.finais else " ")
        celulas = [f"{marca} {estado}"]
        celulas += [_conj(automato, automato.transicao(estado, s), estilo) for s in simbolos]
        linhas.append(celulas)
    larguras = [max(len(linha[i]) for linha in [cabecalho] + linhas) for i in range(len(cabecalho))]

    def montar(celulas):
        return " | ".join(c.ljust(w) for c, w in zip(celulas, larguras)).rstrip()

    return [montar(cabecalho), "-+-".join("-" * w for w in larguras)] + [montar(l) for l in linhas]


# ------------------------------------------------------------- impressão
def imprimir_automato(automato: AFNEpsilon, estilo: Estilo, origem: str = "") -> None:
    """Mostra o autômato lido: M = (Q, Σ, δ, q0, F) e a tabela de transição."""
    _titulo(f"AUTÔMATO FINITO NÃO-DETERMINÍSTICO COM MOVIMENTOS VAZIOS (AFN-{estilo.eps})")
    if origem:
        print(f" Arquivo   : {origem}")
    print(f" Nome      : {automato.nome}")
    if automato.descricao:
        print(f" Descrição : {automato.descricao}")
    print()
    print(f" M = (Q, {estilo.sigma}, {estilo.delta}, q0, F)")
    campos = [
        ("Q  (estados)", _conj(automato, automato.estados, estilo)),
        (f"{estilo.sigma}  (alfabeto)", "{" + ", ".join(automato.alfabeto) + "}"),
        ("q0 (estado inicial)", automato.inicial),
        ("F  (estados finais)", _conj(automato, automato.finais, estilo)),
    ]
    for rotulo, valor in campos:
        print(f"   {rotulo.ljust(19)} = {valor}")
    print()
    print(f" Tabela de transição {estilo.delta}   "
          f"({estilo.marca_inicial} estado inicial, {estilo.marca_final} estado final)")
    for linha in _tabela(automato, estilo):
        print(" " + linha)


def imprimir_computacao(automato: AFNEpsilon, comp: Computacao, estilo: Estilo,
                        numero: int, total: Optional[int] = None) -> None:
    """Mostra a computação de UMA palavra, passo a passo."""
    fecho = f"{estilo.eps}-fecho"
    print()
    _titulo(f"Palavra {numero}" + (f"/{total}" if total else "") +
            f": {_rotulo_palavra(comp.palavra, estilo)}")

    # 1) conjunto inicial de estados ativos (com o fecho-ε do estado inicial)
    print(f" [Início] Estados ativos iniciais = {fecho}({{{automato.inicial}}}) = "
          f"{_conj(automato, comp.ativos_iniciais, estilo)}")
    _imprimir_arestas(comp.arestas_epsilon_iniciais, estilo)
    if not comp.passos:
        print(f"{RECUO}(palavra vazia: não há símbolos para ler)")

    # 2) um bloco por símbolo lido
    for passo in comp.passos:
        print(f" [Passo {passo.indice}] Símbolo lido: '{passo.simbolo}'")
        linhas = [
            (f"{estilo.delta}({_conj(automato, passo.ativos_antes, estilo)}, {passo.simbolo})",
             _conj(automato, passo.movidos, estilo)),
            (f"{fecho}({_conj(automato, passo.movidos, estilo)})",
             _conj(automato, passo.ativos_depois, estilo)),
            ("Estados ativos", _conj(automato, passo.ativos_depois, estilo)),
        ]
        largura = max(len(rotulo) for rotulo, _ in linhas)
        for posicao, (rotulo, valor) in enumerate(linhas):
            print(f"{RECUO}{rotulo.ljust(largura)} = {valor}")
            if posicao == 1:                       # logo após o fecho-ε, mostra como ele foi obtido
                _imprimir_arestas(passo.arestas_epsilon, estilo, RECUO + "   ")
        if not passo.simbolo_valido:
            print(f"{RECUO}AVISO: o símbolo '{passo.simbolo}' não pertence a {estilo.sigma}; "
                  "não existe transição para ele.")
        if passo.ativos_antes and not passo.ativos_depois:
            print(f"{RECUO}Nenhum estado ativo: todos os ramos da computação morreram.")

    # 3) veredito: estados ativos finais ∩ F
    print(" [Fim] Palavra lida por completo")
    relacao = f"  ({estilo.diferente} {estilo.vazio})" if comp.aceita else ""
    linhas = [
        ("Estados ativos finais", _conj(automato, comp.ativos_finais, estilo)),
        ("Estados finais F", _conj(automato, automato.finais, estilo)),
        (f"Estados ativos {estilo.inter} F", _conj(automato, comp.intersecao, estilo) + relacao),
    ]
    largura = max(len(rotulo) for rotulo, _ in linhas)
    for rotulo, valor in linhas:
        print(f"{RECUO}{rotulo.ljust(largura)} = {valor}")
    print(f" RESULTADO: {'ACEITA' if comp.aceita else 'REJEITADA'}")
    if comp.aceita:
        justificativa = ("a interseção entre os estados ativos finais e F é NÃO-VAZIA "
                         f"({_conj(automato, comp.intersecao, estilo)}): há estado final ativo "
                         "ao fim da leitura.")
    elif not comp.ativos_finais:
        justificativa = ("não há estados ativos ao fim da leitura, logo a interseção com F é VAZIA "
                         f"({estilo.vazio}).")
    else:
        justificativa = ("a interseção entre os estados ativos finais e F é VAZIA: nenhum estado "
                         "ativo ao fim da leitura é final.")
    print(textwrap.fill(justificativa, width=LARGURA, initial_indent=" Justificativa: ",
                        subsequent_indent=" " * 16, break_on_hyphens=False))


def imprimir_resumo(comps: List[Computacao], estilo: Estilo) -> None:
    """Tabela final com o veredito de cada palavra testada."""
    print()
    _titulo("RESUMO")
    rotulos = [_rotulo_palavra(c.palavra, estilo) for c in comps]
    largura = max(len(r) for r in rotulos)
    for numero, (comp, rotulo) in enumerate(zip(comps, rotulos), start=1):
        resultado = "ACEITA" if comp.aceita else "REJEITADA"
        invalidos = sorted({p.simbolo for p in comp.passos if not p.simbolo_valido})
        nota = ""
        if invalidos:
            nota = f"  (símbolo fora de {estilo.sigma}: " + ", ".join(f"'{s}'" for s in invalidos) + ")"
        print(f" {numero:>3}  {rotulo.ljust(largura)}  {resultado}{nota}")
    aceitas = sum(1 for comp in comps if comp.aceita)
    print(f" Total: {len(comps)} palavra(s): {aceitas} aceita(s), {len(comps) - aceitas} rejeitada(s).")
