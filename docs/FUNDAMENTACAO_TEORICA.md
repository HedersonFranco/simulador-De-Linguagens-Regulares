# Fundamentação teórica — do AFD ao AFN-ε

Parte do básico e chega aos algoritmos implementados em `afn_epsilon/automato.py`. Serve de apoio
para a questão da 2ª avaliação sobre o trabalho (0,75 ponto).

## 1. Ponto de partida: autômato finito determinístico (AFD)

Um AFD lê uma palavra símbolo a símbolo e, a cada leitura, está em **exatamente um** estado.
Exemplo: palavras sobre {a, b} com número **par** de `a`.

| δ | a | b |
|---|---|---|
| → * p0 (par de a) | p1 | p0 |
| p1 (ímpar de a) | p0 | p1 |

(→ marca o estado inicial e * o estado final.)

Para `aba`: p0 —a→ p1 —b→ p1 —a→ p0. Terminou em p0 (final), então **aceita**.
Aqui δ(p, a) devolve **um** estado.

## 2. Não-determinismo: o AFN

Num AFN, δ(q, a) devolve um **conjunto** de estados (possivelmente vazio). A máquina "segue todos os
caminhos ao mesmo tempo": a palavra é aceita se **algum** caminho termina em estado final.

Exemplo: palavras sobre {a, b} que terminam em `ab`. Estados q0, q1, q2; F = {q2};
δ(q0, a) = {q0, q1}, δ(q0, b) = {q0}, δ(q1, b) = {q2}.

| Palavra | Após ler... | Conjunto de estados possíveis | Resultado |
|---|---|---|---|
| `aab` | início | {q0} | |
| | `a` | {q0, q1} | |
| | `a` | {q0, q1} (de q1 com `a` não sai nada) | |
| | `b` | {q0, q2} | q2 ∈ F → **aceita** |
| `abb` | `a`, `b`, `b` | {q0,q1} → {q0,q2} → {q0} | ∩ F = ∅ → **rejeita** |

A ideia de "acompanhar o conjunto de estados possíveis" é exatamente a do simulador.

## 3. Movimentos vazios: o AFN-ε

Um AFN-ε também pode mudar de estado **sem ler nenhum símbolo**, por uma transição ε
(a máquina "se teletransporta" para onde a transição aponta). Isso facilita compor autômatos
(união, concatenação e fecho de Kleene viram só ligações com ε — a construção de Thompson do `ex2`).

Exemplo (`ex1`): `a*b*c*`. q0 lê a's e passa a q1 **de graça** (ε); q1 lê b's e passa a q2 (ε); q2 lê c's.
Como o fecho-ε de q0 já inclui q2 (final), a palavra vazia é aceita.

## 4. Definição formal

Um AFN-ε é uma 5-upla **M = (Q, Σ, δ, q0, F)**:

* **Q**: conjunto finito de estados;
* **Σ**: alfabeto finito (ε ∉ Σ);
* **δ : Q × (Σ ∪ {ε}) → P(Q)**: função de transição (P(Q) = conjunto das partes de Q);
* **q0 ∈ Q**: estado inicial;
* **F ⊆ Q**: estados finais.

Na implementação: `delta[(estado, símbolo)]` é um `frozenset`; a ausência de chave significa ∅.

## 5. O fecho-ε

O **ε-fecho** de um estado q (também escrito ECLOSE(q) ou E(q)) é o conjunto dos estados alcançáveis
a partir de q seguindo **zero ou mais** transições ε. Todo estado pertence ao próprio fecho (zero passos).
Para um conjunto S: ε-fecho(S) = união dos ε-fechos dos seus elementos.

**Algoritmo implementado** (`fecho_epsilon`) — busca em largura só sobre as arestas ε:

```text
fecho ← S;  fila ← S
enquanto a fila não acabou:
    atual ← próximo da fila
    para cada d em δ(atual, ε):
        se d ∉ fecho:  acrescente d a fecho e ao fim da fila
devolva fecho
```

Exemplo com **ciclo** (`ex3`): q0 —ε→ q1 —ε→ q2 —ε→ q1, e q3 —ε→ q0.
ε-fecho({q3}) = {q3, q0, q1, q2}. A aresta q2 → q1 é vista, mas q1 já está em `fecho`, então não volta
para a fila: **cada estado entra uma única vez e o laço sempre termina**. Sem esse teste de "já visitado",
um ciclo de ε faria o programa girar para sempre.

## 6. Função de transição estendida e linguagem aceita

Para uma palavra w = a1 a2 ... an, o conjunto de **estados ativos** é:

