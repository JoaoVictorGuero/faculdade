import argparse
import colorsys
import csv
import json
import os
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# guarda os dados e o estado de cada processo
class Processo:
    def __init__(self, dados):
        self.pid = dados["pid"]
        self.chegada = dados["chegada"]
        self.classe = dados["classe"]  # curto ou longo (nao usado para escalonar)
        self.paginas = dados["paginas"]
        self.bursts = dados["bursts"]

        self.estado = "NOVO"
        self.indice_burst = 0
        self.cpu_restante = self.bursts[0]["cpu"]
        self.indice_ref = 0

        # controle de bloqueio (e/s ou page fault)
        self.tipo_bloqueio = None
        self.instante_retorno = None
        self.pagina_fault = None

        # metricas do processo
        self.entrada_fila = None
        self.tempo_espera = 0
        self.primeiro_despacho = None
        self.tempo_termino = None
        self.page_faults = 0

    # retorna qual pagina o processo quer acessar agora
    def referencia_atual(self):
        return self.bursts[self.indice_burst]["refs"][self.indice_ref]


# representa um nucleo de cpu
class CPU:
    def __init__(self, indice):
        self.indice = indice
        self.processo = None
        self.ultimo_pid = None
        self.troca_restante = 0
        self.quantum_usado = 0
        self.ref_verificada = False

        # acumuladores de tempo
        self.tempo_util = 0
        self.tempo_troca = 0
        self.tempo_ocioso = 0
        self.trocas_contexto = 0


# informacoes da pagina guardada no quadro da memoria
class QuadroMemoria:
    def __init__(self, pid, pagina, tempo_carga, ordem_carga):
        self.pid = pid
        self.pagina = pagina
        self.tempo_carga = tempo_carga
        self.ordem_carga = ordem_carga
        self.ultimo_uso = tempo_carga
        self.ordem_uso = ordem_carga
        self.protegida = True


# gerencia a memoria fisica com as politicas fifo e lru
class MemoriaFisica:
    def __init__(self, total_quadros, politica):
        self.total_quadros = total_quadros
        self.politica = politica
        # mapa (pid, pagina) -> quadro para busca rapida
        self.quadros = {}
        self.contador_ordem = 0

    def contem_pagina(self, pid, pagina):
        return (pid, pagina) in self.quadros

    # atualiza o ultimo uso para o lru e libera a protecao
    def registrar_acerto(self, pid, pagina, instante):
        quadro = self.quadros[(pid, pagina)]
        quadro.protegida = False
        self.contador_ordem += 1
        quadro.ultimo_uso = instante
        quadro.ordem_uso = self.contador_ordem

    # coloca a pagina na memoria depois que volta do fault
    def instalar_pagina(self, pid, pagina, instante):
        chave = (pid, pagina)
        if chave in self.quadros:
            self.quadros[chave].protegida = True
            return True

        if len(self.quadros) < self.total_quadros:
            self.contador_ordem += 1
            self.quadros[chave] = QuadroMemoria(pid, pagina, instante, self.contador_ordem)
            return True

        # memoria cheia: escolhe vitima entre as nao protegidas
        candidatos = [q for q in self.quadros.values() if not q.protegida]
        if not candidatos:
            return False

        # se for fifo pega o mais antigo carregado, se for lru pega o com uso mais antigo
        if self.politica == "fifo":
            vitima = min(candidatos, key=lambda q: q.ordem_carga)
        else:
            vitima = min(candidatos, key=lambda q: q.ordem_uso)

        del self.quadros[(vitima.pid, vitima.pagina)]
        self.contador_ordem += 1
        self.quadros[chave] = QuadroMemoria(pid, pagina, instante, self.contador_ordem)
        return True

    # libera os quadros do processo quando ele termina
    def liberar_processo(self, pid, num_paginas):
        for pag in range(num_paginas):
            self.quadros.pop((pid, pag), None)


