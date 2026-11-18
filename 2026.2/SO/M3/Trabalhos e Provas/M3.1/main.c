/*
 * Bibliotecas padrao da linguagem C usadas no simulador:
 * - stdio.h:  O que e -> entrada e saida padrao. Como/Porque -> permite imprimir no terminal (printf) e ler comandos (fgets, sscanf).
 * - stdlib.h: O que e -> utilidades gerais e memoria. Como/Porque -> fornece malloc() e free() para criar e apagar arquivos/pastas em memoria.
 * - string.h: O que e -> manipulacao de strings. Como/Porque -> fornece strcmp() para comparar comandos/nomes, strcpy() para copiar e strlen() para medir tamanhos.
 * - time.h:   O que e -> manipulacao de data e hora. Como/Porque -> fornece time() para registrar timestamps nos arquivos e ctime() para mostra-los como texto.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/*
 * Constantes do disco simulado (#define):
 * - O que sao: valores fixos definidos antes da compilacao para configurar o tamanho do disco.
 * - Porque usamos #define: facilita alterar a capacidade do disco em um unico lugar sem procurar numeros espalhados no codigo.
 */
#define NUM_BLOCOS 64       /* Quantidade total de blocos no disco simulado (64 x 16 = 1024 bytes no total) */
#define TAM_BLOCO 16        /* Tamanho de cada bloco em bytes (16 bytes e pequeno de proposito para ficar facil ver textos divididos em varios blocos) */
#define MAX_BLOCOS_ARQ 16   /* Maximo de blocos que um unico arquivo pode apontar na sua tabela de indices (16 x 16 = 256 bytes max por arquivo) */

/*
 * Mascaras de bits para permissoes RWX:
 * - O que sao: potencias de 2 que representam cada bit de permissao (Leitura=4, Escrita=2, Execucao=1).
 * - Como funcionam: em binario, 4 = 100, 2 = 010 e 1 = 001; cada permissao ocupa exatamente 1 bit dentro de um grupo de 3 bits.
 * - Porque usamos: torna muito legivel testar permissoes usando o operador bit a bit '&' (ex: permissao & PERM_R).
 */
#define PERM_R 4 /* 100 em binario: bit de Leitura (Read) */
#define PERM_W 2 /* 010 em binario: bit de Escrita (Write) */
#define PERM_X 1 /* 001 em binario: bit de Execucao (eXecute) */

/*
 * Enum TipoArquivo:
 * - O que e: uma lista de constantes inteiras nomeadas para os tipos de arquivo pedidos na disciplina.
 * - Como funciona: cada nome vira um numero (0 a 3) dentro da struct FCB.
 * - Porque usamos enum: evita usar "numeros magicos" soltos (como 0, 1, 2, 3), deixando o codigo mais facil de ler.
 */
typedef enum {
    TIPO_CARACTERE = 0, /* Arquivos de texto comum */
    TIPO_NUMERICO  = 1, /* Arquivos de dados numericos */
    TIPO_BINARIO   = 2, /* Arquivos binarios */
    TIPO_PROGRAMA  = 3  /* Programas executaveis (ganham permissao 755 por padrao) */
} TipoArquivo;

/*
 * Enum ClasseUsuario:
 * - O que e: representa as tres categorias de usuarios que podem tentar acessar um arquivo no Linux.
 * - Como funciona: a variavel global usuario_atual guarda um desses valores.
 * - Porque usamos: permite simular a troca de usuario com o comando "user" para testar bloqueios de permissao.
 */
typedef enum {
    DONO   = 0, /* Proprietario do arquivo (usa os 3 bits da esquerda: bits 8, 7 e 6) */
    GRUPO  = 1, /* Usuarios do mesmo grupo (usa os 3 bits do meio: bits 5, 4 e 3) */
    OUTROS = 2  /* Qualquer outro usuario / publico (usa os 3 bits da direita: bits 2, 1 e 0) */
} ClasseUsuario;

/*
 * Struct FCB (File Control Block):
 * - O que e: estrutura que representa um arquivo e guarda todos os seus metadados (simulando um inode + entrada).
 * - Como funciona: cada arquivo criado com touch/cp aloca dinamicamente uma struct FCB com malloc().
 * - Porque usamos: na teoria de SO, o sistema separa os dados (nos blocos do disco) dos atributos de controle (no FCB).
 */
typedef struct FCB {
    int inode;                     /* O que e: identificador unico do arquivo. Como/Porque: cresce de 1 em 1 para simular o numero de inode do Linux. */
    char nome[64];                 /* O que e: nome do arquivo. Porque: permite localizar o arquivo dentro do diretorio pelo texto digitado. */
    int tamanho;                   /* O que e: tamanho atual em bytes. Como/Porque: evita ler lixo dos blocos sabendo exatamente onde o texto termina. */
    TipoArquivo tipo;              /* O que e: categoria do arquivo (caractere, numerico, binario, programa). */
    time_t data_criacao;           /* O que e: instante em segundos de quando o arquivo nasceu. */
    time_t data_modificacao;       /* O que e: instante da ultima escrita ou troca de permissao/nome. */
    time_t data_acesso;            /* O que e: instante da ultima leitura (cat/cp) ou execucao (exec). */
    int permissoes;                /* O que e: inteiro de 9 bits (ex: 0644 ou 0755 em octal) com rwx para dono, grupo e outros. */
    int blocos[MAX_BLOCOS_ARQ];    /* O que e: tabela de indices (alocacao indexada). Como/Porque: guarda quais linhas do vetor disco[][] guardam os dados deste arquivo. */
    int qtd_blocos;                /* O que e: quantos blocos estao ocupados por este arquivo no momento. */
    struct FCB *prox;              /* O que e: ponteiro para o proximo arquivo. Como/Porque: liga os arquivos de uma mesma pasta em uma lista encadeada simples. */
} FCB;

/*
 * Struct Diretorio:
 * - O que e: no de uma arvore que representa uma pasta do sistema de arquivos.
 * - Como funciona: usa ponteiros para ligar cada pasta ao seu pai, aos seus filhos (subpastas), aos irmaos e aos seus arquivos (FCBs).
 * - Porque usamos essa forma (arvore com lista de filhos): permite criar infinitas subpastas sem limitar um tamanho fixo de array por diretorio.
 */