```text
S0 = ε-fecho({q0})
Si = ε-fecho( δ(Si-1, ai) ),     onde  δ(S, a) = ⋃ δ(q, a), q ∈ S
L(M) = { w | Sn ∩ F ≠ ∅ }
```

**Por que o fecho-ε aparece em três lugares?** Os movimentos vazios podem acontecer *antes* do
primeiro símbolo (S0), *entre* símbolos e *depois* do último (ambos cobertos pelo ε-fecho de cada Si).
Esquecer o fecho no início rejeita a palavra vazia de `ex1`; esquecê-lo no fim rejeita palavras
que só chegam ao estado final por uma transição ε depois do último símbolo.

**Exemplo completo** (`ex1`, palavra `ba`): Q = {q0, q1, q2}, q0 inicial, F = {q2}.

```text
S0 = ε-fecho({q0})          = {q0, q1, q2}
lê b: δ(S0, b) = {q1}   →  S1 = ε-fecho({q1}) = {q1, q2}
lê a: δ(S1, a) = ∅      →  S2 = ε-fecho(∅)    = ∅
S2 ∩ F = ∅  →  REJEITADA
```

É o que o programa imprime (conferir a saída de `ba` no README).

## 7. Por que simular com conjuntos (e não com tentativa e erro)?

* **Backtracking** testa um caminho de cada vez e volta quando falha. Com não-determinismo, o número
  de caminhos pode crescer exponencialmente com o tamanho da palavra, e ciclos de ε podem causar laço infinito.
* **Simulação por conjuntos** (a do trabalho) mantém só o conjunto Si: no máximo |w| + 1 conjuntos,
  cada um com no máximo |Q| estados. Custo por palavra **O(|w| · (|Q| + |δ|))**; o fecho custa
  O(|Q| + #transições ε) (ignorando a ordenação usada só para imprimir os conjuntos em ordem estável).
* Cada Si é um **estado do AFD equivalente** obtido pela *construção de subconjuntos*; o simulador
  constrói só os que a palavra visita, sem gerar os até 2^|Q| subconjuntos. Por isso AFD, AFN e AFN-ε
  reconhecem exatamente as mesmas linguagens: as **linguagens regulares**.

## 8. Mapa teoria → código

| Teoria | Código (`afn_epsilon/automato.py`) |
|---|---|
| M = (Q, Σ, δ, q0, F) | classe `AFNEpsilon` (`estados`, `alfabeto`, `delta`, `inicial`, `finais`) |
| ε | constante `EPSILON = "ε"` (nunca pertence a Σ) |
| δ(q, a) | `transicao(q, a)` |
| ε-fecho(S) | `fecho_epsilon(S)` |
| δ(S, a) | `mover(S, a)` |
| S0, S1, ..., Sn e Sn ∩ F ≠ ∅ | `simular(w)`; rastro em `Computacao` e `Passo` |
| w ∈ L(M) | `reconhece(w)` |

## 9. Perguntas para estudar (com respostas curtas)

1. **O que é o fecho-ε e como foi calculado?** O conjunto dos estados alcançáveis com zero ou mais
   transições ε. Busca em largura sobre as arestas ε, com um conjunto de visitados.
2. **Por que aplicá-lo ao estado inicial e depois de cada símbolo?** Porque ε-movimentos podem ocorrer em
   qualquer momento da leitura: antes, entre e depois dos símbolos.
3. **Como o algoritmo evita laço infinito em ciclos de ε?** Só enfileira estados ainda fora do fecho; cada
   estado entra no máximo uma vez.
4. **O que significa o conjunto de estados ativos vazio?** Nenhum caminho sobreviveu; a palavra será
   rejeitada, e os símbolos restantes não mudam nada (δ(∅, a) = ∅).
5. **Por que a condição de aceitação é "interseção não vazia com F"?** Cada estado ativo é o fim de algum
   caminho possível; basta **um** terminar em estado final para a palavra ser aceita.
6. **E se um símbolo da palavra não pertencer a Σ?** Não existe transição para ele, o conjunto fica vazio
   e a palavra é rejeitada (w ∉ Σ\*, logo w ∉ L(M)).
7. **Qual a complexidade e por que não é exponencial?** O(|w| · (|Q| + |δ|)): guarda-se um subconjunto de Q
   por passo em vez de explorar todos os caminhos.
8. **Qual a relação com o AFD?** Cada conjunto de estados ativos é um estado do AFD da construção de
   subconjuntos; o simulador a executa "sob demanda", só para os conjuntos que a palavra visita.
9. **Para que servem as transições ε?** Compor autômatos (união, concatenação, fecho de Kleene) sem
   mexer nos componentes, como na construção de Thompson do `ex2`; não aumentam o poder de reconhecimento.
