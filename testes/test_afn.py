# -*- coding: utf-8 -*-
"""
Testes automatizados (apenas `unittest`, da biblioteca padrão).

    python -m unittest discover -s testes -v
"""

import contextlib
import glob
import io
import itertools
import os
import random
import sys
import tempfile
import types
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import main as cli  # noqa: E402
from afn_epsilon import (AFNEpsilon, EPSILON, ErroDefinicao, carregar_arquivo,  # noqa: E402
                         escolher_estilo, imprimir_computacao)
from afn_epsilon.saida import ESTILO_ASCII, ESTILO_UNICODE  # noqa: E402

PASTA_EXEMPLOS = os.path.join(RAIZ, "exemplos")


def criar(estados, alfabeto, inicial, finais, transicoes):
    """Atalho: transicoes = [(origem, símbolo, [destinos]), ...]; use EPSILON para ε."""
    return AFNEpsilon(estados, alfabeto, inicial, finais, transicoes)


def aceita_por_configuracoes(automato, palavra):
    """
    ORÁCULO independente da implementação: percorre o grafo de CONFIGURAÇÕES
    (estado, posição na palavra), que é a definição de "computação" do AFN-ε.
    A palavra é aceita se alguma configuração (f, |w|) com f ∈ F for alcançável.
    """
    inicio = (automato.inicial, 0)
    vistas = {inicio}
    pilha = [inicio]
    while pilha:
        estado, posicao = pilha.pop()
        if posicao == len(palavra) and estado in automato.finais:
            return True
        proximas = [(d, posicao) for d in automato.transicao(estado, EPSILON)]
        if posicao < len(palavra):
            proximas += [(d, posicao + 1) for d in automato.transicao(estado, palavra[posicao])]
        for configuracao in proximas:
            if configuracao not in vistas:
                vistas.add(configuracao)
                pilha.append(configuracao)
    return False


def executar(argumentos):
    """Roda o main capturando stdout/stderr: devolve (código, stdout, stderr)."""
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = cli.main(argumentos)
    return codigo, saida.getvalue(), erro.getvalue()


def exemplo(nome):
    return os.path.join(PASTA_EXEMPLOS, nome)


