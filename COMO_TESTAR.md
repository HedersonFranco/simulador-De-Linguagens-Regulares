# Como testar o simulador — passo a passo

Roteiro para conferir o trabalho do zero: preparar o ambiente, rodar os testes automatizados, rodar
os exemplos, conferir a saída pedida no enunciado e testar um autômato próprio. Os comandos valem
para Windows, Linux e macOS.

## Passo 1 — Conferir o Python

```bash
python --version
```

Precisa ser **Python 3.8 ou superior**. Se `python` não for reconhecido, use `py` (Windows) ou
`python3` (Linux/macOS) em todos os comandos deste roteiro. Não há nada para instalar nem compilar.

## Passo 2 — Abrir a pasta do projeto

* **Pelo .zip do SIGAA:** descompacte e entre na pasta `simulador_afn_epsilon`.
* **Pelo GitHub:**

  ```bash
  git clone https://github.com/HedersonFranco/simulador-De-Linguagens-Regulares.git
  cd simulador-De-Linguagens-Regulares
  ```

Todos os comandos a seguir são executados **dentro dessa pasta** (a que contém o `main.py`).

## Passo 3 — Rodar os testes automatizados

```bash
python -m unittest discover -s testes -v
```

**Esperado:** cada teste termina em `... ok`, e o final é:

```text
Ran 32 tests in ...s

OK
```

Os testes cobrem o fecho-ε (cadeias, ciclos, auto-laços), a simulação, a validação das definições, a
leitura de JSON/TXT, a saída e a linha de comando. Três deles verificam a simulação em massa; um compara
o simulador com um oráculo independente em 300 autômatos aleatórios (detalhes na seção 9 do
[README](README.md)).

## Passo 4 — Rodar os três exemplos

```bash
python main.py exemplos/ex1_a_b_c.json
python main.py exemplos/ex2_termina_em_abb.txt
python main.py exemplos/ex3_casos_de_borda.json
```

Cada execução mostra, nesta ordem: o autômato lido (M = (Q, Σ, δ, q0, F) e a tabela de transição,
para conferir que o arquivo foi lido certo), um bloco por palavra com a computação passo a passo e,
no final, um `RESUMO`. **Resumo esperado:**

| Exemplo | Linguagem | ACEITA | REJEITADA |
|---|---|---|---|
| `ex1_a_b_c.json` | `a*b*c*` | abc, ε, aabbcc, ac, bbb, aab | cba, abca, ba, abcabc |
| `ex2_termina_em_abb.txt` | `(a\|b)*abb` | abb, aabb, babb, abbabb, bbabb | ab, abba, abbb, bb, ε |
| `ex3_casos_de_borda.json` | `{ε} ∪ 0(0\|1)*` | ε, 0, 01, 0110 | 1, 10, 012, 2 |

No `ex3`, `012` e `2` são rejeitadas porque `2` não pertence a Σ (a saída mostra um `AVISO`), e o par
q1 ↔ q2 forma um **ciclo de ε**: o fecho-ε termina mesmo assim.

## Passo 5 — Conferir a saída pedida no enunciado (seção 3.2)

Em qualquer bloco de palavra:

| O enunciado pede | Onde aparece na saída |
|---|---|
| 1. o conjunto inicial de estados ativos, com o fecho-ε do estado inicial | linha `[Início] Estados ativos iniciais = ε-fecho({q0}) = ...` |
| 2. para cada símbolo, o caractere lido e o novo conjunto de estados ativos | `[Passo n] Símbolo lido: '...'` e a linha `Estados ativos = ...` |
| 3. `ACEITA` ou `REJEITADA`, justificado pela interseção com F | bloco `[Fim]`: `Estados ativos ∩ F`, `RESULTADO` e `Justificativa` |

A seção 5 do [README](README.md) mostra dois blocos completos: uma palavra aceita e uma rejeitada.

## Passo 6 — Testar outras palavras

Palavras extras pela linha de comando (`-p` pode ser repetido):

```bash
python main.py exemplos/ex1_a_b_c.json -p abbc -p ε
```

Para a palavra vazia use `ε` (ou `λ`). `-p ""` funciona no bash e no cmd, mas **não no PowerShell**, que
descarta o argumento vazio; lá, use `-p ε` ou `-p '""'`.

Modo interativo: depois das palavras do arquivo, o programa pede novas palavras, uma por linha;
`sair` encerra.

```bash
python main.py exemplos/ex2_termina_em_abb.txt -i
```

## Passo 7 — Testar com um autômato próprio

Crie o arquivo `meu_afn.txt` nesta pasta com o conteúdo abaixo:

```text
# a* ∪ b*: o estado inicial escolhe um dos ramos por transições vazias
estados: s, p, q
alfabeto: a, b
inicial: s
finais: p, q
transicoes:
s, ε -> p, q
p, a -> p
q, b -> q
palavras: ε, aaa, bb, ab
```

```bash
python main.py meu_afn.txt
```

**Esperado:** `ε`, `aaa` e `bb` ACEITAS; `ab` REJEITADA. A palavra vazia é aceita porque o conjunto
inicial já é ε-fecho({s}) = {s, p, q}, que contém estados finais.

Regras do formato (a versão JSON e os detalhes estão na seção 4 do [README](README.md)):

* um campo por linha, no formato `rótulo: valor`; `transicoes:` e `palavras:` continuam nas linhas
  seguintes;
* transição: `origem, símbolo -> destino1, destino2`; ε pode ser escrito `ε`, `λ`, `eps`, `epsilon` ou
  `lambda`;
* cada símbolo de Σ tem **um caractere**; palavras separadas por linha, vírgula ou espaço;
* `#` começa um comentário.

## Passo 8 — Conferir as mensagens de erro (opcional)

Altere uma linha do `meu_afn.txt` por vez e rode de novo:

| Alteração | Mensagem esperada |
|---|---|
| `finais: p, q9` | `ERRO: estados finais que não pertencem a Q: 'q9'.` |
| `transicoes:` trocado por `Tabela de transição:` | `ERRO: linha 6: rótulo desconhecido 'Tabela de transição'. ...` |
| `alfabeto: a, bb` | `ERRO: símbolo inválido no alfabeto: 'bb' (cada símbolo deve ser um único caractere).` |

E `python main.py nao_existe.json` mostra `ERRO: não foi possível ler 'nao_existe.json': ...`.
Em todos esses casos o programa termina com código de saída 2.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `python` não é reconhecido como comando | use `py` (Windows) ou `python3` (Linux/macOS) |
| `can't open file '...main.py'` | o terminal não está na pasta do projeto: volte ao passo 2 |
| `error: argument -p/--palavra: expected one argument` | o PowerShell descartou o `""`: use `-p ε` |
| `?` ou caracteres estranhos no lugar de ε, ∅, ∩ | rode com `--ascii` |
