# Trabalho 01 — Simulador de Linguagens Regulares (AFN-ε)

**Universidade Federal do Piauí — CCN / Departamento de Computação**
**Disciplina:** Teoria da Computação — **Professor:** Carlos André Batista de Carvalho

**Equipe:**

* Hederson Franco Benvindo Lima
* João Guilherme Oliveira Pereira
* David Soares Pereira Junior

Simulador e reconhecedor de **Autômatos Finitos Não-determinísticos com movimentos vazios
(AFN-ε)**. O programa lê a definição formal do autômato em um arquivo (JSON ou TXT), processa
uma lista de palavras e mostra, **passo a passo**, o conjunto de estados ativos até concluir
`ACEITA` ou `REJEITADA`.

## 1. Checklist do enunciado

| Exigência do PDF | Onde está atendida |
|---|---|
| Linguagem livre | Python 3 |
| Proibido usar bibliotecas de Teoria da Computação, Grafos ou Autômatos; fecho-ε e rastreamento feitos à mão | `afn_epsilon/automato.py` (`fecho_epsilon`, `mover`, `simular`); só biblioteca padrão (seção 8) |
| Pacote `.zip` com código-fonte e README com instruções | este pacote; seções 3 e 4 |
| Entrada (TXT ou JSON): Q, Σ, q0, F, tabela δ com transições ε e lista de palavras | seção 4 |
| Saída: conjunto inicial de estados ativos (com o fecho-ε do estado inicial) | linha `[Início]` |
| Saída: para cada símbolo lido, o caractere e o novo conjunto de estados ativos | blocos `[Passo n]` |
| Saída: `ACEITA`/`REJEITADA`, justificada pela interseção entre os estados ativos finais e F | bloco `[Fim]`, `RESULTADO` e `Justificativa` |
| Não ser uma "caixa-preta" | seção 5 (exemplo de saída) |

## 2. Requisitos de ambiente

* **Python 3.8 ou superior** (desenvolvido e testado com Python 3.12). Verifique com `python --version`
  (no Linux/macOS pode ser `python3`; no Windows, `py`).
* **Nenhuma dependência externa** (não há `pip install`) e **nenhuma etapa de compilação**:
  Python é interpretado, basta executar `main.py`.
* Terminal com UTF-8 para exibir `ε`, `∅`, `∩`, `δ`... Se o terminal não suportar, o programa
  troca sozinho para uma saída só com ASCII (ou use `--ascii`).

## 3. Como executar

Descompacte o `.zip`, entre na pasta do projeto e rode:

```bash
python main.py exemplos/ex1_a_b_c.json            # AFN-ε de a*b*c*          (JSON)
python main.py exemplos/ex2_termina_em_abb.txt    # (a|b)*abb por Thompson   (TXT)
python main.py exemplos/ex3_casos_de_borda.json   # ciclo de ε, palavra vazia, símbolo fora de Σ
```

Opções (todas opcionais):

| Opção | Efeito |
|---|---|
| `-p PALAVRA`, `--palavra PALAVRA` | testa também esta palavra; pode repetir. `-p ""` (ou `-p ε`) é a palavra vazia |
| `-i`, `--interativo` | depois das palavras do arquivo, pede novas palavras no teclado (`sair` ou Ctrl+D encerra) |
| `--ascii` | saída só com ASCII (`eps`, `{}`, `inter`, `delta`...) |
| `-h`, `--help` | ajuda |

Exemplos: `python main.py exemplos/ex1_a_b_c.json -p abbc -p ""` e
`python main.py exemplos/ex2_termina_em_abb.txt -i`.

**Código de saída:** `0` = executou; `1` = não havia palavra para testar; `2` = arquivo ausente
ou com erro (a mensagem, em `stderr`, diz o que corrigir — em TXT, com o número da linha).

## 4. Estrutura dos arquivos de teste

O arquivo descreve o autômato **M = (Q, Σ, δ, q0, F)** e as palavras a testar. O formato é
escolhido pela extensão (`.json` ou `.txt`). Mesmo conteúdo nos dois formatos abaixo
(autômato de `a*b*c*`):

### 4.1 JSON

```json
{
  "nome": "a*b*c*",
  "descricao": "todos os a antes dos b e todos os b antes dos c",
  "estados": ["q0", "q1", "q2"],
  "alfabeto": ["a", "b", "c"],
  "inicial": "q0",
  "finais": ["q2"],
  "transicoes": {
    "q0": { "a": ["q0"], "ε": ["q1"] },
    "q1": { "b": ["q1"], "ε": ["q2"] },
    "q2": { "c": ["q2"] }
  },
  "palavras": ["abc", "", "cba"]
}
```

