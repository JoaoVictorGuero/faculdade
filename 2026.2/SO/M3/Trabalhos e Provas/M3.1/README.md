# Simulador de Sistema de Arquivos em Memória

> **Disciplina:** Sistemas Operacionais  
> **Linguagem:** C (Padrão C99 / POSIX)  
> **Ambiente:** Linux / macOS  

---

## 1. Instruções de Compilação e Execução

### 1.1. Pré-requisitos
* Compilador C compatível com POSIX: **GCC** ou **Clang**.
* Sistema operacional: **Linux**, **macOS** ou **WSL (Windows Subsystem for Linux)**.
* Nenhuma biblioteca externa proprietária ou de terceiros é necessária (o simulador utiliza estritamente as bibliotecas padrão do C e cabeçalhos POSIX `termios.h` e `unistd.h`).

### 1.2. Compilação
Abra o terminal no diretório do projeto e execute:

```bash
gcc -Wall -Wextra main.c -o simulador
```

* `-Wall`: ativa avisos sobre construções suspeitas no código.
* `-Wextra`: ativa avisos adicionais para assegurar a melhor qualidade de código.
* `-o simulador`: gera o arquivo binário executável denominado `simulador`.

### 1.3. Execução Interativa
Para iniciar o terminal simulado:

```bash
./simulador
```

#### Recursos do Terminal Interativo:
* **Navegação com Setas (↑ / ↓)**: navega pelo histórico de comandos anteriores (seta para cima) e retorna aos mais recentes (seta para baixo), preservando o rascunho em digitação.
* **Edição de Linha (← / →, Backspace, Delete)**: permite mover o cursor e editar qualquer posição da linha em tempo real.
* **Atalhos Úteis**:
  * `Ctrl + A`: move o cursor para o início da linha.
  * `Ctrl + E`: move o cursor para o fim da linha.
  * `Ctrl + L`: limpa a tela e redesenha o prompt atual.
  * `Ctrl + C`: descarta o comando atual e gera um novo prompt.
  * `Ctrl + D`: encerra o simulador (quando a linha estiver vazia).

### 1.4. Execução em Lote / Redirecionamento (Pipes e Scripts)
O simulador detecta automaticamente se a entrada é um terminal interativo (`isatty(STDIN_FILENO)`). Caso um arquivo ou pipe seja fornecido, o simulador desativa o modo *raw* e processa os comandos via fluxo de entrada padrão:

```bash
./simulador < comandos.txt
```

---

## 2. Escolhas de Design e Estruturas de Dados

O simulador modela o sistema de arquivos inteiramente em memória primária (RAM), utilizando abstrações que espelham diretamente o funcionamento de discos rígidos e sistemas de arquivos reais da família UNIX.

### 2.1. Representação do Disco Físico e Mapa de Ocupação
O disco simulado foi projetado de forma modular com constantes configuráveis:

```c
#define NUM_BLOCOS 64       /* Quantidade total de blocos (64 blocos) */
#define TAM_BLOCO 16        /* Capacidade de cada bloco (16 bytes)    */
#define MAX_BLOCOS_ARQ 16   /* Limite por arquivo (16 x 16 = 256 bytes)*/

char disco[NUM_BLOCOS][TAM_BLOCO]; /* Matriz que representa os setores físicos */
int bloco_ocupado[NUM_BLOCOS];     /* Vetor bitmap de alocação (0 = livre, 1 = ocupado) */
```

* **Por que bloco de 16 bytes?** Um tamanho intencionalmente reduzido permite observar claramente a divisão e o espalhamento de dados pequenos através de múltiplos blocos e demonstrar a fragmentação interna na prática.
* **Bitmap / Vetor de Ocupação:** Em sistemas operacionais reais, o bitmap de blocos livres reside em estruturas de controle no disco (como no Superbloco/Descritores de Grupo do ext2/ext3). No simulador, o vetor `bloco_ocupado` fornece busca $O(n)$ direta por blocos livres com complexidade mínima e clareza didática.

---

### 2.2. O Bloco de Controle de Arquivo (`struct FCB`)
A estrutura `FCB` (File Control Block) representa o equivalente ao **inode** do UNIX somado aos atributos de diretório:

```c
typedef struct FCB {
    int inode;                  /* Identificador numérico único do arquivo */
    char nome[64];              /* Nome do arquivo no diretório */
    int tamanho;                /* Tamanho lógico do conteúdo em bytes */
    TipoArquivo tipo;           /* TIPO_CARACTERE, NUMERICO, BINARIO, PROGRAMA */
    time_t data_criacao;        /* Timestamp de criação (time_t) */
    time_t data_modificacao;    /* Timestamp da última alteração de conteúdo/metadados */
    time_t data_acesso;         /* Timestamp da última leitura (cat/cp) ou execução */
    int permissoes;             /* Máscara de bits em octal (ex: 0644, 0755) */
    int blocos[MAX_BLOCOS_ARQ]; /* Tabela de índices (aponta para blocos do disco) */
    int qtd_blocos;             /* Quantidade de blocos atualmente associados */
    struct FCB *prox;           /* Ponteiro para encadeamento de arquivos no diretório */
} FCB;
```

* **Ponteiro de Encadeamento (`prox`):** Cada diretório armazena seus arquivos em uma lista simplesmente encadeada de FCBs, permitindo adicionar e remover arquivos dinamicamente via `malloc()` e `free()` sem limite rígido de arquivos por pasta.

---

### 2.3. A Árvore de Diretórios (`struct Diretorio`)
Para permitir profundidade arbitrária de subpastas e isolamento entre diretórios, utilizou-se a estrutura clássica de árvore n-ária representada como **First-Child Next-Sibling** com ponteiro para o nó pai:

```c
typedef struct Diretorio {
    char nome[64];              /* Nome da pasta ("/" na raiz) */
    struct Diretorio *pai;      /* Ponteiro para o diretório superior (NULL na raiz) */
    struct Diretorio *filhos;   /* Ponteiro para a primeira subpasta (First-Child) */
    struct Diretorio *prox;     /* Ponteiro para a pasta irmã no mesmo nível (Next-Sibling) */
    FCB *arquivos;              /* Lista encadeada de arquivos contidos nesta pasta */
} Diretorio;
```

---

## 3. Discussão Teórica e Demonstração no Trabalho

### 3.1. Conceito de Arquivo e seus Atributos
Na teoria de Sistemas Operacionais, um arquivo é uma **abstração lógica** mantida pelo sistema operacional que mapeia uma sequência linear de bytes em dispositivos de armazenamento secundário não voláteis.

O simulador materializa essa definição separando rigidamente os **metadados** (mantidos no `FCB`) dos **dados físicos** (armazenados na matriz `disco`):

| Atributo Teórico | Campo na `struct FCB` | Descrição e Papel no Simulador |
| :--- | :--- | :--- |
| **Identificador Único** | `int inode` | Número incremental não reutilizado durante a sessão que identifica o arquivo independentemente de seu nome. |
| **Nome** | `char nome[64]` | Rótulo simbólico para localização humana dentro do diretório. |
| **Tipo** | `TipoArquivo tipo` | Enumeração (`CARACTERE`, `NUMERICO`, `BINARIO`, `PROGRAMA`) definindo a natureza do arquivo. |
| **Tamanho** | `int tamanho` | Quantidade exata de bytes válidos no arquivo, impedindo que o comando `cat` leia lixo de memória ao final do último bloco. |
| **Datas e Horários** | `data_criacao`, `data_modificacao`, `data_acesso` | Timestamps padrão UNIX atualizados pontualmente a cada leitura, escrita ou criação. |
| **Proteção** | `int permissoes` | 9 bits determinando privilégios de Leitura, Escrita e Execução para Dono, Grupo e Outros. |
| **Localização Física** | `int blocos[]` | Tabela de endereços diretos indicando quais blocos do disco compõem o conteúdo do arquivo. |

---

### 3.2. Operações com Arquivos
O trabalho implementa as operações fundamentais exigidas para um sistema de arquivos:

1. **Criação (`touch <nome> [tipo]`)**:
   * Valida unicidade de nome no diretório corrente e integridade dos caracteres.
   * Aloca dinamicamente o `FCB` via `malloc()`.
   * Inicializa o inode, timestamps e permissões padrão (`0644` para arquivos comuns e `0755` para programas).
2. **Escrita (`echo <nome> <texto>`)**:
   * Verifica se o usuário atual possui permissão de escrita (`PERM_W`).
   * Libera os blocos alocados anteriormente pelo arquivo para evitar vazamento de blocos no disco (*re-alocação limpa*).
   * Calcula quantos blocos de 16 bytes são necessários: $\lceil \text{tamanho} / 16 \rceil$.
   * Varre o vetor `bloco_ocupado` alocando os primeiros blocos livres encontrados e copia fatias de até 16 bytes em `disco[bloco_idx]`.
   * Atualiza `tamanho`, `qtd_blocos` e `data_modificacao`.
