# Simulador de Escalonamento Multiprocessado com Paginação sob Demanda

Trabalho prático da disciplina de **Sistemas Operacionais** em Python, integrando escalonadores de CPU (**FCFS**, **SJF não preemptivo** e **Round Robin** com quantum configurável) e gerenciamento de memória física paginada sob demanda (**FIFO** e **LRU**) em máquinas com **1 CPU** e **4 CPUs**.

---

## 1. Arquivos do Projeto

| Arquivo / Pasta | Descrição |
|---|---|
| `simulador.py` | Programa principal com a simulação discreta, escalonamento, memória paginada e saídas (resumo no terminal, CSV e PNG do Gantt) |
| `menu.py` | Menu interativo no terminal para rodar qualquer configuração sem precisar digitar comandos longos |
| `iniciar_menu.bat` | Atalho para abrir o menu com 2 cliques no Windows |
| `testes.py` | Testes automatizados reproduzindo os exemplos manuais da seção 7 do PDF do professor |
| `experimentos.py` | Script que roda as 32 configurações oficiais e gera as tabelas CSV e os gráficos comparativos |
| `relatorio maneiro.docx` | Relatório técnico em Word |
| `requirements.txt` | Dependência para gerar as figuras dos gráficos (`matplotlib`) |
| `dados/` | Arquivos JSON da carga de trabalho (`cenario_A_t0.json` e `cenario_B_espacadas.json`) |
| `resultados/` | Tabelas CSV, gráficos comparativos PNG e arquivos de Gantt gerados |

---

## 2. Instalação

Requer **Python 3.9+** e a biblioteca `matplotlib` para gerar as imagens dos gráficos:

```bash
pip install -r requirements.txt
```

---

## 3. Como Executar

### 3.1. Executar pelo Menu Interativo

Você pode abrir o menu interativo com 2 cliques no arquivo **`iniciar_menu.bat`** ou digitando no terminal:

```bash
python menu.py
```
ou rodando o menu
ou pelo terminal (abaixo)

### 3.2. Executar direto pela Linha de Comando (CLI)

O `simulador.py` aceita todos os parâmetros via argumentos de linha de comando:

```bash
python simulador.py --arquivo dados/cenario_A_t0.json --cpus 4 --sched rr --quantum 10 --subst lru --quadros 256 --custo-troca 1
```

#### Argumentos disponíveis:
- `--arquivo`: Caminho do arquivo JSON da carga (ex.: `dados/cenario_A_t0.json`).
- `--cpus`: Quantidade de CPUs simuladas (`1` ou `4`).
- `--sched`: Política de escalonamento (`fcfs`, `sjf` ou `rr`).
- `--quantum`: Valor inteiro do quantum para o Round Robin (padrão `10`).
- `--subst`: Política de substituição de páginas (`fifo` ou `lru`).
- `--quadros`: Quantidade de quadros na memória física (padrão `256`).
- `--custo-troca`: Custo da troca de contexto em unidades de tempo (padrão `1`).
- `--log`: (Opcional) Mostra e salva o log detalhado a cada evento.

Ao final de cada execução, o simulador imprime o resumo na tela e salva na pasta `resultados/`:
- O CSV do diagrama de Gantt da janela 0 a 200 (`resultados/gantt_<config>.csv`).
- A imagem PNG do diagrama de Gantt da janela 0 a 200 (`resultados/gantt_<config>.png`).

### 3.3. Executar os Testes Automatizados

Para rodar os testes unitários baseados nos exemplos da seção 7 do PDF:

```bash
python testes.py
```

### 3.4. Rodar a Bateria Completa de 32 Experimentos e Gráficos

Para reproduzir todas as 32 configurações oficiais e regerar as tabelas e os 3 gráficos comparativos:

```bash
python experimentos.py
```
sendo eles
As 28 execuções base (todas com LRU):
2 Cenários (A e B)
2 configurações de CPU (1 CPU e 4 CPUs)
7 políticas de escalonamento (FCFS, SJF e Round Robin com 5 quantums: 2, 5, 10, 20 e 50)
2 x 2 x 7 = 28 execuções base

Mais as 4 execuções para comparar FIFO vs LRU:
Como as 28 execuções acima foram todas feitas usando LRU, foram adicionadas mais 4 execuções usando FIFO (com RR 𝑞=10):
Cenário A com 1 CPU (FIFO)
Cenário A com 4 CPUs (FIFO)
Cenário B com 1 CPU (FIFO)
Cenário B com 4 CPUs (FIFO)

28 (base com LRU) +4 (comparações com FIFO)=32 execuções