| Campo | Tipo | Obrigatório | Significado |
|---|---|---|---|
| `estados` | lista de textos | sim | conjunto Q (sem espaços nem vírgulas nos nomes) |
| `alfabeto` | lista de textos de **1 caractere** | sim | alfabeto Σ |
| `inicial` | texto | sim | estado inicial q0 (deve estar em Q) |
| `finais` | lista de textos | sim | conjunto F ⊆ Q (pode ser `[]`) |
| `transicoes` | objeto `{estado: {símbolo: [destinos]}}` | sim | tabela δ. Destinos é uma lista (ou um texto, se for um só). O que não aparece é δ = ∅ |
| `palavras` | lista de textos | não | palavras de teste (`""` ou `"ε"` = palavra vazia) |
| `nome`, `descricao` | texto | não | mostrados no cabeçalho da saída |

### 4.2 TXT

```text
# comentários começam com '#'
nome: a*b*c*
descricao: todos os a antes dos b e todos os b antes dos c
estados: q0, q1, q2
alfabeto: a, b, c
inicial: q0
finais: q2
transicoes:
q0, a -> q0
q0, ε -> q1
q1, b -> q1
q1, ε -> q2
q2, c -> q2
palavras:
abc
ε
cba
```

* `estados`, `alfabeto`, `inicial` e `finais` levam o valor **na mesma linha** do rótulo
  (separado por vírgulas e/ou espaços; chaves `{q0, q1}` são opcionais).
* `transicoes:` e `palavras:` ocupam as linhas seguintes. Transição: `origem, símbolo -> destino1, destino2`
  (a seta `→` também vale). Linhas repetidas com a mesma origem e o mesmo símbolo **se unem**
  (é assim que se escreve o não-determinismo). Palavras: uma por linha (ou separadas por vírgula).
* Comentário: `#` no começo da linha ou depois de um espaço.

### 4.3 Regras comuns

* **Transição vazia (ε):** escreva `ε`, `λ`, `eps`, `epsilon` ou `lambda` (qualquer caixa). No JSON, a chave
  vazia `""` também vale. Se o seu editor não digita `ε`, use `eps`.
* **Palavra vazia:** `ε`, `λ` ou `""` (no TXT uma linha em branco é ignorada, por isso a marca explícita).
* **Símbolos de Σ:** um único caractere; não podem ser espaço, vírgula, `#`, `ε` nem `λ`.
* **Apelidos de campos** (maiúsculas/minúsculas não importam): `Q`; `Sigma`/`Σ`; `q0`/`estado_inicial`;
  `F`/`estados_finais`; `delta`/`δ`/`transições`; `cadeias`/`testes`.
* **Validação:** estado inicial ou final fora de Q, transição com estado/símbolo desconhecido, campo
  ausente, JSON malformado etc. geram uma mensagem de erro clara. Campos desconhecidos geram um `AVISO`.
* **Símbolo fora de Σ numa palavra de teste:** a palavra não pertence a Σ\*, então é `REJEITADA`;
  a saída marca o símbolo com um `AVISO`.
* Codificação: UTF-8 (com ou sem BOM; arquivos "ANSI" do Windows também são lidos).

## 5. Saída do programa

Primeiro o autômato lido (para conferir o parser), depois um bloco por palavra e, no fim, um resumo.
Trecho real de `python main.py exemplos/ex1_a_b_c.json` (palavra aceita):

```text
========================================================================
 Palavra 1/10: "abc"
========================================================================
 [Início] Estados ativos iniciais = ε-fecho({q0}) = {q0, q1, q2}
      ε-transições percorridas: q0 -ε-> q1, q1 -ε-> q2
 [Passo 1] Símbolo lido: 'a'
      δ({q0, q1, q2}, a) = {q0}
      ε-fecho({q0})      = {q0, q1, q2}
         ε-transições percorridas: q0 -ε-> q1, q1 -ε-> q2
      Estados ativos     = {q0, q1, q2}
 [Passo 2] Símbolo lido: 'b'
      δ({q0, q1, q2}, b) = {q1}
      ε-fecho({q1})      = {q1, q2}
         ε-transições percorridas: q1 -ε-> q2
      Estados ativos     = {q1, q2}
 [Passo 3] Símbolo lido: 'c'
      δ({q1, q2}, c) = {q2}
      ε-fecho({q2})  = {q2}
      Estados ativos = {q2}
 [Fim] Palavra lida por completo
      Estados ativos finais = {q2}
      Estados finais F      = {q2}
      Estados ativos ∩ F    = {q2}  (≠ ∅)
 RESULTADO: ACEITA
 Justificativa: a interseção entre os estados ativos finais e F é
                NÃO-VAZIA ({q2}): há estado final ativo ao fim da
                leitura.
```

Palavra rejeitada (`"ba"`, do mesmo arquivo):