typedef struct Diretorio {
    char nome[64];                 /* Nome da pasta (a raiz se chama "/") */
    struct Diretorio *pai;         /* Aponta para a pasta acima (NULL apenas na raiz "/") -> permite fazer "cd .." e "pwd" */
    struct Diretorio *filhos;      /* Aponta para a primeira subpasta dentro desta pasta */
    struct Diretorio *prox;        /* Aponta para a proxima pasta irma (no mesmo nivel do pai) */
    FCB *arquivos;                 /* Aponta para o primeiro arquivo (FCB) guardado dentro desta pasta */
} Diretorio;

/*
 * Variaveis globais do simulador:
 * - O que sao: o "hardware" simulado (disco e mapa de blocos) e o estado atual da sessao.
 * - Como funcionam: em C, arrays e variaveis globais ja iniciam zerados automaticamente ao abrir o programa.
 * - Porque sao globais: varias funcoes diferentes (cat, echo, cp, rm, stat, disco) precisam consultar o mesmo disco e o mesmo usuario atual.
 */
char disco[NUM_BLOCOS][TAM_BLOCO]; /* Matriz que simula o disco fisico: 64 blocos de 16 caracteres cada */
int bloco_ocupado[NUM_BLOCOS];     /* Mapa de bits/flags do disco: 0 significa bloco livre, 1 significa bloco ocupado */
ClasseUsuario usuario_atual = DONO;/* Guarda qual classe de usuario esta operando o terminal agora */
int proximo_inode = 1;             /* Contador global para garantir que cada novo arquivo ganhe um inode diferente */

/* ---------- Funcoes Auxiliares ---------- */

/**
 * Titulo: nome_tipo - Retorna o nome do tipo do arquivo
 *
 * Descricao:
 *   Converte o valor do enum TipoArquivo para uma palavra legivel.
 *
 * O que brevemente é utilizado na funcao:
 *   Condicionais simples (if) comparando o enum TipoArquivo.
 *
 * Onde é utilizada:
 *   cmd_ls e cmd_stat.
 *
 * Porque é feita dessa forma:
 *   Evita repetir varios if/else toda vez que precisamos imprimir o tipo do arquivo.
 */
char *nome_tipo(TipoArquivo t) {
    /* Compara o numero guardado no enum e devolve a palavra correspondente */
    if (t == TIPO_NUMERICO) return "numerico";
    if (t == TIPO_BINARIO)  return "binario";
    if (t == TIPO_PROGRAMA) return "programa";
    return "caractere";
}

/**
 * Titulo: nome_usuario - Retorna o nome do usuario atual
 *
 * Descricao:
 *   Converte o enum ClasseUsuario para texto ("dono", "grupo" ou "outros").
 *
 * O que brevemente é utilizado na funcao:
 *   Condicionais simples (if) sobre o enum ClasseUsuario.
 *
 * Onde é utilizada:
 *   tem_permissao e main.
 *
 * Porque é feita dessa forma:
 *   Centraliza a traducao do usuario para deixar as mensagens e o prompt mais claros.
 */
char *nome_usuario(ClasseUsuario u) {
    /* Traduz o enum da classe de usuario para texto exibivel na tela */
    if (u == GRUPO)  return "grupo";
    if (u == OUTROS) return "outros";
    return "dono";
}

/**
 * Titulo: mostrar_permissoes - Exibe permissoes no formato rwxr-xr-x
 *
 * Descricao:
 *   Le os 9 bits de permissao de um arquivo e imprime as letras r, w, x ou -.
 *
 * O que brevemente é utilizado na funcao:
 *   Operador bit a bit (&) com valores octais (0400 ate 0001) e printf.
 *
 * Onde é utilizada:
 *   cmd_ls, cmd_chmod e cmd_stat.
 *
 * Porque é feita dessa forma:
 *   Testar cada bit diretamente em octal e facil de entender e mostra como o Linux exibe permissoes.
 */
void mostrar_permissoes(int p) {
    /*
     * Cada digito octal representa 3 bits (r=4, w=2, x=1):
     * - 0400, 0200, 0100 testam os 3 bits do DONO (primeiro digito octal)
     * - 0040, 0020, 0010 testam os 3 bits do GRUPO (segundo digito octal)
     * - 0004, 0002, 0001 testam os 3 bits de OUTROS (terceiro digito octal)
     * Se o resultado do '&' for diferente de 0, o bit esta ligado e imprimimos a letra; senao '-'.
     */
    printf("%c%c%c%c%c%c%c%c%c",
           (p & 0400) ? 'r' : '-', (p & 0200) ? 'w' : '-', (p & 0100) ? 'x' : '-',
           (p & 0040) ? 'r' : '-', (p & 0020) ? 'w' : '-', (p & 0010) ? 'x' : '-',
           (p & 0004) ? 'r' : '-', (p & 0002) ? 'w' : '-', (p & 0001) ? 'x' : '-');
}

/**
 * Titulo: tem_permissao - Verifica controle de acesso RWX do usuario atual
 *
 * Descricao:
 *   Checa se o usuario_atual pode ler (PERM_R), escrever (PERM_W) ou executar (PERM_X) o arquivo.
 *
 * O que brevemente é utilizado na funcao:
 *   Deslocamento de bits (>>), mascara bit a bit (&), variavel global usuario_atual e printf.
 *
 * Onde é utilizada:
 *   cmd_echo, cmd_cat, cmd_exec, cmd_cp, cmd_mv e cmd_rm.
 *
 * Porque é feita dessa forma:
 *   Deslocar 6, 3 ou 0 bits isola exatamente os 3 bits do dono, grupo ou outros de forma bem curta.
 */
int tem_permissao(FCB *arq, int op) {
    /* Escolhe quantas casas empurrar os bits para a direita conforme o usuario atual */
    int shift = 0;
    if (usuario_atual == DONO) shift = 6;       /* Dono fica nos bits 8..6 -> empurra 6 casas */
    else if (usuario_atual == GRUPO) shift = 3; /* Grupo fica nos bits 5..3 -> empurra 3 casas */
                                                /* Outros ja fica nos bits 2..0 -> shift = 0 */

    /* O '& 7' (111 em binario) mantem apenas os 3 bits (rwx) do usuario escolhido */
    int perm_classe = (arq->permissoes >> shift) & 7;

    /* Testa se o bit da operacao (PERM_R=4, PERM_W=2 ou PERM_X=1) esta ativo */
    if ((perm_classe & op) == 0) {
        printf("Erro: Permissao negada para '%s' (usuario: %s).\n",
               arq->nome, nome_usuario(usuario_atual));
        return 0; /* Bloqueia a operacao */
    }
    return 1; /* Autoriza a operacao */
}