class TestFechoEpsilon(unittest.TestCase):
    def test_sem_transicoes_epsilon_o_fecho_e_o_proprio_conjunto(self):
        m = criar(["q0", "q1"], ["a"], "q0", [], [("q0", "a", ["q1"])])
        self.assertEqual(m.fecho_epsilon({"q0"}), {"q0"})

    def test_cadeia_de_epsilons(self):
        m = criar(["q0", "q1", "q2", "q3"], ["a"], "q0", [],
                  [("q0", EPSILON, ["q1"]), ("q1", EPSILON, ["q2"]), ("q2", "a", ["q3"])])
        self.assertEqual(m.fecho_epsilon({"q0"}), {"q0", "q1", "q2"})
        self.assertEqual(m.fecho_epsilon({"q1"}), {"q1", "q2"})
        self.assertEqual(m.fecho_epsilon({"q3"}), {"q3"})

    def test_ciclo_e_auto_laco_terminam(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", [],
                  [("q0", EPSILON, ["q1", "q0"]), ("q1", EPSILON, ["q2"]), ("q2", EPSILON, ["q0"])])
        self.assertEqual(m.fecho_epsilon({"q1"}), {"q0", "q1", "q2"})

    def test_conjunto_vazio_e_uniao_de_conjuntos(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", [], [("q0", EPSILON, ["q1"])])
        self.assertEqual(m.fecho_epsilon(set()), frozenset())
        self.assertEqual(m.fecho_epsilon({"q0", "q2"}), {"q0", "q1", "q2"})

    def test_ignora_transicoes_que_leem_simbolos(self):
        m = criar(["q0", "q1"], ["a"], "q0", [], [("q0", "a", ["q1"])])
        self.assertNotIn("q1", m.fecho_epsilon({"q0"}))

    def test_registro_das_arestas_descobridoras(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", [],
                  [("q0", EPSILON, ["q1"]), ("q1", EPSILON, ["q2"])])
        arestas = []
        m.fecho_epsilon({"q0"}, arestas)
        self.assertEqual(arestas, [("q0", "q1"), ("q1", "q2")])


class TestPassoESimulacao(unittest.TestCase):
    def test_mover_une_os_destinos_sem_aplicar_fecho(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", [],
                  [("q0", "a", ["q1"]), ("q1", "a", ["q2"]), ("q2", EPSILON, ["q0"])])
        self.assertEqual(m.mover({"q0", "q1"}, "a"), {"q1", "q2"})
        self.assertEqual(m.mover({"q2"}, "a"), frozenset())

    def test_palavra_vazia_depende_do_fecho_do_estado_inicial(self):
        m = criar(["q0", "q1"], ["a"], "q0", ["q1"], [("q0", EPSILON, ["q1"])])
        self.assertTrue(m.reconhece(""))
        m2 = criar(["q0", "q1"], ["a"], "q0", ["q1"], [("q0", "a", ["q1"])])
        self.assertFalse(m2.reconhece(""))

    def test_epsilon_depois_do_ultimo_simbolo_conta(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", ["q2"],
                  [("q0", "a", ["q1"]), ("q1", EPSILON, ["q2"])])
        self.assertTrue(m.reconhece("a"))

    def test_simbolo_fora_do_alfabeto_rejeita(self):
        m = criar(["q0"], ["a"], "q0", ["q0"], [])
        computacao = m.simular("aba")
        self.assertFalse(computacao.aceita)
        self.assertFalse(computacao.passos[1].simbolo_valido)
        self.assertEqual(computacao.ativos_finais, frozenset())

    def test_epsilon_digitado_na_palavra_nao_vira_movimento_vazio(self):
        m = criar(["q0", "q1"], ["a"], "q0", ["q1"], [("q0", EPSILON, ["q1"])])
        self.assertFalse(m.reconhece("ε"))

    def test_rastro_tem_um_passo_por_simbolo(self):
        m = carregar_arquivo(exemplo("ex1_a_b_c.json"))[0]
        computacao = m.simular("aabbc")
        self.assertEqual([p.simbolo for p in computacao.passos], list("aabbc"))
        self.assertEqual(computacao.ativos_iniciais, {"q0", "q1", "q2"})
        self.assertEqual(computacao.passos[2].ativos_depois, {"q1", "q2"})
        self.assertEqual(computacao.intersecao, {"q2"})

    def test_termina_em_abb_para_todas_as_palavras_ate_tamanho_8(self):
        m = carregar_arquivo(exemplo("ex2_termina_em_abb.txt"))[0]
        for tamanho in range(9):
            for letras in itertools.product("ab", repeat=tamanho):
                palavra = "".join(letras)
                self.assertEqual(m.reconhece(palavra), palavra.endswith("abb"), palavra)

    def test_a_estrela_b_estrela_c_estrela(self):
        m = carregar_arquivo(exemplo("ex1_a_b_c.json"))[0]
        for tamanho in range(8):
            for letras in itertools.product("abc", repeat=tamanho):
                self.assertEqual(m.reconhece("".join(letras)), list(letras) == sorted(letras))

    def test_resultados_coincidem_com_o_oraculo_em_automatos_aleatorios(self):
        sorteio = random.Random(2026)
        palavras = ["".join(t) for n in range(6) for t in itertools.product("ab", repeat=n)]
        for _ in range(300):
            n = sorteio.randint(1, 5)
            estados = [f"q{i}" for i in range(n)]
            transicoes = []
            for q in estados:
                for simbolo in ("a", "b", EPSILON):
                    alvos = [d for d in estados if sorteio.random() < 0.3]
                    transicoes.append((q, simbolo, alvos))
            finais = [q for q in estados if sorteio.random() < 0.4]
            m = criar(estados, ["a", "b"], "q0", finais, transicoes)
            for palavra in palavras:
                self.assertEqual(m.reconhece(palavra), aceita_por_configuracoes(m, palavra),
                                 (transicoes, finais, palavra))


class TestValidacao(unittest.TestCase):
    def _exige_erro(self, *args, **kwargs):
        with self.assertRaises(ErroDefinicao):
            criar(*args, **kwargs)

    def test_definicoes_invalidas(self):
        self._exige_erro([], ["a"], "q0", [], [])                                    # Q vazio
        self._exige_erro(["q0"], [], "q0", [], [])                                   # Σ vazio
        self._exige_erro(["q0"], ["ab"], "q0", [], [])                               # símbolo com 2 caracteres
        self._exige_erro(["q0"], ["ε"], "q0", [], [])                                # ε em Σ
        self._exige_erro(["q0"], ["a"], "q9", [], [])                                # q0 ∉ Q
        self._exige_erro(["q0"], ["a"], "q0", ["q9"], [])                            # F ⊄ Q
        self._exige_erro(["q0"], ["a"], "q0", [], [("q9", "a", ["q0"])])             # origem ∉ Q
        self._exige_erro(["q0"], ["a"], "q0", [], [("q0", "b", ["q0"])])             # símbolo ∉ Σ
        self._exige_erro(["q0"], ["a"], "q0", [], [("q0", "a", ["q9"])])             # destino ∉ Q
        self._exige_erro(["q 0"], ["a"], "q0", [], [])                               # espaço no nome

    def test_transicoes_repetidas_sao_unidas(self):
        m = criar(["q0", "q1", "q2"], ["a"], "q0", [],
                  [("q0", "a", ["q1"]), ("q0", "a", ["q2"])])
        self.assertEqual(m.transicao("q0", "a"), {"q1", "q2"})


class TestLeitor(unittest.TestCase):
    def escrever(self, nome, conteudo, binario=False):
        caminho = os.path.join(self.pasta.name, nome)
        with open(caminho, "wb" if binario else "w", **({} if binario else {"encoding": "utf-8"})) as f:
            f.write(conteudo)
        return caminho

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)

    def test_json_e_txt_equivalentes(self):
        txt = """
        # comentário
        Q: {q0, q1, q2}
        Sigma: a b c           # separado por espaços
        q0: q0
        F: q2
        delta:
        q0, a -> q0
        q0 ε -> {q1}
        q1, b → q1
        q1, eps -> q2
        q2, c -> q2
        palavras: abc, ""
        ε
        ab ba
        """
        m_txt, palavras, _ = carregar_arquivo(self.escrever("a.txt", txt))
        m_json, _, _ = carregar_arquivo(exemplo("ex1_a_b_c.json"))
        self.assertEqual(m_txt.delta, m_json.delta)
        self.assertEqual(m_txt.estados, m_json.estados)
        self.assertEqual(palavras, ["abc", "", "", "ab", "ba"])

    def test_json_com_apelidos_e_destino_unico_em_texto(self):
        json_ = ('{"Q": ["s", "t"], "Sigma": ["x"], "q0": "s", "F": ["t"], '
                 '"delta": {"s": {"x": "t", "": ["s"]}}, "testes": ["x", "", "ε"]}')
        m, palavras, _ = carregar_arquivo(self.escrever("b.json", json_))
        self.assertEqual(m.transicao("s", "x"), {"t"})
        self.assertEqual(m.transicao("s", EPSILON), {"s"})
        self.assertEqual(palavras, ["x", "", ""])

    def test_bom_utf8_e_arquivo_ansi(self):
        base = "estados: q0\nalfabeto: a\ninicial: q0\nfinais: q0\ntransicoes:\n# coment\u00e1rio\n"
        self.assertEqual(carregar_arquivo(self.escrever("bom.txt", b"\xef\xbb\xbf" + base.encode("utf-8"), True))[0].inicial, "q0")
        self.assertEqual(carregar_arquivo(self.escrever("ansi.txt", base.encode("cp1252"), True))[0].inicial, "q0")

    def erro_em(self, nome, conteudo, trecho):
        with self.assertRaises(ErroDefinicao) as contexto:
            carregar_arquivo(self.escrever(nome, conteudo))
        self.assertIn(trecho, str(contexto.exception))

    def test_erros_do_txt_citam_a_linha(self):
        self.erro_em("e1.txt", "estados: q0\nalfabeto: a\ninicial: q0\nfinais: q0\ntransicoes:\nq0 a q0\n", "linha 6")
        self.erro_em("e2.txt", "estados: q0\nsoltos\n", "linha 2")
        self.erro_em("e3.txt", "estados: q0\nestados: q1\n", "linha 2")
        self.erro_em("e4.txt", "estados: q0\n", "obrigatório")
        self.erro_em("e5.txt", "estados: q0\nalfabeto: 10, 11\ninicial: q0\nfinais: q0\ntransicoes:\n",
                     "único caractere")
        self.erro_em("e6.txt", "estados: q0\nTabela de transição:\n", "linha 2: rótulo desconhecido")

    def test_erros_do_json(self):
        self.erro_em("e1.json", "{ isto nao e json", "JSON inválido")
        self.erro_em("e2.json", '{"estados": ["q0"], "estados": ["q1"]}', "repetida")
        self.erro_em("e3.json", '{"estados": "q0"}', "lista")
        self.erro_em("e4.json", '[1, 2]', "objeto")

    def test_campo_desconhecido_gera_aviso(self):
        json_ = ('{"estados": ["q0"], "alfabeto": ["a"], "inicial": "q0", "finais": [], '
                 '"transicoes": {}, "autor": "x"}')
        _, _, avisos = carregar_arquivo(self.escrever("w.json", json_))
        self.assertTrue(any("autor" in aviso for aviso in avisos))

    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroDefinicao):
            carregar_arquivo(os.path.join(self.pasta.name, "nao_existe.json"))


