# -*- coding: utf-8 -*-
"""
Leitura do arquivo de entrada (JSON ou TXT) e construção do AFN-ε.

O arquivo traz os elementos formais do autômato (Q, Σ, q0, F, δ) e a lista de
palavras a testar. Todo erro de formato vira `ErroDefinicao` com mensagem clara
(em TXT, com o número da linha). Só são usados `json` e `os` da biblioteca padrão
— nada de Teoria da Computação, de grafos ou de autômatos (nem expressões regulares).
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from .automato import AFNEpsilon, EPSILON, ErroDefinicao, eh_grafia_epsilon

# Rótulos aceitos para cada campo (sem diferenciar maiúsculas de minúsculas).
# O primeiro de cada tupla é o nome "canônico", o documentado no README.
CAMPOS = {
    "estados": ("estados", "q"),
    "alfabeto": ("alfabeto", "sigma", "σ"),
    "inicial": ("inicial", "estado_inicial", "estado inicial", "q0"),
    "finais": ("finais", "estados_finais", "estados finais", "f"),
    "transicoes": ("transicoes", "transições", "delta", "δ"),
    "palavras": ("palavras", "cadeias", "testes"),
    "nome": ("nome",),
    "descricao": ("descricao", "descrição"),
}
_CANONICO = {rotulo: campo for campo, rotulos in CAMPOS.items() for rotulo in rotulos}
_OBRIGATORIOS = ("estados", "alfabeto", "inicial", "finais", "transicoes")
_SECOES = ("transicoes", "palavras")   # campos TXT que ocupam várias linhas

Transicao = Tuple[str, str, List[str]]


def normalizar_palavra(texto: str) -> str:
    """Converte as grafias da palavra vazia (ε, λ, "") em '' e devolve as demais intactas."""
    if texto in ("", '""') or texto.lower() in ("ε", "λ"):
        return ""
    return texto


def carregar_arquivo(caminho: str) -> Tuple[AFNEpsilon, List[str], List[str]]:
    """
    Lê `caminho` (.json ou .txt) e devolve (autômato, palavras de teste, avisos).
    Levanta ErroDefinicao se o arquivo não puder ser lido ou estiver incorreto.
    """
    try:
        with open(caminho, "rb") as arquivo:
            bruto = arquivo.read()
    except OSError as erro:
        raise ErroDefinicao(f"não foi possível ler '{caminho}': {erro.strerror or erro}.")
    texto = _decodificar(bruto)
    extensao = os.path.splitext(caminho)[1].lower()
    eh_json = extensao == ".json" or (extensao != ".txt" and texto.lstrip().startswith("{"))
    avisos: List[str] = []
    campos = _ler_json(texto, avisos) if eh_json else _ler_txt(texto)
    return _construir(campos, caminho, avisos)


def _decodificar(bruto: bytes) -> str:
    try:
        return bruto.decode("utf-8-sig")                     # aceita (e descarta) o BOM
    except UnicodeDecodeError:
        return bruto.decode("cp1252", errors="replace")      # arquivos salvos como "ANSI"


def _construir(campos: Dict, caminho: str, avisos: List[str]):
    ausentes = [campo for campo in _OBRIGATORIOS if campo not in campos]
    if ausentes:
        raise ErroDefinicao("campo(s) obrigatório(s) ausente(s): " + ", ".join(ausentes) + ".")
    automato = AFNEpsilon(
        estados=campos["estados"],
        alfabeto=campos["alfabeto"],
        inicial=campos["inicial"],
        finais=campos["finais"],
        transicoes=campos["transicoes"],
        nome=campos.get("nome") or os.path.basename(caminho),
        descricao=campos.get("descricao", ""),
    )
    return automato, list(campos.get("palavras", [])), avisos


# ------------------------------------------------------------------ JSON
def _objeto_sem_repeticao(pares):
    """Impede chaves repetidas (o json padrão deixaria a última sobrescrever a primeira)."""
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ErroDefinicao(f"chave repetida no JSON: {chave!r}.")
        objeto[chave] = valor
    return objeto


def _ler_json(texto: str, avisos: List[str]) -> Dict:
    try:
        dados = json.loads(texto, object_pairs_hook=_objeto_sem_repeticao)
    except json.JSONDecodeError as erro:
        raise ErroDefinicao(f"JSON inválido (linha {erro.lineno}, coluna {erro.colno}): {erro.msg}.")
    if not isinstance(dados, dict):
        raise ErroDefinicao("o JSON deve conter um objeto { ... } com os campos do autômato.")

    brutos: Dict = {}
    for chave, valor in dados.items():
        campo = _CANONICO.get(chave.strip().lower())
        if campo is None:
            avisos.append(f"campo desconhecido ignorado: {chave!r}.")
            continue
        if campo in brutos:
            raise ErroDefinicao(f"o campo '{campo}' foi informado mais de uma vez (ex.: 'Q' e 'estados').")
        brutos[campo] = valor

    campos: Dict = {}
    for campo in ("estados", "alfabeto", "finais", "palavras"):
        if campo in brutos:
            campos[campo] = _lista_de_textos(brutos[campo], f"'{campo}'")
    for campo in ("inicial", "nome", "descricao"):
        if campo in brutos:
            campos[campo] = _texto(brutos[campo], f"'{campo}'")
    if "transicoes" in brutos:
        campos["transicoes"] = _transicoes_json(brutos["transicoes"])
    if "palavras" in campos:
        campos["palavras"] = [normalizar_palavra(p) for p in campos["palavras"]]
    return campos


def _texto(valor, onde: str) -> str:
    if not isinstance(valor, str):
        raise ErroDefinicao(f"{onde} deve ser um texto entre aspas, mas veio {valor!r}.")
    return valor


def _lista_de_textos(valor, onde: str) -> List[str]:
    if not isinstance(valor, list):
        raise ErroDefinicao(f"{onde} deve ser uma lista, ex.: [\"a\", \"b\"]; veio {valor!r}.")
    return [_texto(item, f"cada item de {onde}") for item in valor]


def _transicoes_json(valor) -> List[Transicao]:
    modelo = '{"estado": {"símbolo": ["destinos"]}}'
    if not isinstance(valor, dict):
        raise ErroDefinicao(f"'transicoes' deve ser um objeto no formato {modelo}.")
    saida: List[Transicao] = []
    for origem, por_simbolo in valor.items():
        if not isinstance(por_simbolo, dict):
            raise ErroDefinicao(
                f"em 'transicoes', o valor de {origem!r} deve ser um objeto do tipo "
                '{"símbolo": ["destinos"]}.')
        for simbolo, destinos in por_simbolo.items():
            if isinstance(destinos, str):
                destinos = [destinos]
            destinos = _lista_de_textos(destinos, f"os destinos de transicoes[{origem!r}][{simbolo!r}]")
            vazio = simbolo == "" or eh_grafia_epsilon(simbolo)
            saida.append((origem, EPSILON if vazio else simbolo, destinos))
    return saida


# ------------------------------------------------------------------- TXT
def _sem_comentario(linha: str) -> str:
    """Remove comentários: um '#' que abre a linha ou vem depois de um espaço."""
    for posicao, caractere in enumerate(linha):
        if caractere == "#" and (posicao == 0 or linha[posicao - 1].isspace()):
            return linha[:posicao]
    return linha


def _sem_chaves(texto: str) -> str:
    """Aceita a notação de conjunto: '{q0, q1}' vale o mesmo que 'q0, q1'."""
    texto = texto.strip()
    if texto.startswith("{") and texto.endswith("}"):
        return texto[1:-1]
    return texto


def _separar_itens(texto: str) -> List[str]:
    """Divide por vírgulas e/ou espaços."""
    return texto.replace(",", " ").split()


def _separar_rotulo(linha: str):
    """Se a linha é 'rótulo: valor' de um campo conhecido, devolve (rótulo, valor)."""
    posicao = linha.find(":")
    if posicao > 0:
        rotulo = linha[:posicao].strip().lower()
        if rotulo in _CANONICO:
            return rotulo, linha[posicao + 1:].strip()
    return None, ""


def _ler_txt(texto: str) -> Dict:
    campos: Dict = {}
    secao = None
    for numero, bruta in enumerate(texto.splitlines(), start=1):
        linha = _sem_comentario(bruta).strip()
        if not linha:
            continue
        rotulo, resto = _separar_rotulo(linha)
        if rotulo is not None:
            campo = _CANONICO[rotulo]
            if campo in _SECOES:
                secao = campo
                campos.setdefault(campo, [])
                linha = resto                      # pode haver conteúdo junto do rótulo
            else:
                if campo in campos:
                    raise ErroDefinicao(f"linha {numero}: o campo '{campo}' aparece mais de uma vez.")
                campos[campo] = _valor_txt(campo, resto, numero)
                secao = None
                continue
        if not linha:
            continue
        if secao == "transicoes":
            campos["transicoes"].append(_transicao_txt(linha, numero))
        elif secao == "palavras":
            campos["palavras"].extend(_palavras_txt(linha))
        else:
            raise ErroDefinicao(
                f"linha {numero}: conteúdo fora de uma seção: {linha!r}. Os campos estados, alfabeto, "
                "inicial e finais levam o valor na mesma linha do rótulo (ex.: 'estados: q0, q1').")
    return campos


def _valor_txt(campo: str, valor: str, numero: int):
    if campo in ("estados", "finais"):
        return _separar_itens(_sem_chaves(valor))
    if campo == "alfabeto":
        return [c for c in _sem_chaves(valor) if not c.isspace() and c != ","]
    if campo == "inicial":
        itens = _separar_itens(valor)
        if len(itens) != 1:
            raise ErroDefinicao(f"linha {numero}: informe exatamente um estado inicial (veio {valor!r}).")
        return itens[0]
    return valor                                   # nome, descricao


def _transicao_txt(linha: str, numero: int) -> Transicao:
    for seta in ("->", "→"):
        if seta in linha:
            esquerda, _, direita = linha.partition(seta)
            break
    else:
        raise ErroDefinicao(
            f"linha {numero}: transição sem '->': {linha!r}. Formato: origem, símbolo -> destino1, destino2")
    lado = _separar_itens(esquerda)
    if len(lado) != 2:
        raise ErroDefinicao(
            f"linha {numero}: o lado esquerdo deve ser 'origem, símbolo' "
            f"(use ε, eps ou lambda para transição vazia): {linha!r}.")
    destinos = _separar_itens(_sem_chaves(direita))
    if not destinos:
        raise ErroDefinicao(f"linha {numero}: transição sem estado de destino: {linha!r}.")
    origem, simbolo = lado
    return origem, (EPSILON if eh_grafia_epsilon(simbolo) else simbolo), destinos


def _palavras_txt(linha: str) -> List[str]:
    return [normalizar_palavra(p) for p in _separar_itens(linha)]