/**
 * Titulo: nome_valido - Valida nomes de arquivos e pastas
 *
 * Descricao:
 *   Garante que o nome nao esteja vazio, nao seja "." ou "..", nao tenha '/' e caiba no vetor.
 *
 * O que brevemente é utilizado na funcao:
 *   strlen, strcmp e laco for percorrendo a string.
 *
 * Onde é utilizada:
 *   cmd_mkdir, cmd_touch, cmd_cp e cmd_mv.
 *
 * Porque é feita dessa forma:
 *   Evita nomes que quebrariam a arvore de diretorios ou o tamanho maximo de 64 caracteres.
 */
int nome_valido(char *nome) {
    /* Impede nome vazio ou maior que o espaco reservado na struct (64 bytes contando o '\0') */
    if (nome[0] == '\0' || strlen(nome) >= 64) return 0;

    /* "." e ".." sao nomes especiais de navegacao na arvore, nao podem ser criados como arquivos/pastas */
    if (strcmp(nome, ".") == 0 || strcmp(nome, "..") == 0) return 0;

    /* Barra '/' separa diretorios no caminho, entao nao permitimos dentro de um nome */
    for (int i = 0; nome[i] != '\0'; i++) {
        if (nome[i] == '/') return 0;
    }
    return 1;
}

/**
 * Titulo: buscar_dir - Procura um subdiretorio pelo nome
 *
 * Descricao:
 *   Percorre a lista encadeada de subdiretorios dentro de dir procurando o nome informado.
 *
 * O que brevemente é utilizado na funcao:
 *   Laco while, ponteiro Diretorio e strcmp.
 *
 * Onde é utilizada:
 *   cmd_mkdir, cmd_cd, cmd_touch, cmd_cp e cmd_mv.
 *
 * Porque é feita dessa forma:
 *   Como os filhos formam uma lista encadeada simples, percorrer ate achar e direto e sem complicacao.
 */
Diretorio *buscar_dir(Diretorio *dir, char *nome) {
    /* Comeca pelo primeiro filho da pasta e vai pulando para o irmao (prox) ate achar ou acabar */
    Diretorio *aux = dir->filhos;
    while (aux != NULL) {
        if (strcmp(aux->nome, nome) == 0) return aux;
        aux = aux->prox;
    }
    return NULL; /* Nao encontrou nenhuma subpasta com esse nome */
}

/**
 * Titulo: buscar_arq - Procura um arquivo (FCB) pelo nome
 *
 * Descricao:
 *   Percorre a lista encadeada de arquivos do diretorio atual ate encontrar o FCB desejado.
 *
 * O que brevemente é utilizado na funcao:
 *   Laco while, ponteiro FCB e strcmp.
 *
 * Onde é utilizada:
 *   cmd_mkdir, cmd_touch, cmd_echo, cmd_cat, cmd_exec, cmd_chmod, cmd_cp, cmd_mv e cmd_stat.
 *
 * Porque é feita dessa forma:
 *   Reaproveita a mesma busca simples em quase todos os comandos de arquivo.
 */
FCB *buscar_arq(Diretorio *dir, char *nome) {
    /* Comeca pelo primeiro arquivo da pasta e avanca pelo ponteiro prox */
    FCB *aux = dir->arquivos;
    while (aux != NULL) {
        if (strcmp(aux->nome, nome) == 0) return aux;
        aux = aux->prox;
    }
    return NULL; /* Arquivo nao existe neste diretorio */
}

/**
 * Titulo: imprimir_caminho - Mostra o caminho completo do diretorio
 *
 * Descricao:
 *   Imprime da raiz "/" ate o diretorio passado subindo pelos ponteiros pai.
 *
 * O que brevemente é utilizado na funcao:
 *   Recursao simples usando o ponteiro pai e printf.
 *
 * Onde é utilizada:
 *   imprimir_caminho (recursiva) e main (no prompt e no comando pwd).
 *
 * Porque é feita dessa forma:
 *   A recursao imprime primeiro os pais e depois os filhos, mostrando o caminho na ordem certa sem usar vetores extras.
 */
void imprimir_caminho(Diretorio *dir) {
    /* Caso base da recursao: chegou na raiz (pai == NULL), imprime "/" e volta */
    if (dir->pai == NULL) {
        printf("/");
        return;
    }
    /* Primeiro chama para o pai (subindo ate a raiz) */
    imprimir_caminho(dir->pai);
    /* Coloca "/" separador se o pai nao for a propria raiz (evita imprimir "//pasta") */
    if (dir->pai->pai != NULL) printf("/");
    /* Agora imprime o nome da pasta atual na volta da recursao */
    printf("%s", dir->nome);
}

/* ---------- Alocacao de Blocos no Disco ---------- */

/**
 * Titulo: liberar_blocos - Libera os blocos ocupados por um arquivo
 *
 * Descricao:
 *   Marca os blocos do arquivo como livres no vetor bloco_ocupado e limpa os dados do disco.
 *
 * O que brevemente é utilizado na funcao:
 *   Lacos for, vetores globais bloco_ocupado e disco, e campos do FCB.
 *
 * Onde é utilizada:
 *   escrever_blocos, cmd_rm e liberar_tudo.
 *
 * Porque é feita dessa forma:
 *   Garante que blocos de arquivos apagados ou reescritos possam ser reutilizados depois.
 */
void liberar_blocos(FCB *arq) {
    /* Passa por cada bloco anotado na tabela do arquivo */
    for (int i = 0; i < arq->qtd_blocos; i++) {
        int b = arq->blocos[i];
        bloco_ocupado[b] = 0; /* Marca o bloco fisico como livre no mapa do disco */
        /* Limpa os 16 bytes do bloco no disco simulado */
        for (int j = 0; j < TAM_BLOCO; j++) disco[b][j] = '\0';
        arq->blocos[i] = -1;  /* Remove a referencia do FCB */
    }
    arq->qtd_blocos = 0;
    arq->tamanho = 0;
}

/**
 * Titulo: escrever_blocos - Grava texto dividido em blocos de 16 bytes
 *
 * Descricao:
 *   Calcula quantos blocos sao necessarios, busca blocos livres no disco simulado e salva os caracteres.
 *
 * O que brevemente é utilizado na funcao:
 *   strlen, lacos for, operador modulo (%) para trocar de bloco a cada 16 bytes e time().
 *
 * Onde é utilizada:
 *   cmd_echo e cmd_cp.
 *
 * Porque é feita dessa forma:
 *   Simula a alocacao indexada de forma visual e simples, guardando os indices dos blocos dentro do FCB.
 */