```text
 [Início] Estados ativos iniciais = ε-fecho({q0}) = {q0, q1, q2}
      ε-transições percorridas: q0 -ε-> q1, q1 -ε-> q2
 [Passo 1] Símbolo lido: 'b'
      δ({q0, q1, q2}, b) = {q1}
      ε-fecho({q1})      = {q1, q2}
         ε-transições percorridas: q1 -ε-> q2
      Estados ativos     = {q1, q2}
 [Passo 2] Símbolo lido: 'a'
      δ({q1, q2}, a) = ∅
      ε-fecho(∅)     = ∅
      Estados ativos = ∅
      Nenhum estado ativo: todos os ramos da computação morreram.
 [Fim] Palavra lida por completo
      Estados ativos finais = ∅
      Estados finais F      = {q2}
      Estados ativos ∩ F    = ∅
 RESULTADO: REJEITADA
 Justificativa: não há estados ativos ao fim da leitura, logo a
                interseção com F é VAZIA (∅).
```

Como ler: `δ(S, a)` é o conjunto alcançado lendo `a` a partir dos estados ativos `S`; o `ε-fecho`
acrescenta tudo o que se alcança de graça por transições vazias; o resultado é o novo conjunto de
**estados ativos**. Ao fim da palavra, ela é aceita se, e somente se, **estados ativos ∩ F ≠ ∅**.

## 6. Estrutura do projeto

```text
simulador_afn_epsilon/
├── README.md                     este arquivo
├── main.py                       programa principal (linha de comando)
├── afn_epsilon/
│   ├── __init__.py
│   ├── automato.py               NÚCLEO: classe AFNEpsilon, fecho_epsilon, mover, simular
│   ├── leitor.py                 leitura e validação dos arquivos JSON/TXT
│   └── saida.py                  formatação da saída passo a passo
├── exemplos/
│   ├── ex1_a_b_c.json            a*b*c* (JSON, cadeia de ε)
│   ├── ex2_termina_em_abb.txt    (a|b)*abb por Thompson (TXT, 11 estados, laço do fecho de Kleene)
│   └── ex3_casos_de_borda.json   ciclo de ε, palavra vazia aceita, símbolo fora de Σ
├── testes/
│   └── test_afn.py               testes automatizados (unittest)
└── docs/
    └── FUNDAMENTACAO_TEORICA.md  teoria do zero, algoritmos e perguntas para estudar
```

## 7. Como funciona

Cada instante da computação é descrito por um **conjunto de estados ativos** `S`:

```text
S0 = ε-fecho({q0})                       conjunto inicial
Si = ε-fecho( δ(Si-1, ai) )              para cada símbolo ai lido
w é aceita  ⇔  Sn ∩ F ≠ ∅
```

* `fecho_epsilon(S)` — busca em largura que parte de `S` e segue **só** as transições ε, guardando os
  estados já visitados (por isso termina mesmo com ciclos de ε). Custo O(|Q| + #transições ε).
* `mover(S, a)` — união de δ(q, a) para todo q ∈ S.
* `simular(w)` — aplica as duas funções símbolo a símbolo, registra cada passo (usado na saída) e
  testa a interseção com F no final.

Custo por palavra: O(|w| · (|Q| + |δ|)), sem backtracking. A teoria completa, com exemplos e
perguntas de estudo, está em [`docs/FUNDAMENTACAO_TEORICA.md`](docs/FUNDAMENTACAO_TEORICA.md).

## 8. Restrição de bibliotecas

Cumprindo o enunciado, **não há** biblioteca de Teoria da Computação, de Teoria dos Grafos ou de
autômatos (nem `re`, `networkx`, `automata-lib`...). O fecho-ε e o rastreamento das transições são
implementados à mão em `afn_epsilon/automato.py`. Só entra a biblioteca padrão do Python, para tarefas
que nada têm a ver com autômatos: `json` e `os` (leitura de arquivos), `argparse` e `sys` (linha de
comando), `dataclasses` e `typing` (registros de dados), `textwrap` (quebra de linha na saída).
Os testes usam também `unittest`, `itertools`, `random` e `tempfile`.

## 9. Testes automatizados

```bash
python -m unittest discover -s testes -v
```

São 32 testes: fecho-ε (cadeias, ciclos, auto-laços), passo e simulação, validação das definições,
leitura de JSON/TXT, saída e linha de comando. Dois deles confrontam o simulador com um **oráculo
independente** (busca no grafo de configurações *(estado, posição)*, que é a definição de computação):
todas as palavras de até 8 símbolos no `ex2` e de até 7 no `ex1`, e 300 autômatos aleatórios com todas as palavras de até 5 símbolos.

## 10. Decisões de projeto

* Cada símbolo de Σ é **um caractere**, e uma palavra é uma sequência de caracteres.
* Os conjuntos aparecem na **ordem de declaração** de Q (saída determinística; `q10` não vem antes de `q2`).
* A computação continua até o fim da palavra mesmo que o conjunto de estados ativos já esteja vazio,
  para mostrar um passo por símbolo lido, como pede o enunciado.
* A lógica (`automato.py`) é separada da leitura (`leitor.py`) e da apresentação (`saida.py`).