# le e valida o arquivo json com os processos
def carregar_e_validar_json(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    pids_vistos = set()
    for p in dados:
        pid = p["pid"]
        if pid in pids_vistos:
            raise ValueError(f"PID duplicado: {pid}")
        pids_vistos.add(pid)
        if p["chegada"] < 0 or p["paginas"] <= 0 or not p["bursts"]:
            raise ValueError(f"Dados invalidos no processo {pid}")
        if "cpu" not in p["bursts"][0] or "cpu" not in p["bursts"][-1]:
            raise ValueError(f"Processo {pid} deve comecar e terminar com burst de CPU")
        for i, b in enumerate(p["bursts"]):
            if i % 2 == 0:
                if "cpu" not in b or b["cpu"] <= 0 or len(b["refs"]) != b["cpu"]:
                    raise ValueError(f"Burst de CPU invalido no processo {pid}")
                if any(r < 0 or r >= p["paginas"] for r in b["refs"]):
                    raise ValueError(f"Referencia de pagina fora do limite no processo {pid}")
            else:
                if "es" not in b or b["es"] <= 0:
                    raise ValueError(f"Burst de E/S invalido no processo {pid}")

    return dados


# seleciona o proximo processo da fila de prontos
def escolher_proximo_processo(fila_prontos, escalonador):
    if escalonador in ("fcfs", "rr"):
        return fila_prontos.popleft()

    if escalonador == "sjf":
        # sjf pega o menor tempo restante do burst
        melhor_proc = min(fila_prontos, key=lambda p: p.cpu_restante)
        fila_prontos.remove(melhor_proc)
        return melhor_proc

    raise ValueError(f"Escalonador desconhecido: {escalonador}")


# registra ou junta intervalos no gantt ate o limite de 200
def adicionar_intervalo_gantt(gantt_por_cpu, indice_cpu, inicio, fim, evento, limite=200):
    if inicio >= limite or fim <= inicio:
        return
    fim_recortado = min(fim, limite)
    lista = gantt_por_cpu[indice_cpu]
    if lista and lista[-1][2] == inicio and lista[-1][3] == evento:
        lista[-1][2] = fim_recortado
    else:
        lista.append([indice_cpu, inicio, fim_recortado, evento])


# formata uma linha do log de eventos
def formatar_linha_log(instante, evento, pid, fila_prontos, bloqueados, cpus, memoria):
    prontos_str = "[" + ", ".join(f"P{p.pid}" for p in fila_prontos) + "]"
    bloq_ordenados = sorted(bloqueados, key=lambda p: (p.instante_retorno, p.pid))
    bloq_str = (
        "["
        + ", ".join(f"P{p.pid}(ret={p.instante_retorno},{p.tipo_bloqueio})" for p in bloq_ordenados)
        + "]"
    )
    cpus_str = ", ".join(
        f"CPU{c.indice}="
        + (
            f"P{c.processo.pid}(TROCA)"
            if c.processo and c.troca_restante > 0
            else (f"P{c.processo.pid}" if c.processo else "OCIOSA")
        )
        for c in cpus
    )
    quadros_ocupados = len(memoria.quadros) if memoria is not None else 0
    return (
        f"t={instante} | evento={evento} | pid=P{pid} | "
        f"prontos={prontos_str} | bloqueados={bloq_str} | "
        f"cpus=[{cpus_str}] | quadros_ocupados={quadros_ocupados}"
    )


# executa a simulacao discreta passo a passo
def executar_simulacao(
    dados_processos,
    num_cpus=1,
    escalonador="fcfs",
    quantum=10,
    politica_subst="lru",
    num_quadros=256,
    custo_troca=1,
    ativar_log=False,
    usar_memoria=True,
    duracao_fault=20,
    limite_gantt=200,
):
    if escalonador == "rr" and (quantum is None or quantum <= 0):
        raise ValueError("O escalonador Round Robin (rr) exige --quantum inteiro positivo.")

    processos = [Processo(d) for d in dados_processos]
    total_processos = len(processos)
    total_referencias_previstas = sum(
        len(b["refs"]) for p in processos for b in p.bursts if "refs" in b
    )

    # ordena os processos que chegam por instante de chegada e pid
    novos_ordenados = sorted(processos, key=lambda p: (p.chegada, p.pid))
    idx_novos = 0

    fila_prontos = deque()
    retornos_por_tempo = {}
    conjunto_bloqueados = set()

    cpus = [CPU(i) for i in range(num_cpus)]
    memoria = MemoriaFisica(num_quadros, politica_subst) if usar_memoria else None

    gantt_por_cpu = [[] for _ in range(num_cpus)]
    registros_log = []

    total_page_faults = 0
    terminados = 0
    t = 0

    def agendar_bloqueio(proc):
        conjunto_bloqueados.add(proc)
        retornos_por_tempo.setdefault(proc.instante_retorno, []).append(proc)

    def registrar_log(instante, evento, pid):
        if ativar_log:
            registros_log.append(
                formatar_linha_log(
                    instante,
                    evento,
                    pid,
                    fila_prontos,
                    conjunto_bloqueados,
                    cpus,
                    memoria,
                )
            )

    while True:
        # FASE A: conclui o trabalho da cpu no intervalo anterior [t - 1, t]
        if t > 0:
            for cpu in cpus:
                if cpu.processo is None:
                    cpu.tempo_ocioso += 1
                    adicionar_intervalo_gantt(gantt_por_cpu, cpu.indice, t - 1, t, "OCIOSA", limite_gantt)
                elif cpu.troca_restante > 0:
                    cpu.troca_restante -= 1
                    cpu.tempo_troca += 1
                    adicionar_intervalo_gantt(gantt_por_cpu, cpu.indice, t - 1, t, "TROCA", limite_gantt)
                else:
                    # executou 1 unidade util de cpu
                    proc = cpu.processo
                    cpu.tempo_util += 1
                    adicionar_intervalo_gantt(
                        gantt_por_cpu, cpu.indice, t - 1, t, f"P{proc.pid}", limite_gantt
                    )

                    proc.cpu_restante -= 1
                    proc.indice_ref += 1
                    cpu.quantum_usado += 1
                    cpu.ref_verificada = False

                    # verifica se terminou o burst atual de cpu
                    if proc.cpu_restante == 0:
                        cpu.processo = None
                        cpu.quantum_usado = 0
                        proc.indice_burst += 1

                        if proc.indice_burst == len(proc.bursts):
                            proc.estado = "TERMINADO"
                            proc.tempo_termino = t
                            terminados += 1
                            if memoria is not None:
                                memoria.liberar_processo(proc.pid, proc.paginas)
                            registrar_log(t, "TERMINO", proc.pid)
                        else:
                            duracao_es = proc.bursts[proc.indice_burst]["es"]
                            proc.estado = "BLOQUEADO"
                            proc.tipo_bloqueio = "ES"
                            proc.instante_retorno = t + duracao_es
                            agendar_bloqueio(proc)
                            registrar_log(t, "FIM_BURST_ES", proc.pid)

            if terminados == total_processos:
                break

        # FASE B: eventos que acontecem no instante t
        # 1. chegadas e retornos de e/s e page fault (ordenados por pid)
        eventos_entrada = []
        while idx_novos < total_processos and novos_ordenados[idx_novos].chegada == t:
            eventos_entrada.append(novos_ordenados[idx_novos])
            idx_novos += 1

        if t in retornos_por_tempo:
            for proc_bloq in retornos_por_tempo.pop(t):
                eventos_entrada.append(proc_bloq)

        if eventos_entrada:
            eventos_entrada.sort(key=lambda p: p.pid)
            for proc in eventos_entrada:
                if proc.estado == "NOVO":
                    proc.estado = "PRONTO"
                    proc.entrada_fila = t
                    fila_prontos.append(proc)
                    registrar_log(t, "CHEGADA", proc.pid)
                elif proc.tipo_bloqueio == "ES":
                    conjunto_bloqueados.remove(proc)
                    proc.indice_burst += 1
                    proc.cpu_restante = proc.bursts[proc.indice_burst]["cpu"]
                    proc.indice_ref = 0
                    proc.tipo_bloqueio = None
                    proc.instante_retorno = None
                    proc.estado = "PRONTO"
                    proc.entrada_fila = t
                    fila_prontos.append(proc)
                    registrar_log(t, "RETORNO_ES", proc.pid)
                elif proc.tipo_bloqueio == "FAULT":
                    instalou = memoria.instalar_pagina(proc.pid, proc.pagina_fault, t)
                    if instalou:
                        conjunto_bloqueados.remove(proc)
                        proc.tipo_bloqueio = None
                        proc.instante_retorno = None
                        proc.pagina_fault = None
                        proc.estado = "PRONTO"
                        proc.entrada_fila = t
                        fila_prontos.append(proc)
                        registrar_log(t, "RETORNO_FAULT", proc.pid)
                    else:
                        # se todos quadros estiverem protegidos, espera mais 20 unidades
                        proc.instante_retorno = t + duracao_fault
                        agendar_bloqueio(proc)
                        registrar_log(t, "FAULT_ADIADO_SEM_VITIMA", proc.pid)

        # 2. preempcao de quantum no round robin
        if escalonador == "rr":
            for cpu in cpus:
                if (
                    cpu.processo is not None
                    and cpu.troca_restante == 0
                    and cpu.quantum_usado == quantum
                ):
                    if len(fila_prontos) > 0:
                        proc = cpu.processo
                        cpu.processo = None
                        cpu.quantum_usado = 0
                        cpu.ref_verificada = False
                        proc.estado = "PRONTO"
                        proc.entrada_fila = t
                        fila_prontos.append(proc)
                        registrar_log(t, "PREEMPCAO_QUANTUM", proc.pid)
                    else:
                        # sem concorrente pronto: renova o quantum sem custo
                        cpu.quantum_usado = 0
                        registrar_log(t, "RENOVACAO_QUANTUM", cpu.processo.pid)

        # 3. verificacao de pagina e despacho para cpus livres
        while True:
            houve_mudanca = False

            # verifica se a pagina da referencia esta na memoria
            for cpu in cpus:
                if (
                    cpu.processo is not None
                    and cpu.troca_restante == 0
                    and not cpu.ref_verificada
                ):
                    proc = cpu.processo
                    if memoria is not None:
                        pagina = proc.referencia_atual()
                        if memoria.contem_pagina(proc.pid, pagina):
                            memoria.registrar_acerto(proc.pid, pagina, t)
                            cpu.ref_verificada = True
                        else:
                            # page fault: bloqueia e libera a cpu imediatamente
                            total_page_faults += 1
                            proc.page_faults += 1
                            proc.estado = "BLOQUEADO"
                            proc.tipo_bloqueio = "FAULT"
                            proc.pagina_fault = pagina
                            proc.instante_retorno = t + duracao_fault
                            agendar_bloqueio(proc)

                            cpu.processo = None
                            cpu.quantum_usado = 0
                            cpu.ref_verificada = False
                            registrar_log(t, "PAGE_FAULT", proc.pid)
                            houve_mudanca = True
                    else:
                        cpu.ref_verificada = True

            # despacha processos para cpus livres na ordem do indice
            for cpu in cpus:
                if cpu.processo is None and len(fila_prontos) > 0:
                    proc = escolher_proximo_processo(fila_prontos, escalonador)
                    proc.tempo_espera += t - proc.entrada_fila
                    proc.entrada_fila = None
                    if proc.primeiro_despacho is None:
                        proc.primeiro_despacho = t
                    proc.estado = "EXECUTANDO"

                    cpu.processo = proc
                    cpu.quantum_usado = 0
                    cpu.ref_verificada = False

                    # convencao A de troca de contexto
                    if cpu.ultimo_pid != proc.pid:
                        cpu.ultimo_pid = proc.pid
                        if custo_troca > 0:
                            cpu.troca_restante = custo_troca
                            cpu.trocas_contexto += 1
                        else:
                            cpu.troca_restante = 0
                    else:
                        cpu.troca_restante = 0

                    registrar_log(t, "DESPACHO", proc.pid)
                    houve_mudanca = True
                    break

            if not houve_mudanca:
                break

        # FASE C: avanco do relogio (pula tempo se todas cpus estiverem ociosas)
        todas_ociosas = all(cpu.processo is None for cpu in cpus)
        if todas_ociosas and len(fila_prontos) == 0:
            candidatos_tempo = []
            if idx_novos < total_processos:
                candidatos_tempo.append(novos_ordenados[idx_novos].chegada)
            if retornos_por_tempo:
                candidatos_tempo.append(min(retornos_por_tempo.keys()))

            if not candidatos_tempo:
                break

            proximo_t = min(candidatos_tempo)
            if proximo_t > t + 1:
                salto = proximo_t - (t + 1)
                for cpu in cpus:
                    cpu.tempo_ocioso += salto
                    adicionar_intervalo_gantt(
                        gantt_por_cpu, cpu.indice, t, proximo_t - 1, "OCIOSA", limite_gantt
                    )
                t = proximo_t
                continue

        t += 1

    makespan = t

    # calculo das metricas finais
    esperas = [p.tempo_espera for p in processos]
    turnarounds = [p.tempo_termino - p.chegada for p in processos]
    respostas = [p.primeiro_despacho - p.chegada for p in processos]

    espera_media = sum(esperas) / total_processos
    espera_maxima = max(esperas)
    turnaround_medio = sum(turnarounds) / total_processos
    resposta_media = sum(respostas) / total_processos
    trocas_totais = sum(cpu.trocas_contexto for cpu in cpus)
    taxa_faults_pct = (
        (total_page_faults / total_referencias_previstas) * 100.0
        if total_referencias_previstas > 0
        else 0.0
    )

    metricas_cpus = []
    for cpu in cpus:
        utilizacao_frac = (
            (cpu.tempo_util + cpu.tempo_troca) / makespan if makespan > 0 else 0.0
        )
        metricas_cpus.append(
            {
                "cpu": cpu.indice,
                "tempo_util": cpu.tempo_util,
                "tempo_troca": cpu.tempo_troca,
                "tempo_ocioso": cpu.tempo_ocioso,
                "pct_util": (cpu.tempo_util / makespan * 100.0) if makespan > 0 else 0.0,
                "pct_troca": (cpu.tempo_troca / makespan * 100.0) if makespan > 0 else 0.0,
                "pct_ocioso": (cpu.tempo_ocioso / makespan * 100.0) if makespan > 0 else 0.0,
                "utilizacao": utilizacao_frac,
                "utilizacao_pct": utilizacao_frac * 100.0,
                "trocas_contexto": cpu.trocas_contexto,
            }
        )

    gantt_unificado = []
    for lista_cpu in gantt_por_cpu:
        gantt_unificado.extend(lista_cpu)

    resultado = {
        "parametros": {
            "cpus": num_cpus,
            "sched": escalonador,
            "quantum": quantum if escalonador == "rr" else None,
            "subst": politica_subst if usar_memoria else "desativada",
            "quadros": num_quadros if usar_memoria else 0,
            "custo_troca": custo_troca,
        },
        "espera_media": espera_media,
        "espera_maxima": espera_maxima,
        "turnaround_medio": turnaround_medio,
        "resposta_media": resposta_media,
        "makespan": makespan,
        "trocas_contexto_total": trocas_totais,
        "page_faults_total": total_page_faults,
        "total_referencias": total_referencias_previstas,
        "taxa_faults_pct": taxa_faults_pct,
        "cpus": metricas_cpus,
        "processos": sorted(processos, key=lambda p: p.pid),
        "gantt": gantt_unificado,
        "logs": registros_log,
    }

    return resultado


# salva o gantt da janela 0 a 200 em csv
def salvar_gantt_csv(gantt, caminho_csv):
    os.makedirs(os.path.dirname(caminho_csv) or ".", exist_ok=True)
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["cpu", "inicio", "fim", "evento"])
        for linha in gantt:
            escritor.writerow(linha)