int escrever_blocos(FCB *arq, char *texto) {
    /* Calcula o tamanho do texto e quantos blocos de 16 bytes ele vai precisar (arredondando para cima) */
    int tam = (int)strlen(texto);
    int necessarios = (tam + TAM_BLOCO - 1) / TAM_BLOCO;

    /* Impede passar da capacidade maxima da tabela de indices dentro do FCB */
    if (necessarios > MAX_BLOCOS_ARQ) {
        printf("Erro: Limite maximo de %d bytes excedido.\n", MAX_BLOCOS_ARQ * TAM_BLOCO);
        return 0;
    }

    /* Conta quantos blocos livres existem no disco (somando os que este proprio arquivo ja ocupa, pois serao liberados) */
    int livres = arq->qtd_blocos;
    for (int i = 0; i < NUM_BLOCOS; i++) {
        if (bloco_ocupado[i] == 0) livres++;
    }
    if (necessarios > livres) {
        printf("Erro: Espaco insuficiente no disco.\n");
        return 0;
    }

    /* Apaga os blocos antigos do arquivo antes de gravar o novo texto */
    liberar_blocos(arq);

    /* Grava o texto caractere por caractere; a cada 16 bytes (i % TAM_BLOCO == 0), pega um novo bloco livre */
    int b = -1;
    for (int i = 0; i < tam; i++) {
        int pos_bloco = i % TAM_BLOCO;
        if (pos_bloco == 0) {
            /* Procura o primeiro bloco livre no vetor bloco_ocupado */
            b = -1;
            for (int k = 0; k < NUM_BLOCOS; k++) {
                if (bloco_ocupado[k] == 0) {
                    b = k;
                    break;
                }
            }
            bloco_ocupado[b] = 1;                 /* Reserva o bloco no disco */
            arq->blocos[arq->qtd_blocos] = b;     /* Guarda o indice desse bloco na tabela do FCB */
            arq->qtd_blocos++;
        }
        disco[b][pos_bloco] = texto[i];           /* Escreve 1 byte dentro do bloco escolhido */
    }

    /* Atualiza os metadados de tamanho e data de modificacao do arquivo */
    arq->tamanho = tam;
    arq->data_modificacao = time(NULL);
    return 1;
}

/* ---------- Comandos de Diretorios e Arquivos ---------- */

/**
 * Titulo: cmd_mkdir - Cria um novo subdiretorio
 *
 * Descricao:
 *   Valida o nome, verifica se ja nao existe e aloca uma nova struct Diretorio ligada ao pai.
 *
 * O que brevemente é utilizado na funcao:
 *   nome_valido, buscar_dir, buscar_arq, malloc, strcpy e ponteiros de lista encadeada.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando mkdir).
 *
 * Porque é feita dessa forma:
 *   Inserir o novo filho no inicio da lista encadeada de filhos e simples e rapido.
 */
void cmd_mkdir(Diretorio *atual, char *nome) {
    /* Valida o nome e garante que nao haja outra pasta ou arquivo com o mesmo nome aqui */
    if (!nome_valido(nome)) {
        printf("Erro: Nome invalido.\n");
        return;
    }
    if (buscar_dir(atual, nome) || buscar_arq(atual, nome)) {
        printf("Erro: '%s' ja existe.\n", nome);
        return;
    }

    /* Aloca memoria dinamica para a nova pasta e preenche seus ponteiros na arvore */
    Diretorio *novo = (Diretorio *)malloc(sizeof(Diretorio));
    strcpy(novo->nome, nome);
    novo->pai = atual;          /* O pai da nova pasta e a pasta onde estamos agora */
    novo->filhos = NULL;        /* Pasta recem-criada comeca sem subpastas */
    novo->arquivos = NULL;      /* Pasta recem-criada comeca sem arquivos */
    novo->prox = atual->filhos; /* Encadeia no inicio da lista de filhos da pasta atual */
    atual->filhos = novo;
    printf("Diretorio '%s' criado.\n", nome);
}

/**
 * Titulo: cmd_cd - Navega entre diretorios na arvore
 *
 * Descricao:
 *   Retorna o ponteiro para a raiz ("/"), para o pai ("..") ou para um subdiretorio filho.
 *
 * O que brevemente é utilizado na funcao:
 *   strcmp, buscar_dir e ponteiro pai da struct Diretorio.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando cd).
 *
 * Porque é feita dessa forma:
 *   Retornar o novo ponteiro Diretorio atualiza facilmente a pasta corrente no main.
 */
Diretorio *cmd_cd(Diretorio *atual, Diretorio *raiz, char *nome) {
    /* "/" volta direto para a raiz; ".." sobe um nivel usando o ponteiro pai */
    if (strcmp(nome, "/") == 0) return raiz;
    if (strcmp(nome, "..") == 0) return (atual->pai != NULL) ? atual->pai : raiz;

    /* Caso contrario, procura uma subpasta com esse nome dentro do diretorio atual */
    Diretorio *sub = buscar_dir(atual, nome);
    if (sub == NULL) {
        printf("Erro: Diretorio '%s' nao encontrado.\n", nome);
        return atual; /* Mantem na pasta atual se nao encontrar */
    }
    return sub;
}

/**
 * Titulo: cmd_ls - Lista pastas e arquivos do diretorio atual
 *
 * Descricao:
 *   Mostra os subdiretorios e os arquivos com inode, permissoes, tamanho, tipo e nome.
 *
 * O que brevemente é utilizado na funcao:
 *   Lacos while, mostrar_permissoes, nome_tipo e printf.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando ls).
 *
 * Porque é feita dessa forma:
 *   Imita o comando ls -l do Linux mostrando os metadados principais de forma resumida.
 */
void cmd_ls(Diretorio *atual) {
    Diretorio *d = atual->filhos;
    FCB *f = atual->arquivos;

    if (d == NULL && f == NULL) {
        printf("(diretorio vazio)\n");
        return;
    }

    /* Primeiro lista todas as subpastas da pasta atual */
    while (d != NULL) {
        printf("  [DIR] %s\n", d->nome);
        d = d->prox;
    }

    /* Depois lista todos os arquivos (FCBs) com seus atributos principais */
    while (f != NULL) {
        printf("  [ARQ] inode:%d ", f->inode);
        mostrar_permissoes(f->permissoes);
        printf(" (%03o) %dB %s - %s\n",
               f->permissoes, f->tamanho, nome_tipo(f->tipo), f->nome);
        f = f->prox;
    }
}

