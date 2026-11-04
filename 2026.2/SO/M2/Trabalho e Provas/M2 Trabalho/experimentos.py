import csv
import json
import os
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulador import (
    carregar_e_validar_json,
    executar_simulacao,
    gerar_figura_gantt,
    salvar_gantt_csv,
)


# monta as 32 configuracoes oficiais exigidas no pdf
def obter_configuracoes_experimentos():
    cenarios = [
        ("A", "dados/cenario_A_t0.json"),
        ("B", "dados/cenario_B_espacadas.json"),
    ]
    quantums_rr = [2, 5, 10, 20, 50]
    configuracoes = []

    # 28 execucoes base com lru
    for cod_cenario, arquivo in cenarios:
        for num_cpus in (1, 4):
            configuracoes.append(
                {
                    "cenario": cod_cenario,
                    "arquivo": arquivo,
                    "cpus": num_cpus,
                    "sched": "fcfs",
                    "quantum": None,
                    "subst": "lru",
                    "quadros": 256,
                    "custo_troca": 1,
                    "grupo": "base",
                }
            )
            configuracoes.append(
                {
                    "cenario": cod_cenario,
                    "arquivo": arquivo,
                    "cpus": num_cpus,
                    "sched": "sjf",
                    "quantum": None,
                    "subst": "lru",
                    "quadros": 256,
                    "custo_troca": 1,
                    "grupo": "base",
                }
            )
            for q in quantums_rr:
                configuracoes.append(
                    {
                        "cenario": cod_cenario,
                        "arquivo": arquivo,
                        "cpus": num_cpus,
                        "sched": "rr",
                        "quantum": q,
                        "subst": "lru",
                        "quadros": 256,
                        "custo_troca": 1,
                        "grupo": "base",
                    }
                )

    # 4 execucoes extras para comparar fifo x lru
    for cod_cenario, arquivo in cenarios:
        for num_cpus in (1, 4):
            configuracoes.append(
                {
                    "cenario": cod_cenario,
                    "arquivo": arquivo,
                    "cpus": num_cpus,
                    "sched": "rr",
                    "quantum": 10,
                    "subst": "fifo",
                    "quadros": 256,
                    "custo_troca": 1,
                    "grupo": "fifo_vs_lru",
                }
            )

    return configuracoes


def rotulo_escalonador(sched, quantum):
    if sched == "rr":
        return f"RR (Q={quantum})"
    return sched.upper()


def identificador_config(cfg):
    q_str = f"_q{cfg['quantum']}" if cfg["sched"] == "rr" else ""
    return (
        f"cenario_{cfg['cenario']}_{cfg['cpus']}cpu_"
        f"{cfg['sched']}{q_str}_{cfg['subst']}_{cfg['quadros']}q"
    )


# metricas separadas por classe curto e longo para analise
def resumir_por_classe(processos):
    resumo = {}
    for classe in ("curto", "longo"):
        procs_c = [p for p in processos if p.classe == classe]
        if procs_c:
            esperas = [p.tempo_espera for p in procs_c]
            turnarounds = [p.tempo_termino - p.chegada for p in procs_c]
            respostas = [p.primeiro_despacho - p.chegada for p in procs_c]
            faults = [p.page_faults for p in procs_c]
            resumo[classe] = {
                "quantidade": len(procs_c),
                "espera_media": sum(esperas) / len(procs_c),
                "espera_maxima": max(esperas),
                "turnaround_medio": sum(turnarounds) / len(procs_c),
                "resposta_media": sum(respostas) / len(procs_c),
                "faults_medio": sum(faults) / len(procs_c),
                "faults_total": sum(faults),
            }
    return resumo


