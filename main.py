#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Linguagens Regulares: reconhecedor de AFN-ε (Teoria da Computação, UFPI).

Uso:
    python main.py ARQUIVO                 # processa as palavras listadas no arquivo
    python main.py ARQUIVO -p abba -p ε    # testa também outras palavras (ε = palavra vazia)
    python main.py ARQUIVO -i              # depois, pergunta novas palavras no terminal
    python main.py ARQUIVO --ascii         # troca ε, ∅, ∩... por eps, {}, inter...
"""

import argparse
import sys

from afn_epsilon import (ErroDefinicao, carregar_arquivo, configurar_saida, escolher_estilo,
                         imprimir_automato, imprimir_computacao, imprimir_resumo,
                         normalizar_palavra)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Simulador e reconhecedor de Autômatos Finitos Não-determinísticos "
                    "com movimentos vazios (AFN-ε), com a computação passo a passo.",
        epilog="Exemplo: python main.py exemplos/ex1_a_b_c.json")
    parser.add_argument("arquivo", help="arquivo .json ou .txt com o autômato e as palavras de teste")
    parser.add_argument("-p", "--palavra", action="append", default=[], metavar="PALAVRA",
                        help='testa também esta palavra (repita a opção para várias; '
                             'use ε para a palavra vazia)')
    parser.add_argument("-i", "--interativo", action="store_true",
                        help="depois das palavras do arquivo, lê novas palavras do teclado")
    parser.add_argument("--ascii", action="store_true",
                        help="troca os símbolos matemáticos da saída por texto ASCII (eps, {}, inter, ...)")
    return parser


def sessao_interativa(automato, estilo, resultados) -> None:
    """Lê palavras do teclado até 'sair' (ou Ctrl+D / Ctrl+Z) e simula cada uma."""
    print()
    print("Modo interativo: digite uma palavra e tecle Enter.")
    print('  (ε, λ ou "" = palavra vazia; "sair" ou Ctrl+D encerra)')
    while True:
        try:
            entrada = input("palavra> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if entrada.lower() == "sair":
            break
        if not entrada:
            continue
        computacao = automato.simular(normalizar_palavra(entrada))
        imprimir_computacao(automato, computacao, estilo, len(resultados) + 1)
        resultados.append(computacao)


def main(argv=None) -> int:
    args = criar_parser().parse_args(argv)
    configurar_saida()
    estilo = escolher_estilo(args.ascii)

    try:
        automato, palavras, avisos = carregar_arquivo(args.arquivo)
    except ErroDefinicao as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2
    for aviso in avisos:
        print(f"AVISO: {aviso}", file=sys.stderr)

    palavras = palavras + [normalizar_palavra(p) for p in args.palavra]
    imprimir_automato(automato, estilo, args.arquivo)
    if not palavras and not args.interativo:
        print("ERRO: nenhuma palavra para testar (preencha 'palavras' no arquivo, "
              "ou use -p PALAVRA / -i).", file=sys.stderr)
        return 1

    resultados = []
    for numero, palavra in enumerate(palavras, start=1):
        computacao = automato.simular(palavra)
        imprimir_computacao(automato, computacao, estilo, numero, len(palavras))
        resultados.append(computacao)
    if args.interativo:
        sessao_interativa(automato, estilo, resultados)
    if resultados:
        imprimir_resumo(resultados, estilo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