/**
 * Titulo: criar_fcb - Aloca e inicializa um File Control Block (FCB)
 *
 * Descricao:
 *   Reserva memoria para um FCB, gera um inode unico, define datas, permissoes e liga no diretorio.
 *
 * O que brevemente é utilizado na funcao:
 *   malloc, time(), strcpy, variavel global proximo_inode e laco for.
 *
 * Onde é utilizada:
 *   cmd_touch e cmd_cp.
 *
 * Porque é feita dessa forma:
 *   Evita duplicar toda a inicializacao do FCB na criacao de arquivo (touch) e na copia (cp).
 */
FCB *criar_fcb(Diretorio *atual, char *nome, TipoArquivo tipo) {
    /* Aloca um novo FCB na memoria heap e pega a hora atual do sistema */
    FCB *novo = (FCB *)malloc(sizeof(FCB));
    time_t agora = time(NULL);

    /* Preenche identificacao, tamanho inicial, tipo e timestamps */
    novo->inode = proximo_inode++;
    strcpy(novo->nome, nome);
    novo->tamanho = 0;
    novo->tipo = tipo;
    novo->data_criacao = agora;
    novo->data_modificacao = agora;
    novo->data_acesso = agora;

    /* Arquivos de programa nascem executaveis (0755); os demais nascem como leitura/escrita para o dono (0644) */
    novo->permissoes = (tipo == TIPO_PROGRAMA) ? 0755 : 0644;

    /* Inicializa a tabela de blocos vazia (-1 significa nenhum bloco ligado) */
    novo->qtd_blocos = 0;
    for (int i = 0; i < MAX_BLOCOS_ARQ; i++) novo->blocos[i] = -1;

    /* Insere o novo arquivo no inicio da lista encadeada do diretorio atual */
    novo->prox = atual->arquivos;
    atual->arquivos = novo;
    return novo;
}

/**
 * Titulo: cmd_touch - Cria um arquivo vazio no diretorio atual
 *
 * Descricao:
 *   Valida o nome e o tipo opcional do arquivo e cria um novo FCB no diretorio atual.
 *
 * O que brevemente é utilizado na funcao:
 *   nome_valido, buscar_arq, buscar_dir, strcmp e criar_fcb.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando touch).
 *
 * Porque é feita dessa forma:
 *   Deixa o tipo como "caractere" por padrao caso o usuario nao informe um segundo argumento.
 */
void cmd_touch(Diretorio *atual, char *nome, char *tipo_str) {
    if (!nome_valido(nome)) {
        printf("Erro: Nome invalido.\n");
        return;
    }
    if (buscar_arq(atual, nome) || buscar_dir(atual, nome)) {
        printf("Erro: '%s' ja existe.\n", nome);
        return;
    }

    /* Se o usuario informou um segundo argumento (tipo), converte o texto para o enum TipoArquivo */
    TipoArquivo tipo = TIPO_CARACTERE;
    if (tipo_str[0] != '\0') {
        if (strcmp(tipo_str, "caractere") == 0) tipo = TIPO_CARACTERE;
        else if (strcmp(tipo_str, "numerico") == 0) tipo = TIPO_NUMERICO;
        else if (strcmp(tipo_str, "binario") == 0) tipo = TIPO_BINARIO;
        else if (strcmp(tipo_str, "programa") == 0) tipo = TIPO_PROGRAMA;
        else {
            printf("Erro: Tipo invalido (use caractere, numerico, binario ou programa).\n");
            return;
        }
    }

    /* Cria o FCB e exibe o resumo do arquivo criado */
    FCB *novo = criar_fcb(atual, nome, tipo);
    printf("Arquivo '%s' criado (inode %d, permissao %03o).\n",
           novo->nome, novo->inode, novo->permissoes);
}

/**
 * Titulo: cmd_echo - Escreve conteudo dentro de um arquivo
 *
 * Descricao:
 *   Localiza o arquivo, verifica permissao de escrita e grava o texto nos blocos do disco.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, tem_permissao(PERM_W), escrever_blocos e printf.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando echo).
 *
 * Porque é feita dessa forma:
 *   Separa a checagem de permissao da logica de alocacao de blocos no disco simulado.
 */
void cmd_echo(Diretorio *atual, char *nome, char *texto) {
    /* Primeiro encontra o arquivo na pasta atual */
    FCB *arq = buscar_arq(atual, nome);
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }
    /* Verifica se o usuario_atual tem permissao de escrita (W) antes de alterar o disco */
    if (!tem_permissao(arq, PERM_W)) return;

    /* Divide e grava o texto nos blocos simulados */
    if (escrever_blocos(arq, texto)) {
        printf("Gravados %d bytes em '%s' (%d blocos).\n",
               arq->tamanho, arq->nome, arq->qtd_blocos);
    }
}

/**
 * Titulo: cmd_cat - Le e imprime o conteudo de um arquivo
 *
 * Descricao:
 *   Verifica permissao de leitura, atualiza a data de acesso e le caractere por caractere dos blocos.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, tem_permissao(PERM_R), time(), laco for com divisao (/) e modulo (%).
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando cat).
 *
 * Porque é feita dessa forma:
 *   Usar i / TAM_BLOCO e i % TAM_BLOCO mostra claramente como o texto e remontado a partir dos blocos.
 */
void cmd_cat(Diretorio *atual, char *nome) {
    FCB *arq = buscar_arq(atual, nome);
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }
    /* Exige permissao de leitura (R) para o usuario atual */
    if (!tem_permissao(arq, PERM_R)) return;

    /* Atualiza o horario do ultimo acesso, mesmo se o arquivo estiver vazio */
    arq->data_acesso = time(NULL);
    if (arq->tamanho == 0) {
        printf("(arquivo vazio)\n");
        return;
    }

    /* Le cada byte: i / 16 diz qual entrada do vetor blocos[] usar; i % 16 diz a posicao dentro do bloco */
    for (int i = 0; i < arq->tamanho; i++) {
        int b = arq->blocos[i / TAM_BLOCO];
        printf("%c", disco[b][i % TAM_BLOCO]);
    }
    printf("\n");
}

/**
 * Titulo: cmd_exec - Simula a execucao de um arquivo
 *
 * Descricao:
 *   Verifica se o usuario tem permissao de execucao (+x) e atualiza a data de acesso.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, tem_permissao(PERM_X), time() e printf.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando exec).
 *
 * Porque é feita dessa forma:
 *   Permite testar na pratica a permissao X (Execucao) do controle de acesso RWX.
 */