class TestSaidaECLI(unittest.TestCase):
    def test_exemplos_rodam_e_dao_os_resultados_esperados(self):
        esperado = {
            "ex1_a_b_c.json": lambda w: list(w) == sorted(w),
            "ex2_termina_em_abb.txt": lambda w: w.endswith("abb"),
            "ex3_casos_de_borda.json": lambda w: w == "" or (w[0] == "0" and set(w) <= {"0", "1"}),
        }
        arquivos = sorted(glob.glob(os.path.join(PASTA_EXEMPLOS, "*")))
        self.assertEqual({os.path.basename(a) for a in arquivos}, set(esperado))
        for arquivo in arquivos:
            automato, palavras, _ = carregar_arquivo(arquivo)
            self.assertTrue(palavras)
            for palavra in palavras:
                self.assertEqual(automato.reconhece(palavra), esperado[os.path.basename(arquivo)](palavra),
                                 (arquivo, palavra))
            codigo, saida, erro = executar([arquivo])
            self.assertEqual((codigo, erro), (0, ""))
            self.assertEqual(saida.count("RESULTADO: "), len(palavras))

    def test_saida_traz_os_elementos_exigidos_no_enunciado(self):
        _, saida, _ = executar([exemplo("ex1_a_b_c.json"), "-p", "ab"])
        for trecho in ("Estados ativos iniciais = ε-fecho({q0}) = {q0, q1, q2}",
                       "[Passo 1] Símbolo lido: 'a'", "[Passo 2] Símbolo lido: 'b'",
                       "Estados ativos     = {q1, q2}", "Estados ativos ∩ F", "RESULTADO: ACEITA",
                       "RESULTADO: REJEITADA", "Justificativa", "Tabela de transição"):
            self.assertIn(trecho, saida)

    def test_opcao_palavra_e_palavra_vazia(self):
        codigo, saida, _ = executar([exemplo("ex2_termina_em_abb.txt"), "-p", "abb", "-p", ""])
        self.assertEqual(codigo, 0)
        self.assertIn("Palavra 11/12", saida)
        self.assertIn("Palavra 12/12: ε (palavra vazia)", saida)

    def test_modo_ascii_nao_usa_simbolos_especiais(self):
        for arquivo in glob.glob(os.path.join(PASTA_EXEMPLOS, "*")):
            _, saida, _ = executar([arquivo, "--ascii", "-p", ""])
            for glifo in "εΣδ∅∩≠→∪":
                self.assertTrue(glifo not in saida, f"{glifo!r} apareceu na saída ASCII de {arquivo}")
            self.assertIn("eps-fecho", saida)

    def test_estilo_cai_para_ascii_quando_o_terminal_nao_suporta_unicode(self):
        with mock.patch.object(sys, "stdout", types.SimpleNamespace(encoding="ascii")):
            self.assertIs(escolher_estilo(), ESTILO_ASCII)
        with mock.patch.object(sys, "stdout", types.SimpleNamespace(encoding="utf-8")):
            self.assertIs(escolher_estilo(), ESTILO_UNICODE)
        # o texto do --help tem ε: não pode quebrar num terminal sem Unicode
        terminal_ascii = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
        with mock.patch.object(sys, "stdout", terminal_ascii), self.assertRaises(SystemExit):
            cli.main(["--help"])

    def test_erros_devolvem_codigo_diferente_de_zero(self):
        codigo, _, erro = executar(["nao_existe.json"])
        self.assertEqual(codigo, 2)
        self.assertIn("ERRO", erro)

    def test_modo_interativo(self):
        respostas = iter(["ab", "", "ε", "sair"])
        with mock.patch("builtins.input", lambda prompt="": next(respostas)):
            codigo, saida, _ = executar([exemplo("ex1_a_b_c.json"), "-p", "c", "-i"])
        self.assertEqual(codigo, 0)
        self.assertIn("Modo interativo", saida)
        self.assertIn("Palavra 12: \"ab\"", saida)
        self.assertIn("Palavra 13: ε (palavra vazia)", saida)

    def test_computacao_vazia_e_impressa(self):
        m = carregar_arquivo(exemplo("ex1_a_b_c.json"))[0]
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            imprimir_computacao(m, m.simular(""), ESTILO_UNICODE, 1)
        self.assertIn("palavra vazia", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
