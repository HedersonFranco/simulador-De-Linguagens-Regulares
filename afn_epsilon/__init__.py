# -*- coding: utf-8 -*-
"""Simulador de AFN-ε (Autômatos Finitos Não-determinísticos com movimentos vazios)."""

from .automato import AFNEpsilon, Computacao, EPSILON, ErroDefinicao, Passo
from .leitor import carregar_arquivo, normalizar_palavra
from .saida import (configurar_saida, escolher_estilo, imprimir_automato,
                    imprimir_computacao, imprimir_resumo)

__all__ = [
    "AFNEpsilon", "Computacao", "EPSILON", "ErroDefinicao", "Passo",
    "carregar_arquivo", "normalizar_palavra",
    "configurar_saida", "escolher_estilo", "imprimir_automato",
    "imprimir_computacao", "imprimir_resumo",
]