void cmd_exec(Diretorio *atual, char *nome) {
    FCB *arq = buscar_arq(atual, nome);
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }
    /* Exige permissao de execucao (X) para simular a execucao do programa/arquivo */
    if (!tem_permissao(arq, PERM_X)) return;

    arq->data_acesso = time(NULL);
    printf("Executando '%s' (inode %d)... Concluido!\n", arq->nome, arq->inode);
}

/**
 * Titulo: cmd_chmod - Altera as permissoes RWX de um arquivo
 *
 * Descricao:
 *   Valida o codigo octal (ex: 755 ou 644), converte para inteiro e atualiza o FCB.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, laco for validando digitos '0'-'7', sscanf com "%o" e time().
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando chmod).
 *
 * Porque é feita dessa forma:
 *   sscanf com "%o" converte texto octal direto para numero inteiro de forma simples para iniciantes.
 */
void cmd_chmod(Diretorio *atual, char *octal_str, char *nome) {
    FCB *arq = buscar_arq(atual, nome);
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }

    /* Na base octal so existem digitos de '0' a '7'; se houver '8', '9' ou letras, rejeita */
    for (int i = 0; octal_str[i] != '\0'; i++) {
        if (octal_str[i] < '0' || octal_str[i] > '7') {
            printf("Erro: Use um numero octal valido (ex: 755).\n");
            return;
        }
    }

    /* Converte a string octal (ex: "755") para valor inteiro e garante que caiba em 9 bits (0..0777) */
    int perm = 0;
    if (sscanf(octal_str, "%o", &perm) != 1 || perm < 0 || perm > 0777) {
        printf("Erro: Permissao invalida.\n");
        return;
    }

    /* Salva a nova bitmask no FCB e atualiza a data de modificacao */
    arq->permissoes = perm;
    arq->data_modificacao = time(NULL);
    printf("Permissoes de '%s' alteradas para ", arq->nome);
    mostrar_permissoes(arq->permissoes);
    printf(" (%03o).\n", arq->permissoes);
}

/**
 * Titulo: cmd_cp - Copia um arquivo para outro nome no diretorio atual
 *
 * Descricao:
 *   Le os dados dos blocos da origem e cria um novo FCB independente com novos blocos.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, tem_permissao(PERM_R), nome_valido, criar_fcb, escrever_blocos e laco for.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando cp).
 *
 * Porque é feita dessa forma:
 *   A copia recebe um novo inode e seus proprios blocos para que editar um arquivo nao altere o outro.
 */
void cmd_cp(Diretorio *atual, char *origem, char *destino) {
    FCB *orig = buscar_arq(atual, origem);
    if (orig == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", origem);
        return;
    }
    /* Para copiar, precisa ter permissao de leitura (R) no arquivo original */
    if (!tem_permissao(orig, PERM_R)) return;
    if (!nome_valido(destino) || buscar_arq(atual, destino) || buscar_dir(atual, destino)) {
        printf("Erro: Nome de destino invalido ou ja existente.\n");
        return;
    }

    /* Copia os caracteres dos blocos do arquivo original para um vetor temporario */
    char texto[MAX_BLOCOS_ARQ * TAM_BLOCO + 1];
    for (int i = 0; i < orig->tamanho; i++) {
        int b = orig->blocos[i / TAM_BLOCO];
        texto[i] = disco[b][i % TAM_BLOCO];
    }
    texto[orig->tamanho] = '\0'; /* Fecha a string com terminador nulo */

    /* Cria um novo FCB (com novo inode) e grava o texto em novos blocos no disco */
    FCB *copia = criar_fcb(atual, destino, orig->tipo);
    copia->permissoes = orig->permissoes;
    if (!escrever_blocos(copia, texto)) {
        /* Se faltar espaco no disco, remove o FCB recem-criado para nao deixar lixo na lista */
        atual->arquivos = copia->prox;
        free(copia);
        return;
    }
    orig->data_acesso = time(NULL);
    printf("Arquivo '%s' copiado para '%s' (inode %d).\n", orig->nome, copia->nome, copia->inode);
}

/**
 * Titulo: cmd_mv - Move ou renomeia um arquivo
 *
 * Descricao:
 *   Se o destino for um subdiretorio existente, move o FCB para dentro dele; senao, renomeia o arquivo.
 *
 * O que brevemente é utilizado na funcao:
 *   Laco while com ponteiro anterior (ant), tem_permissao(PERM_W), buscar_dir e strcpy.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando mv).
 *
 * Porque é feita dessa forma:
 *   Reproduz o comportamento real do mv no Linux usando apenas manipulacao de ponteiros ou troca de nome.
 */
void cmd_mv(Diretorio *atual, char *origem, char *destino) {
    /* Procura o arquivo guardando tambem o no anterior (ant) para poder desconecta-lo da lista se for mover */
    FCB *ant = NULL;
    FCB *arq = atual->arquivos;
    while (arq != NULL && strcmp(arq->nome, origem) != 0) {
        ant = arq;
        arq = arq->prox;
    }
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", origem);
        return;
    }
    /* Mover ou renomear exige permissao de escrita (W) */
    if (!tem_permissao(arq, PERM_W)) return;

    /* Caso 1: se "destino" for o nome de uma subpasta existente, move o FCB para ela */
    Diretorio *sub = buscar_dir(atual, destino);
    if (sub != NULL) {
        if (buscar_arq(sub, arq->nome) || buscar_dir(sub, arq->nome)) {
            printf("Erro: Ja existe '%s' em '%s'.\n", arq->nome, sub->nome);
            return;
        }
        /* Retira o arquivo da lista encadeada da pasta atual */
        if (ant == NULL) atual->arquivos = arq->prox;
        else ant->prox = arq->prox;

        /* Coloca o mesmo FCB (mantendo inode e blocos) na lista da pasta destino */
        arq->prox = sub->arquivos;
        sub->arquivos = arq;
        arq->data_modificacao = time(NULL);
        printf("Arquivo '%s' movido para '%s'.\n", arq->nome, sub->nome);
        return;
    }

    /* Caso 2: se nao e uma pasta, apenas troca o nome do arquivo dentro do diretorio atual */
    if (!nome_valido(destino) || buscar_arq(atual, destino)) {
        printf("Erro: Nome de destino invalido ou ja existente.\n");
        return;
    }
    strcpy(arq->nome, destino);
    arq->data_modificacao = time(NULL);
    printf("Arquivo '%s' renomeado para '%s'.\n", origem, destino);
}