# salva as tabelas consolidadas em csv
def salvar_tabelas_csv(resultados):
    os.makedirs("resultados", exist_ok=True)

    campos_resumo = [
        "id_execucao",
        "cenario",
        "cpus",
        "escalonador",
        "quantum",
        "subst",
        "quadros",
        "custo_troca",
        "espera_media",
        "espera_maxima",
        "turnaround_medio",
        "resposta_media",
        "makespan",
        "speedup",
        "eficiencia",
        "trocas_contexto_total",
        "page_faults_total",
        "taxa_faults_pct",
        "utilizacao_media_cpus_pct",
        "ocioso_total_cpus",
    ]

    for cenario in ("A", "B"):
        caminho = os.path.join("resultados", f"tabela_resumo_cenario_{cenario}.csv")
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos_resumo)
            w.writeheader()
            for r in resultados:
                if r["cenario"] != cenario:
                    continue
                util_media = sum(c["utilizacao_pct"] for c in r["cpus_metricas"]) / len(
                    r["cpus_metricas"]
                )
                ocioso_total = sum(c["tempo_ocioso"] for c in r["cpus_metricas"])
                w.writerow(
                    {
                        "id_execucao": r["id_execucao"],
                        "cenario": r["cenario"],
                        "cpus": r["cpus"],
                        "escalonador": r["rotulo_sched"],
                        "quantum": r["quantum"] if r["quantum"] is not None else "-",
                        "subst": r["subst"].upper(),
                        "quadros": r["quadros"],
                        "custo_troca": r["custo_troca"],
                        "espera_media": f"{r['espera_media']:.2f}",
                        "espera_maxima": r["espera_maxima"],
                        "turnaround_medio": f"{r['turnaround_medio']:.2f}",
                        "resposta_media": f"{r['resposta_media']:.2f}",
                        "makespan": r["makespan"],
                        "speedup": f"{r['speedup']:.4f}" if r["speedup"] is not None else "-",
                        "eficiencia": (
                            f"{r['eficiencia']:.4f}" if r["eficiencia"] is not None else "-"
                        ),
                        "trocas_contexto_total": r["trocas_contexto_total"],
                        "page_faults_total": r["page_faults_total"],
                        "taxa_faults_pct": f"{r['taxa_faults_pct']:.2f}",
                        "utilizacao_media_cpus_pct": f"{util_media:.2f}",
                        "ocioso_total_cpus": ocioso_total,
                    }
                )

    # tabela detalhada por cpu
    caminho_cpu = os.path.join("resultados", "tabela_detalhada_por_cpu.csv")
    campos_cpu = [
        "id_execucao",
        "cenario",
        "num_cpus",
        "escalonador",
        "subst",
        "cpu_id",
        "tempo_util",
        "pct_util",
        "tempo_troca",
        "pct_troca",
        "tempo_ocioso",
        "pct_ocioso",
        "utilizacao_pct",
        "trocas_contexto",
        "makespan",
    ]
    with open(caminho_cpu, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos_cpu)
        w.writeheader()
        for r in resultados:
            for c in r["cpus_metricas"]:
                w.writerow(
                    {
                        "id_execucao": r["id_execucao"],
                        "cenario": r["cenario"],
                        "num_cpus": r["cpus"],
                        "escalonador": r["rotulo_sched"],
                        "subst": r["subst"].upper(),
                        "cpu_id": f"CPU {c['cpu']}",
                        "tempo_util": c["tempo_util"],
                        "pct_util": f"{c['pct_util']:.2f}",
                        "tempo_troca": c["tempo_troca"],
                        "pct_troca": f"{c['pct_troca']:.2f}",
                        "tempo_ocioso": c["tempo_ocioso"],
                        "pct_ocioso": f"{c['pct_ocioso']:.2f}",
                        "utilizacao_pct": f"{c['utilizacao_pct']:.2f}",
                        "trocas_contexto": c["trocas_contexto"],
                        "makespan": r["makespan"],
                    }
                )

    # tabela comparativa fifo x lru
    caminho_fl = os.path.join("resultados", "tabela_fifo_vs_lru.csv")
    with open(caminho_fl, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos_resumo)
        w.writeheader()
        for r in resultados:
            if r["sched"] == "rr" and r["quantum"] == 10:
                util_media = sum(c["utilizacao_pct"] for c in r["cpus_metricas"]) / len(
                    r["cpus_metricas"]
                )
                ocioso_total = sum(c["tempo_ocioso"] for c in r["cpus_metricas"])
                w.writerow(
                    {
                        "id_execucao": r["id_execucao"],
                        "cenario": r["cenario"],
                        "cpus": r["cpus"],
                        "escalonador": r["rotulo_sched"],
                        "quantum": r["quantum"],
                        "subst": r["subst"].upper(),
                        "quadros": r["quadros"],
                        "custo_troca": r["custo_troca"],
                        "espera_media": f"{r['espera_media']:.2f}",
                        "espera_maxima": r["espera_maxima"],
                        "turnaround_medio": f"{r['turnaround_medio']:.2f}",
                        "resposta_media": f"{r['resposta_media']:.2f}",
                        "makespan": r["makespan"],
                        "speedup": f"{r['speedup']:.4f}" if r["speedup"] is not None else "-",
                        "eficiencia": (
                            f"{r['eficiencia']:.4f}" if r["eficiencia"] is not None else "-"
                        ),
                        "trocas_contexto_total": r["trocas_contexto_total"],
                        "page_faults_total": r["page_faults_total"],
                        "taxa_faults_pct": f"{r['taxa_faults_pct']:.2f}",
                        "utilizacao_media_cpus_pct": f"{util_media:.2f}",
                        "ocioso_total_cpus": ocioso_total,
                    }
                )