3. **Leitura (`cat <nome>`)**:
   * Valida permissão de leitura (`PERM_R`).
   * Percorre sequencialmente a tabela de índices `blocos[]`, imprimindo apenas os caracteres válidos de cada bloco até atingir `tamanho`.
   * Atualiza `data_acesso`.
4. **Execução (`exec <nome>`)**:
   * Valida permissão de execução (`PERM_X`).
   * Verifica se o arquivo é do tipo `programa`. Se válido, simula a carga e execução com indicação de processo ativo; caso contrário, rejeita a operação com código de erro descritivo.
   * Atualiza `data_acesso`.
5. **Exclusão (`rm <nome>`)**:
   * Desaloca todos os blocos do arquivo no vetor `bloco_ocupado` e limpa seus bytes no disco.
   * Desconecta o `FCB` da lista encadeada do diretório.
   * Libera a memória da struct com `free()`, prevenindo *memory leaks*.
6. **Cópia (`cp <orig> <dest>`)**:
   * Valida permissão de leitura na origem.
   * Cria um novo FCB independente no diretório de destino com novo `inode`.
   * Aloca novos blocos no disco e duplica o conteúdo integralmente (cópia profunda / *deep copy*).
7. **Movimentação / Renomeação (`mv <orig> <dest>`)**:
   * Se o destino for um novo nome na mesma pasta: apenas renomeia o arquivo e atualiza o timestamp de modificação.
   * Se o destino for um subdiretório: remove o FCB da lista do diretório de origem e o insere na lista do diretório de destino, sem necessidade de copiar os blocos de dados no disco (operação $O(1)$ de metadados, exatamente como em sistemas de arquivos reais).

---

### 3.3. File Control Block (FCB) vs. "Inode" Simulado
Em sistemas de arquivos clássicos (como FAT), o FCB é uma entrada de diretório que contém tanto o nome quanto os ponteiros para os dados. Já em sistemas POSIX (como o ext4), a estrutura do **inode** fica dissociada do nome do arquivo, e o diretório funciona como uma tabela de mapeamento entre `(nome, inode)`.

No nosso simulador:
* Cada arquivo possui um `inode` numérico exclusivo gerenciado pelo contador sequencial global `proximo_inode`.
* Toda a tabela de endereçamento físico (`blocos[]`) e as propriedades de proteção (`permissoes`) são centralizadas no `FCB`.
* Ao mover um arquivo para outra pasta (`mv`), os blocos físicos e o número de inode permanecem intactos, demonstrando na prática a independência entre a localização hierárquica e os descritores do arquivo.

---

### 3.4. Estrutura de Diretórios em Árvore e suas Vantagens
O projeto implementa uma **estrutura hierárquica em árvore** partindo da raiz (`/`). As principais vantagens teóricas demonstradas são:

1. **Eficiência de Busca**: Em vez de percorrer uma lista linear de todos os arquivos existentes no sistema, a busca limita-se apenas aos irmãos do diretório atual ou ao caminho percorrido nó a nó.
2. **Nomeação e Espaço de Nomes Flexível**: Arquivos com nomes idênticos podem coexistir sem colisão de identificadores, desde que situados em diretórios diferentes (por exemplo, `/docs/relatorio.txt` e `/backup/relatorio.txt`).
3. **Agrupamento Lógico**: Permite que o usuário organize arquivos segundo critérios funcionais, projetos ou classes de acesso.
4. **Resolução de Caminhos Absolutos e Relativos**:
   * **Caminho Absoluto:** Iniciado com `/` (ex: `cd /docs/trabalhos`), o algoritmo inicia a busca na raiz global `raiz`.
   * **Caminho Relativo:** Não iniciado com `/` (ex: `cd trabalhos`), a busca avança a partir do ponteiro `atual`.
   * **Navegação de Retorno (`..`):** O comando `cd ..` acessa diretamente o ponteiro `atual->pai`, retrocedendo níveis na árvore com complexidade $O(1)$.

---

### 3.5. Mecanismo de Proteção e Chmod com Bitmasks

#### 3.5.1. Matriz de Acesso POSIX (9 bits)
As permissões são armazenadas em uma variável inteira utilizando uma representação octal clássica de 9 bits:

$$\underbrace{r \quad w \quad x}_{\text{Dono (bits 8..6)}} \quad \underbrace{r \quad w \quad x}_{\text{Grupo (bits 5..3)}} \quad \underbrace{r \quad w \quad x}_{\text{Outros (bits 2..0)}}$$

Onde cada bit corresponde a:
* **$r$ (Read - Leitura):** Peso 4 ($100_2$). Permite ler o conteúdo (`cat`, `cp`).
* **$w$ (Write - Escrita):** Peso 2 ($010_2$). Permite alterar conteúdo (`echo`) ou excluir (`rm`).
* **$x$ (eXecute - Execução):** Peso 1 ($001_2$). Permite executar o arquivo (`exec`).

Exemplo: permissão octal `0755`:
* Dono: $7 = 4 + 2 + 1 \implies rwx$ ($111_2$)
* Grupo: $5 = 4 + 0 + 1 \implies r-x$ ($101_2$)
* Outros: $5 = 4 + 0 + 1 \implies r-x$ ($101_2$)

#### 3.5.2. Verificação de Acesso com Bitwise (`tem_permissao`)
Para checar se um usuário tem permissão para realizar uma operação, a função `tem_permissao` utiliza operadores de deslocamento (`>>`) e máscara lógica (`& 7`):

```c
int shift = 0;
if (usuario_atual == DONO) shift = 6;       /* Isola bits 8..6 */
else if (usuario_atual == GRUPO) shift = 3; /* Isola bits 5..3 */
                                            /* Outros: shift = 0 */

int perm_classe = (arq->permissoes >> shift) & 7;

if ((perm_classe & op) == 0) {
    /* Permissão negada! */
    return 0;
}
return 1;
```

#### 3.5.3. Alteração com `chmod <octal> <nome>`
A função `cmd_chmod` recebe a representação textual do octal (ex: `"755"`), valida os 3 dígitos entre 0 e 7 e converte via base 8:
```c
int nova_perm = (int)strtol(octal, NULL, 8);
```

#### 3.5.4. Troca de Identidade com `user`
O comando `user <dono|grupo|outros>` permite alterar em tempo de execução a variável global `usuario_atual`, possibilitando testar imediatamente os bloqueios de permissão para leitura, escrita e execução sem reiniciar o programa.

---

### 3.6. Estratégias de Alocação de Blocos e a Escolha da Alocação Indexada

A disciplina de Sistemas Operacionais apresenta três abordagens fundamentais para organização física de arquivos:

| Abordagem | Funcionamento | Vantagens | Desvantagens |
| :--- | :--- | :--- | :--- |
| **Alocação Contínua** | O arquivo ocupa um conjunto linear contíguo de blocos. | Acesso sequencial e aleatório extremamente rápido ($O(1)$). | **Fragmentação externa severa**; dificuldade de expansão do arquivo sem realocação total. |
| **Alocação Encadeada** | Cada bloco contém um ponteiro armazenando o endereço do próximo bloco. | Sem fragmentação externa; arquivos podem crescer livremente. | Acesso direto/aleatório lento ($O(n)$); perda de um ponteiro compromete o arquivo inteiro; desperdício de bytes por bloco para ponteiros. |
| **Alocação Indexada (Adotada)** | Cada arquivo possui uma tabela de índices direta no seu descritor (`FCB->blocos[]`) apontando para seus blocos. | **Sem fragmentação externa**; suporte a acesso aleatório direto $O(1)$; blocos podem estar espalhados em qualquer região livre do disco. | Sobrecarga de espaço para armazenar a tabela de índices em arquivos muito pequenos. |

#### Implementação no Projeto:
O simulador utiliza **Alocação Indexada**. O vetor `FCB->blocos` armazena até `MAX_BLOCOS_ARQ` (16) índices de blocos. O comando `disco` renderiza uma grade visual com a ocupação de todos os 64 blocos (`#` para bloco ocupado e `.` para bloco livre), permitindo visualizar o espalhamento não-contíguo dos blocos de dados pelo disco:

```
Disco (64 blocos de 16 bytes) - Ocupados: 5 | Livres: 59
#####...........
................
................
................
```

---

## 4. Exemplos de Uso e Comparação com o Linux

A tabela abaixo compara os comandos do simulador com os comandos reais de um terminal UNIX/Linux:

| Comando no Simulador | Comando Linux Equivalente | Descrição |
| :--- | :--- | :--- |
| `mkdir docs` | `mkdir docs` | Cria a pasta `docs` no diretório corrente. |
| `cd docs` / `cd ..` / `cd /` | `cd docs` / `cd ..` / `cd /` | Navega entre diretórios (relativo, pai ou raiz). |
| `pwd` | `pwd` | Exibe o caminho absoluto do diretório atual. |
| `ls` | `ls -la` | Lista subdiretórios e arquivos com permissões, tipo, tamanho e datas. |
| `touch texto.txt` | `touch texto.txt` | Cria um arquivo vazio do tipo caractere. |
| `touch app programa` | `touch app` | Cria um programa executável com permissão `0755` por padrão. |
| `echo texto.txt Ola Mundo` | `echo "Ola Mundo" > texto.txt` | Grava o conteúdo nos blocos de disco do arquivo. |
| `cat texto.txt` | `cat texto.txt` | Lê e exibe o conteúdo armazenado nos blocos. |
| `exec app` | `./app` | Executa o arquivo se o bit `x` estiver ativo e for programa. |
| `chmod 600 texto.txt` | `chmod 600 texto.txt` | Altera as permissões (somente leitura/escrita para o dono). |
| `cp texto.txt copia.txt` | `cp texto.txt copia.txt` | Clona o arquivo alocando novos blocos no disco. |
| `mv texto.txt docs/` | `mv texto.txt docs/` | Move ou renomeia o arquivo. |
| `rm texto.txt` | `rm texto.txt` | Remove o arquivo e libera seus blocos de disco. |
| `stat texto.txt` | `stat texto.txt` | Mostra todos os atributos do FCB e a tabela de blocos. |
| `disco` | `df -h` / mapa de blocos | Exibe o mapa visual de blocos livres e ocupados no disco. |
| `user grupo` | `su -` / `newgrp` | Troca o usuário simulado para testar permissões. |
| `help` | `help` / `man` | Exibe a lista sintética de comandos aceitos. |
| `exit` | `exit` | Encerra a execução e desaloca toda a memória dinamicamente. |

---

### 4.1. Roteiro Prático de Demonstração

Abaixo segue uma sequência passo a passo para demonstrar todas as funcionalidades do simulador:

```bash
# 1. Iniciar o simulador
./simulador

# 2. Criar estrutura de diretórios e navegar
[dono:/]$ mkdir documentos
[dono:/]$ mkdir programas
[dono:/]$ cd documentos
[dono:/documentos]$ pwd
/documentos

# 3. Criar arquivos e escrever dados
[dono:/documentos]$ touch nota.txt
[dono:/documentos]$ echo nota.txt Sistemas Operacionais M3
[dono:/documentos]$ cat nota.txt
Sistemas Operacionais M3

# 4. Inspecionar o FCB e o disco
[dono:/documentos]$ stat nota.txt
[dono:/documentos]$ disco

# 5. Criar e executar um programa
[dono:/documentos]$ cd /programas
[dono:/programas]$ touch calculadora programa
[dono:/programas]$ exec calculadora
[Executando 'calculadora'] Processo simulado finalizado com sucesso.

# 6. Testar o mecanismo de proteção (Permissões RWX)
[dono:/programas]$ chmod 700 calculadora
[dono:/programas]$ user outros
[outros:/programas]$ exec calculadora
Erro: Permissao negada para 'calculadora' (usuario: outros).

# 7. Retornar ao dono e mover arquivo
[outros:/programas]$ user dono
[dono:/programas]$ mv calculadora /documentos/
[dono:/programas]$ cd /documentos
[dono:/documentos]$ ls

# 8. Sair com liberação limpa de memória
[dono:/documentos]$ exit
Memoria liberada. Ate logo!
```

---

## 5. Gerenciamento de Memória e Valgrind

Todas as estruturas de dados (`Diretorio` e `FCB`) e seus blocos associados são gerenciados dinamicamente via `malloc()`. Na finalização do simulador (`exit` ou `Ctrl+D`), a função recursiva `liberar_tudo(raiz)` percorre toda a árvore de diretórios liberando todos os FCBs, blocos do disco e estruturas de nós, garantindo **zero vazamentos de memória (zero memory leaks)**.

Para checar com Valgrind em ambiente Linux:
```bash
valgrind --leak-check=full --show-leak-kinds=all ./simulador
```
Saída esperada:
```
All heap blocks were freed -- no leaks are possible
ERROR SUMMARY: 0 errors from 0 contexts
```

---
*Projeto desenvolvido para a disciplina de Sistemas Operacionais.*