/**
 * Titulo: cmd_rm - Exclui um arquivo do diretorio atual
 *
 * Descricao:
 *   Remove o arquivo da lista encadeada, libera seus blocos no disco e libera a memoria do FCB.
 *
 * O que brevemente é utilizado na funcao:
 *   Laco while com ponteiro anterior (ant), tem_permissao(PERM_W), liberar_blocos e free.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando rm).
 *
 * Porque é feita dessa forma:
 *   Guardar o ponteiro anterior permite desconectar o elemento do meio da lista encadeada sem perde-la.
 */
void cmd_rm(Diretorio *atual, char *nome) {
    /* Busca o arquivo mantendo o ponteiro anterior (ant) para refazer a ligacao da lista ao remover */
    FCB *ant = NULL;
    FCB *arq = atual->arquivos;
    while (arq != NULL && strcmp(arq->nome, nome) != 0) {
        ant = arq;
        arq = arq->prox;
    }
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }
    /* Excluir exige permissao de escrita (W) */
    if (!tem_permissao(arq, PERM_W)) return;

    /* Desconecta o FCB da lista encadeada do diretorio */
    if (ant == NULL) atual->arquivos = arq->prox;
    else ant->prox = arq->prox;

    /* Primeiro devolve os blocos ao disco simulado e depois libera a struct da memoria */
    liberar_blocos(arq);
    free(arq);
    printf("Arquivo '%s' excluido.\n", nome);
}

/**
 * Titulo: cmd_stat - Exibe todos os metadados e blocos de um arquivo
 *
 * Descricao:
 *   Mostra os campos completos do FCB (inode, datas, permissoes, tamanho) e o conteudo de cada bloco.
 *
 * O que brevemente é utilizado na funcao:
 *   buscar_arq, mostrar_permissoes, nome_tipo, ctime() e lacos for sobre blocos.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando stat).
 *
 * Porque é feita dessa forma:
 *   Facilita visualizar na apresentacao como o arquivo foi fatiado em blocos de 16 bytes no disco.
 */
void cmd_stat(Diretorio *atual, char *nome) {
    FCB *arq = buscar_arq(atual, nome);
    if (arq == NULL) {
        printf("Erro: Arquivo '%s' nao encontrado.\n", nome);
        return;
    }

    /* Imprime todos os campos do FCB; ctime() ja traz uma quebra de linha no final da string */
    printf("--- Metadados (FCB) ---\n");
    printf("  Nome:        %s\n", arq->nome);
    printf("  Inode:       %d\n", arq->inode);
    printf("  Tipo:        %s\n", nome_tipo(arq->tipo));
    printf("  Tamanho:     %d bytes\n", arq->tamanho);
    printf("  Permissoes:  ");
    mostrar_permissoes(arq->permissoes);
    printf(" (%03o)\n", arq->permissoes);
    printf("  Criacao:     %s", ctime(&arq->data_criacao));
    printf("  Modificacao: %s", ctime(&arq->data_modificacao));
    printf("  Acesso:      %s", ctime(&arq->data_acesso));
    printf("  Blocos (%d):\n", arq->qtd_blocos);

    /* Mostra bloco por bloco onde o conteudo do arquivo foi salvo no disco */
    int pos = 0;
    for (int i = 0; i < arq->qtd_blocos; i++) {
        int b = arq->blocos[i];
        printf("    Bloco %2d: [", b);
        for (int j = 0; j < TAM_BLOCO && pos < arq->tamanho; j++) {
            printf("%c", disco[b][j]);
            pos++;
        }
        printf("]\n");
    }
}

/**
 * Titulo: cmd_disco - Mostra o mapa de ocupacao dos blocos do disco
 *
 * Descricao:
 *   Conta blocos livres e ocupados e desenha uma grade visual com '#' (ocupado) e '.' (livre).
 *
 * O que brevemente é utilizado na funcao:
 *   Lacos for percorrendo o vetor global bloco_ocupado e printf.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando disco).
 *
 * Porque é feita dessa forma:
 *   Permite enxergar rapidamente quantos blocos estao livres e onde os dados foram alocados.
 */
void cmd_disco(void) {
    /* Soma quantos dos 64 blocos estao marcados como ocupados (1) */
    int ocupados = 0;
    for (int i = 0; i < NUM_BLOCOS; i++) {
        if (bloco_ocupado[i]) ocupados++;
    }
    printf("Disco (%d blocos de %d bytes) - Ocupados: %d | Livres: %d\n",
           NUM_BLOCOS, TAM_BLOCO, ocupados, NUM_BLOCOS - ocupados);

    /* Desenha os 64 blocos em 4 linhas de 16 blocos para facilitar a leitura visual */
    for (int i = 0; i < NUM_BLOCOS; i++) {
        printf("%c", bloco_ocupado[i] ? '#' : '.');
        if ((i + 1) % 16 == 0) printf("\n");
    }
}

/**
 * Titulo: liberar_tudo - Libera toda a memoria da arvore ao encerrar
 *
 * Descricao:
 *   Percorre recursivamente todos os subdiretorios e arquivos liberando blocos e dando free().
 *
 * O que brevemente é utilizado na funcao:
 *   Recursao, lacos while, liberar_blocos e free.
 *
 * Onde é utilizada:
 *   liberar_tudo (recursiva) e main (antes de encerrar o programa).
 *
 * Porque é feita dessa forma:
 *   Evita memory leaks garantindo que cada malloc feito durante o uso seja liberado na saida.
 */
void liberar_tudo(Diretorio *dir) {
    if (dir == NULL) return;

    /* Primeiro apaga recursivamente todas as subpastas (salvando o proximo ponteiro antes do free) */
    Diretorio *filho = dir->filhos;
    while (filho != NULL) {
        Diretorio *prox = filho->prox;
        liberar_tudo(filho);
        filho = prox;
    }

    /* Depois libera os blocos e da free() em cada arquivo da pasta */
    FCB *arq = dir->arquivos;
    while (arq != NULL) {
        FCB *prox = arq->prox;
        liberar_blocos(arq);
        free(arq);
        arq = prox;
    }

    /* Por fim libera a propria struct Diretorio */
    free(dir);
}

/**
 * Titulo: cmd_help - Exibe a lista de comandos disponiveis
 *
 * Descricao:
 *   Imprime um resumo curto de todos os comandos aceitos pelo simulador.
 *
 * O que brevemente é utilizado na funcao:
 *   Chamadas simples de printf.
 *
 * Onde é utilizada:
 *   main (quando o usuario digita o comando help).
 *
 * Porque é feita dessa forma:
 *   Mantem o menu de ajuda organizado fora do loop principal do main.
 */