# grafico 1: tempo de espera medio por escalonador
def gerar_grafico_1_espera_media(resultados):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=False)
    ordem_rotulos = ["FCFS", "SJF", "RR (Q=2)", "RR (Q=5)", "RR (Q=10)", "RR (Q=20)", "RR (Q=50)"]
    x = list(range(len(ordem_rotulos)))
    largura = 0.36

    for idx_cen, (cenario, nome_cen) in enumerate(
        [("A", "Cenário A (Chegadas em t = 0)"), ("B", "Cenário B (Chegadas Espaçadas)")]
    ):
        ax = axes[idx_cen]
        base_cen = [r for r in resultados if r["cenario"] == cenario and r["subst"] == "lru"]
        mapa_1cpu = {r["rotulo_sched"]: r["espera_media"] for r in base_cen if r["cpus"] == 1}
        mapa_4cpu = {r["rotulo_sched"]: r["espera_media"] for r in base_cen if r["cpus"] == 4}

        vals_1 = [mapa_1cpu[rot] for rot in ordem_rotulos]
        vals_4 = [mapa_4cpu[rot] for rot in ordem_rotulos]

        b1 = ax.bar(
            [i - largura / 2 for i in x],
            vals_1,
            width=largura,
            label="1 CPU",
            color="#4C78A8",
            edgecolor="black",
            linewidth=0.6,
        )
        b4 = ax.bar(
            [i + largura / 2 for i in x],
            vals_4,
            width=largura,
            label="4 CPUs",
            color="#F58518",
            edgecolor="black",
            linewidth=0.6,
        )

        for barra in list(b1) + list(b4):
            altura = barra.get_height()
            ax.annotate(
                f"{altura:.0f}",
                xy=(barra.get_x() + barra.get_width() / 2, altura),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.5,
            )

        ax.set_title(nome_cen, fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(ordem_rotulos, rotation=25, ha="right", fontsize=9)
        ax.set_ylabel("Tempo de Espera Médio (unidades de tempo)")
        ax.set_xlabel("Escalonador / Configuração (LRU, 256 quadros)")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend()
        ax.margins(y=0.14)

    fig.suptitle(
        "Comparação do Tempo de Espera Médio por Escalonador e Quantidade de CPUs",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout()
    caminho = os.path.join("resultados", "grafico_1_espera_media.png")
    plt.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


# grafico 2: efeito do tamanho do quantum no round robin
def gerar_grafico_2_efeito_quantum(resultados):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    quantums = [2, 5, 10, 20, 50]

    series = [
        ("A", 1, "Cenário A - 1 CPU", "#1f77b4", "o", "-"),
        ("A", 4, "Cenário A - 4 CPUs", "#ff7f0e", "s", "--"),
        ("B", 1, "Cenário B - 1 CPU", "#2ca02c", "^", "-"),
        ("B", 4, "Cenário B - 4 CPUs", "#d62728", "D", "--"),
    ]

    metricas_paineis = [
        ("espera_media", "Tempo de Espera Médio (unid. tempo)", "Painel 1: Espera Média vs Quantum"),
        ("resposta_media", "Tempo de Resposta Médio (unid. tempo)", "Painel 2: Resposta Média vs Quantum"),
        ("trocas_contexto_total", "Trocas de Contexto (ocorrências)", "Painel 3: Trocas de Contexto vs Quantum"),
    ]

    for idx_p, (chave_metrica, ylabel, titulo_painel) in enumerate(metricas_paineis):
        ax = axes[idx_p]
        for cen, cpus, label, cor, marcador, estilo in series:
            dados_rr = {
                r["quantum"]: r[chave_metrica]
                for r in resultados
                if r["cenario"] == cen
                and r["cpus"] == cpus
                and r["sched"] == "rr"
                and r["subst"] == "lru"
            }
            y_vals = [dados_rr[q] for q in quantums]
            ax.plot(
                quantums,
                y_vals,
                label=label,
                color=cor,
                marker=marcador,
                linestyle=estilo,
                linewidth=1.8,
                markersize=6,
            )

        ax.set_title(titulo_painel, fontsize=11, fontweight="bold")
        ax.set_xlabel("Quantum (unidades úteis de CPU)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(quantums)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(fontsize=8.5)

    fig.suptitle(
        "Efeito do Tamanho do Quantum no Round Robin (LRU, 256 quadros)",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout()
    caminho = os.path.join("resultados", "grafico_2_efeito_quantum_rr.png")
    plt.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


# grafico 3: speedup com 4 cpus comparado com 1 cpu
def gerar_grafico_3_speedup(resultados):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ordem_rotulos = [
        "FCFS",
        "SJF",
        "RR (Q=2)",
        "RR (Q=5)",
        "RR (Q=10)",
        "RR (Q=20)",
        "RR (Q=50)",
        "RR (Q=10) FIFO",
    ]
    x = list(range(len(ordem_rotulos)))
    largura = 0.36

    def obter_speedup(cenario, rotulo):
        for r in resultados:
            if r["cenario"] == cenario and r["cpus"] == 4:
                rot_r = (
                    "RR (Q=10) FIFO"
                    if r["subst"] == "fifo"
                    else r["rotulo_sched"]
                )
                if rot_r == rotulo:
                    return r["speedup"]
        return 0.0

    sp_A = [obter_speedup("A", rot) for rot in ordem_rotulos]
    sp_B = [obter_speedup("B", rot) for rot in ordem_rotulos]

    bA = ax.bar(
        [i - largura / 2 for i in x],
        sp_A,
        width=largura,
        label="Cenário A (Chegadas em t = 0)",
        color="#4C78A8",
        edgecolor="black",
        linewidth=0.6,
    )
    bB = ax.bar(
        [i + largura / 2 for i in x],
        sp_B,
        width=largura,
        label="Cenário B (Chegadas Espaçadas)",
        color="#54A24B",
        edgecolor="black",
        linewidth=0.6,
    )

    ax.axhline(4.0, color="#E45756", linestyle="--", linewidth=1.3, label="Speedup Ideal (4,0)")
    ax.axhline(1.0, color="#888888", linestyle=":", linewidth=1.0, label="Sem Ganho (1,0)")

    for barra in list(bA) + list(bB):
        altura = barra.get_height()
        ax.annotate(
            f"{altura:.2f}",
            xy=(barra.get_x() + barra.get_width() / 2, altura),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )

    ax.set_title(
        "Speedup (1 CPU vs 4 CPUs) por Escalonador e Configuração",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(ordem_rotulos, rotation=20, ha="right")
    ax.set_ylabel("Speedup (Makespan 1 CPU ÷ Makespan 4 CPUs)")
    ax.set_xlabel("Escalonador / Configuração (256 quadros)")
    ax.set_ylim(0, 5.5)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right")

    plt.tight_layout()
    caminho = os.path.join("resultados", "grafico_3_speedup.png")
    plt.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def main():
    os.makedirs("resultados", exist_ok=True)
    configuracoes = obter_configuracoes_experimentos()
    total = len(configuracoes)

    cache_cargas = {
        "dados/cenario_A_t0.json": carregar_e_validar_json("dados/cenario_A_t0.json"),
        "dados/cenario_B_espacadas.json": carregar_e_validar_json("dados/cenario_B_espacadas.json"),
    }

    resultados = []
    inicio_lote = time.time()

    print(f"Iniciando bateria de {total} experimentos oficiais...")
    for idx, cfg in enumerate(configuracoes, start=1):
        t0 = time.time()
        dados_entrada = cache_cargas[cfg["arquivo"]]

        res = executar_simulacao(
            dados_processos=dados_entrada,
            num_cpus=cfg["cpus"],
            escalonador=cfg["sched"],
            quantum=cfg["quantum"] if cfg["quantum"] is not None else 10,
            politica_subst=cfg["subst"],
            num_quadros=cfg["quadros"],
            custo_troca=cfg["custo_troca"],
            ativar_log=False,
        )

        id_exec = identificador_config(cfg)
        rot_sched = rotulo_escalonador(cfg["sched"], cfg["quantum"])

        # salva csv e png do gantt (janela 0 a 200)
        caminho_csv_gantt = os.path.join("resultados", f"gantt_{id_exec}.csv")
        caminho_png_gantt = os.path.join("resultados", f"gantt_{id_exec}.png")
        salvar_gantt_csv(res["gantt"], caminho_csv_gantt)

        titulo_gantt = (
            f"Gantt (0 a 200) — Cenário {cfg['cenario']} | {cfg['cpus']} CPU(s) | "
            f"{rot_sched} | {cfg['subst'].upper()} ({cfg['quadros']} quadros)"
        )
        gerar_figura_gantt(res["gantt"], cfg["cpus"], titulo_gantt, caminho_png_gantt)

        registro = {
            "id_execucao": id_exec,
            "cenario": cfg["cenario"],
            "arquivo": cfg["arquivo"],
            "cpus": cfg["cpus"],
            "sched": cfg["sched"],
            "quantum": cfg["quantum"],
            "rotulo_sched": rot_sched,
            "subst": cfg["subst"],
            "quadros": cfg["quadros"],
            "custo_troca": cfg["custo_troca"],
            "grupo": cfg["grupo"],
            "espera_media": res["espera_media"],
            "espera_maxima": res["espera_maxima"],
            "turnaround_medio": res["turnaround_medio"],
            "resposta_media": res["resposta_media"],
            "makespan": res["makespan"],
            "trocas_contexto_total": res["trocas_contexto_total"],
            "page_faults_total": res["page_faults_total"],
            "total_referencias": res["total_referencias"],
            "taxa_faults_pct": res["taxa_faults_pct"],
            "cpus_metricas": res["cpus"],
            "por_classe": resumir_por_classe(res["processos"]),
            "speedup": None,
            "eficiencia": None,
            "gantt_csv": caminho_csv_gantt,
            "gantt_png": caminho_png_gantt,
        }
        resultados.append(registro)
        dur = time.time() - t0
        print(
            f"[{idx:02d}/{total:02d}] {id_exec:<38} | makespan={res['makespan']:<6} "
            f"| espera_med={res['espera_media']:<8.2f} | faults={res['page_faults_total']:<5} ({dur:.2f}s)"
        )

    # calcula speedup e eficiencia comparando 1 cpu e 4 cpus
    mapa_makespan_1cpu = {}
    for r in resultados:
        if r["cpus"] == 1:
            chave = (r["cenario"], r["sched"], r["quantum"], r["subst"], r["quadros"], r["custo_troca"])
            mapa_makespan_1cpu[chave] = r["makespan"]

    for r in resultados:
        chave = (r["cenario"], r["sched"], r["quantum"], r["subst"], r["quadros"], r["custo_troca"])
        mk_1 = mapa_makespan_1cpu.get(chave)
        if r["cpus"] == 4 and mk_1 is not None:
            r["speedup"] = mk_1 / r["makespan"]
            r["eficiencia"] = r["speedup"] / 4.0

    salvar_tabelas_csv(resultados)
    caminho_json = os.path.join("resultados", "resultados_completos.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    g1 = gerar_grafico_1_espera_media(resultados)
    g2 = gerar_grafico_2_efeito_quantum(resultados)
    g3 = gerar_grafico_3_speedup(resultados)

    tempo_total = time.time() - inicio_lote
    print("-" * 78)
    print(f"Experimentos concluídos com sucesso em {tempo_total:.2f}s!")
    print("Tabelas salvas em:")
    print("  - resultados/tabela_resumo_cenario_A.csv")
    print("  - resultados/tabela_resumo_cenario_B.csv")
    print("  - resultados/tabela_detalhada_por_cpu.csv")
    print("  - resultados/tabela_fifo_vs_lru.csv")
    print("Gráficos comparativos gerados em:")
    print(f"  - {g1}")
    print(f"  - {g2}")
    print(f"  - {g3}")


if __name__ == "__main__":
    main()