# desenha o diagrama de gantt em png
def gerar_figura_gantt(gantt, num_cpus, titulo, caminho_png, limite_janela=200):
    os.makedirs(os.path.dirname(caminho_png) or ".", exist_ok=True)

    tamanho_painel = 50
    num_paineis = max(1, (limite_janela + tamanho_painel - 1) // tamanho_painel)

    phi = 0.618033988749895
    def obter_cor_processo(pid_num):
        h = (pid_num * phi) % 1.0
        s = 0.70 + 0.20 * ((pid_num % 3) / 2.0)
        l = 0.45 + 0.15 * (((pid_num // 3) % 3) / 2.0)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        cor_texto = "#000000" if lum > 0.55 else "#FFFFFF"
        return (r, g, b), cor_texto

    altura_painel = 1.8 if num_cpus == 1 else (0.55 * num_cpus + 0.6)
    altura_fig = altura_painel * num_paineis + 1.4

    fig, eixos = plt.subplots(num_paineis, 1, figsize=(15, altura_fig), squeeze=False)

    for p_idx in range(num_paineis):
        ax = eixos[p_idx, 0]
        t0 = p_idx * tamanho_painel
        t1 = min((p_idx + 1) * tamanho_painel, limite_janela)

        for cpu_id, inicio, fim, evento in gantt:
            inter_inicio = max(inicio, t0)
            inter_fim = min(fim, t1)
            dur = inter_fim - inter_inicio
            if dur <= 0:
                continue

            if evento == "TROCA":
                cor = "#555555"
                cor_texto = "#FFFFFF"
            elif evento == "OCIOSA":
                cor = "#E0E0E0"
                cor_texto = "#666666"
            else:
                pid_num = int(evento[1:]) if evento.startswith("P") else 0
                cor, cor_texto = obter_cor_processo(pid_num)

            ax.barh(
                y=cpu_id,
                width=dur,
                left=inter_inicio,
                height=0.65,
                color=cor,
                edgecolor="black",
                linewidth=0.5,
            )

            if evento.startswith("P"):
                rotacao = 0 if dur >= 2 else 90
                tam_fonte = 7 if dur >= 2 else 6
                ax.text(
                    inter_inicio + dur / 2.0,
                    cpu_id,
                    evento,
                    ha="center",
                    va="center",
                    color=cor_texto,
                    fontsize=tam_fonte,
                    fontweight="bold",
                    rotation=rotacao,
                )
            elif dur >= 5:
                ax.text(
                    inter_inicio + dur / 2.0,
                    cpu_id,
                    evento,
                    ha="center",
                    va="center",
                    color=cor_texto,
                    fontsize=6.5,
                    fontweight="bold",
                )

        ax.set_yticks(range(num_cpus))
        ax.set_yticklabels([f"CPU {i}" for i in range(num_cpus)], fontsize=8.5, fontweight="bold")
        ax.invert_yaxis()
        ax.set_xlim(t0, t1)
        ax.set_xticks(range(t0, t1 + 1, 5))
        ax.set_xticks(range(t0, t1 + 1, 1), minor=True)
        ax.grid(axis="x", which="major", linestyle="--", alpha=0.6)
        ax.grid(axis="x", which="minor", linestyle=":", alpha=0.25)
        ax.set_title(f"Janela temporal: t = {t0} a {t1}", fontsize=9.5, fontweight="bold", loc="left")

    eixos[-1, 0].set_xlabel("Tempo (unidades inteiras)", fontsize=10, fontweight="bold")
    fig.suptitle(titulo, fontsize=12, fontweight="bold", y=0.99)

    legenda = [
        Patch(facecolor="#164cce", edgecolor="black", label="Processo em execução (PID com cor consistente)"),
        Patch(facecolor="#555555", edgecolor="black", label="Troca de contexto (TROCA)"),
        Patch(facecolor="#E0E0E0", edgecolor="black", label="CPU Ociosa (OCIOSA)"),
    ]
    fig.legend(handles=legenda, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=3, fontsize=9, framealpha=0.9)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(caminho_png, dpi=150)
    plt.close(fig)


# imprime o resumo padronizado no terminal
def imprimir_resumo(resultado, caminho_arquivo):
    p = resultado["parametros"]
    quantum_str = str(p["quantum"]) if p["quantum"] is not None else "N/A"

    print("=" * 72)
    print("RESUMO PADRONIZADO DA SIMULAÇÃO")
    print("=" * 72)
    print("1. Parâmetros usados:")
    print(f"   Arquivo de carga : {caminho_arquivo}")
    print(f"   CPUs             : {p['cpus']}")
    print(f"   Escalonador      : {p['sched'].upper()} (Quantum: {quantum_str})")
    print(f"   Memória          : {p['subst'].upper()} ({p['quadros']} quadros)")
    print(f"   Custo de troca   : {p['custo_troca']}")
    print("-" * 72)
    print("2. Métricas globais obrigatórias:")
    print(f"   Tempo de espera médio  : {resultado['espera_media']:.2f}")
    print(f"   Tempo de espera máximo : {resultado['espera_maxima']}")
    print(f"   Turnaround médio       : {resultado['turnaround_medio']:.2f}")
    print(f"   Tempo de resposta médio: {resultado['resposta_media']:.2f}")
    print(f"   Makespan               : {resultado['makespan']}")
    print(f"   Trocas de contexto     : {resultado['trocas_contexto_total']}")
    print("-" * 72)
    print("3. Tabela por CPU:")
    print(
        f"   {'CPU':<5} {'Útil':>10} {'%Útil':>8} {'Troca':>10} {'%Troca':>8} "
        f"{'Ocioso':>10} {'%Ocioso':>8} {'Utiliz.':>9} {'Trocas':>8}"
    )
    for c in resultado["cpus"]:
        print(
            f"   CPU {c['cpu']:<1} "
            f"{c['tempo_util']:>10} {c['pct_util']:>7.2f}% "
            f"{c['tempo_troca']:>10} {c['pct_troca']:>7.2f}% "
            f"{c['tempo_ocioso']:>10} {c['pct_ocioso']:>7.2f}% "
            f"{c['utilizacao_pct']:>8.2f}% {c['trocas_contexto']:>8}"
        )
    print("-" * 72)
    print("4. Memória e Page Faults:")
    print(f"   Page faults totais     : {resultado['page_faults_total']}")
    print(f"   Referências previstas  : {resultado['total_referencias']}")
    print(f"   Taxa de page faults    : {resultado['taxa_faults_pct']:.2f}%")
    print("=" * 72)


# monta o nome do arquivo para salvar na pasta resultados
def montar_identificador_execucao(caminho_arquivo, args):
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    q_str = f"_q{args.quantum}" if args.sched == "rr" else ""
    return (
        f"{nome_base}_{args.cpus}cpu_{args.sched}{q_str}_"
        f"{args.subst}_{args.quadros}q_troca{args.custo_troca}"
    )


# argumentos de linha de comando
def criar_parser():
    parser = argparse.ArgumentParser(
        description="Simulador de Escalonamento Multiprocessado com Paginação sob Demanda"
    )
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo JSON da carga")
    parser.add_argument(
        "--cpus", type=int, required=True, choices=[1, 4], help="Quantidade de CPUs (1 ou 4)"
    )
    parser.add_argument(
        "--sched",
        required=True,
        choices=["fcfs", "sjf", "rr"],
        help="Política de escalonamento (fcfs, sjf ou rr)",
    )
    parser.add_argument(
        "--quantum",
        type=int,
        default=10,
        help="Quantum para o escalonador Round Robin (inteiro positivo)",
    )
    parser.add_argument(
        "--subst",
        required=True,
        choices=["fifo", "lru"],
        help="Política de substituição de páginas (fifo ou lru)",
    )
    parser.add_argument(
        "--quadros",
        type=int,
        default=256,
        help="Quantidade de quadros na memória física (padrão: 256)",
    )
    parser.add_argument(
        "--custo-troca",
        type=int,
        default=1,
        help="Custo da troca de contexto em unidades de tempo (padrão: 1)",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Ativa o registro detalhado de eventos (seção 9.3)",
    )
    parser.add_argument(
        "--sem-memoria",
        action="store_true",
        help="Desativa a simulação de memória (usado para validar o exemplo 7.1)",
    )
    parser.add_argument(
        "--duracao-fault",
        type=int,
        default=20,
        help="Duração do bloqueio por page fault em unidades de tempo (padrão: 20)",
    )
    return parser


def main():
    parser = criar_parser()
    args = parser.parse_args()

    if args.sched == "rr" and args.quantum <= 0:
        parser.error("O argumento --quantum deve ser um inteiro positivo.")
    if args.quadros <= 0:
        parser.error("O argumento --quadros deve ser um inteiro positivo.")
    if args.custo_troca < 0:
        parser.error("O argumento --custo-troca deve ser um inteiro não negativo.")

    dados = carregar_e_validar_json(args.arquivo)
    resultado = executar_simulacao(
        dados_processos=dados,
        num_cpus=args.cpus,
        escalonador=args.sched,
        quantum=args.quantum,
        politica_subst=args.subst,
        num_quadros=args.quadros,
        custo_troca=args.custo_troca,
        ativar_log=args.log,
        usar_memoria=not args.sem_memoria,
        duracao_fault=args.duracao_fault,
    )

    os.makedirs("resultados", exist_ok=True)
    ident = montar_identificador_execucao(args.arquivo, args)

    caminho_gantt_csv = os.path.join("resultados", f"gantt_{ident}.csv")
    salvar_gantt_csv(resultado["gantt"], caminho_gantt_csv)

    caminho_gantt_png = os.path.join("resultados", f"gantt_{ident}.png")
    titulo_gantt = (
        f"Gantt (0 a 200) — {os.path.basename(args.arquivo)} | {args.cpus} CPU(s) | "
        f"{args.sched.upper()}"
        + (f" (Q={args.quantum})" if args.sched == "rr" else "")
        + f" | {args.subst.upper()} ({args.quadros} quadros)"
    )
    gerar_figura_gantt(resultado["gantt"], args.cpus, titulo_gantt, caminho_gantt_png)

    if args.log:
        caminho_log = os.path.join("resultados", f"log_{ident}.txt")
        with open(caminho_log, "w", encoding="utf-8") as f:
            for linha in resultado["logs"]:
                f.write(linha + "\n")

    imprimir_resumo(resultado, args.arquivo)
    print(f"Arquivo CSV do Gantt salvo em : {caminho_gantt_csv}")
    print(f"Figura PNG do Gantt salva em  : {caminho_gantt_png}")
    if args.log:
        print(f"Arquivo de log salvo em       : {caminho_log}")


if __name__ == "__main__":
    main()