void cmd_help(void) {
    printf("Comandos:\n");
    printf("  mkdir <nome>             - Cria pasta\n");
    printf("  cd <nome|..|/>           - Entra em pasta\n");
    printf("  pwd / ls                 - Mostra caminho / lista itens\n");
    printf("  touch <nome> [tipo]      - Cria arquivo (caractere|numerico|binario|programa)\n");
    printf("  echo <nome> <texto>      - Escreve texto no arquivo\n");
    printf("  cat <nome> / exec <nome> - Le / executa arquivo\n");
    printf("  chmod <octal> <nome>     - Muda permissoes (ex: chmod 755 app)\n");
    printf("  cp <orig> <dest>         - Copia arquivo\n");
    printf("  mv <orig> <dest>         - Renomeia ou move para pasta\n");
    printf("  rm <nome>                - Exclui arquivo\n");
    printf("  stat <nome> / disco      - Mostra FCB e blocos / mapa do disco\n");
    printf("  user <dono|grupo|outros> - Troca usuario atual\n");
    printf("  exit                     - Sai e libera memoria\n");
}

/* ---------- Funcao Principal ---------- */

/**
 * Titulo: main - Loop principal do simulador de sistema de arquivos
 *
 * Descricao:
 *   Cria o diretorio raiz "/", exibe o prompt, le os comandos do teclado e chama as funcoes.
 *
 * O que brevemente é utilizado na funcao:
 *   malloc, fgets, sscanf, strcmp, laco while(1) e liberar_tudo.
 *
 * Onde é utilizada:
 *   Ponto de entrada do programa executado pelo sistema operacional.
 *
 * Porque é feita dessa forma:
 *   Usar fgets + sscanf torna a leitura de comandos e argumentos simples e facil de explicar.
 */
int main(void) {
    /* Cria dinamicamente o diretorio raiz "/" que serve de base para toda a arvore */
    Diretorio *raiz = (Diretorio *)malloc(sizeof(Diretorio));
    strcpy(raiz->nome, "/");
    raiz->pai = NULL;      /* Raiz nao tem pai */
    raiz->filhos = NULL;
    raiz->prox = NULL;
    raiz->arquivos = NULL;

    /* "atual" guarda sempre em qual pasta o usuario esta navegando no momento */
    Diretorio *atual = raiz;
    char linha[350], cmd[32], arg1[64], arg2[256];

    printf("=== Mini-Sistema de Arquivos em Memoria ===\n");
    printf("Digite 'help' para ver os comandos.\n");

    /* Loop interativo do terminal simulado: repete ate o usuario digitar "exit" */
    while (1) {
        /* Mostra o usuario atual e o caminho da pasta no prompt (ex: [dono:/docs]$ ) */
        printf("[%s:", nome_usuario(usuario_atual));
        imprimir_caminho(atual);
        printf("]$ ");

        /* Le uma linha inteira do teclado; se acabar a entrada (EOF), sai do loop */
        if (fgets(linha, sizeof(linha), stdin) == NULL) break;

        /* Remove Enter (\n, \r) e espacos sobrando no final da linha para evitar erros nos nomes */
        int tam_linha = (int)strlen(linha);
        while (tam_linha > 0 && (linha[tam_linha - 1] == '\n' ||
               linha[tam_linha - 1] == '\r' || linha[tam_linha - 1] == ' ')) {
            linha[--tam_linha] = '\0';
        }

        /*
         * Separa a linha em:
         * - cmd:  primeira palavra (comando)
         * - arg1: segunda palavra (nome do arquivo/pasta ou permissao)
         * - arg2: todo o resto da linha (permite textos com espaco no echo ou segundo argumento)
         */
        arg1[0] = '\0';
        arg2[0] = '\0';
        if (sscanf(linha, "%31s %63s %255[^\n]", cmd, arg1, arg2) < 1) continue;

        /* Direciona cada comando digitado para a sua respectiva funcao */
        if (strcmp(cmd, "exit") == 0) break;
        else if (strcmp(cmd, "help") == 0) cmd_help();
        else if (strcmp(cmd, "ls") == 0) cmd_ls(atual);
        else if (strcmp(cmd, "disco") == 0) cmd_disco();
        else if (strcmp(cmd, "pwd") == 0) {
            imprimir_caminho(atual);
            printf("\n");
        }
        else if (strcmp(cmd, "mkdir") == 0 && arg1[0] != '\0') cmd_mkdir(atual, arg1);
        else if (strcmp(cmd, "cd") == 0 && arg1[0] != '\0') atual = cmd_cd(atual, raiz, arg1);
        else if (strcmp(cmd, "touch") == 0 && arg1[0] != '\0') cmd_touch(atual, arg1, arg2);
        else if (strcmp(cmd, "echo") == 0 && arg1[0] != '\0' && arg2[0] != '\0') cmd_echo(atual, arg1, arg2);
        else if (strcmp(cmd, "cat") == 0 && arg1[0] != '\0') cmd_cat(atual, arg1);
        else if (strcmp(cmd, "exec") == 0 && arg1[0] != '\0') cmd_exec(atual, arg1);
        else if (strcmp(cmd, "chmod") == 0 && arg1[0] != '\0' && arg2[0] != '\0') cmd_chmod(atual, arg1, arg2);
        else if (strcmp(cmd, "cp") == 0 && arg1[0] != '\0' && arg2[0] != '\0') cmd_cp(atual, arg1, arg2);
        else if (strcmp(cmd, "mv") == 0 && arg1[0] != '\0' && arg2[0] != '\0') cmd_mv(atual, arg1, arg2);
        else if (strcmp(cmd, "rm") == 0 && arg1[0] != '\0') cmd_rm(atual, arg1);
        else if (strcmp(cmd, "stat") == 0 && arg1[0] != '\0') cmd_stat(atual, arg1);
        else if (strcmp(cmd, "user") == 0 && arg1[0] != '\0') {
            if (strcmp(arg1, "dono") == 0) usuario_atual = DONO;
            else if (strcmp(arg1, "grupo") == 0) usuario_atual = GRUPO;
            else if (strcmp(arg1, "outros") == 0) usuario_atual = OUTROS;
            else printf("Erro: Use dono, grupo ou outros.\n");
        }
        else printf("Comando invalido ou faltam argumentos. Digite 'help'.\n");
    }

    /* Libera toda a arvore de diretorios e arquivos da memoria antes de fechar */
    liberar_tudo(raiz);
    printf("Memoria liberada. Ate logo!\n");
    return 0;
}
