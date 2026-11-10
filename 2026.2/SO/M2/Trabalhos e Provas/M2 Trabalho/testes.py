import os
import unittest
from simulador import carregar_e_validar_json, executar_simulacao, gerar_figura_gantt


# testes dos exemplos do pdf do professor
class TestesSimulador(unittest.TestCase):

    # exemplo 5.4: processo 17 sozinho sem page fault e sem troca
    def test_5_4_processo_17_sem_faults(self):
        carga = [
            {
                "pid": 17,
                "chegada": 342,
                "classe": "curto",
                "paginas": 6,
                "bursts": [
                    {"cpu": 4, "refs": [0, 1, 1, 2]},
                    {"es": 12},
                    {"cpu": 3, "refs": [2, 3, 3]},
                ],
            }
        ]
        res = executar_simulacao(
            carga,
            num_cpus=1,
            escalonador="fcfs",
            custo_troca=0,
            usar_memoria=False,
        )
        p17 = res["processos"][0]
        self.assertEqual(p17.tempo_espera, 0)
        self.assertEqual(p17.tempo_termino, 361)
        self.assertEqual(p17.tempo_termino - p17.chegada, 19)
        self.assertEqual(res["cpus"][0]["tempo_util"], 7)

    # exemplo 5.5: processo 17 sozinho com page faults de 20 unidades
    def test_5_5_processo_17_com_faults(self):
        carga = [
            {
                "pid": 17,
                "chegada": 342,
                "classe": "curto",
                "paginas": 6,
                "bursts": [
                    {"cpu": 4, "refs": [0, 1, 1, 2]},
                    {"es": 12},
                    {"cpu": 3, "refs": [2, 3, 3]},
                ],
            }
        ]
        res = executar_simulacao(
            carga,
            num_cpus=1,
            escalonador="fcfs",
            politica_subst="lru",
            num_quadros=256,
            custo_troca=0,
            usar_memoria=True,
            duracao_fault=20,
        )
        p17 = res["processos"][0]
        self.assertEqual(p17.tempo_espera, 0)
        self.assertEqual(p17.tempo_termino, 441)
        self.assertEqual(p17.tempo_termino - p17.chegada, 99)
        self.assertEqual(res["page_faults_total"], 4)

    def _carga_7_1(self):
        return [
            {
                "pid": 1,
                "chegada": 0,
                "classe": "curto",
                "paginas": 1,
                "bursts": [{"cpu": 5, "refs": [0, 0, 0, 0, 0]}],
            },
            {
                "pid": 2,
                "chegada": 0,
                "classe": "curto",
                "paginas": 1,
                "bursts": [{"cpu": 3, "refs": [0, 0, 0]}],
            },
            {
                "pid": 3,
                "chegada": 2,
                "classe": "curto",
                "paginas": 1,
                "bursts": [{"cpu": 2, "refs": [0, 0]}],
            },
        ]

    # exemplo 7.1 no fcfs sem memoria
    def test_7_1_fcfs_sem_memoria(self):
        res = executar_simulacao(
            self._carga_7_1(),
            num_cpus=1,
            escalonador="fcfs",
            custo_troca=1,
            usar_memoria=False,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [0, 6, 8])
        self.assertEqual(
            [p1.primeiro_despacho - p1.chegada, p2.primeiro_despacho - p2.chegada, p3.primeiro_despacho - p3.chegada],
            [0, 6, 8],
        )
        self.assertEqual(
            [p1.tempo_termino - p1.chegada, p2.tempo_termino - p2.chegada, p3.tempo_termino - p3.chegada],
            [6, 10, 11],
        )
        self.assertEqual(res["makespan"], 13)
        self.assertEqual(res["cpus"][0]["tempo_util"], 10)
        self.assertEqual(res["cpus"][0]["tempo_troca"], 3)
        self.assertEqual(res["cpus"][0]["tempo_ocioso"], 0)
        self.assertAlmostEqual(res["espera_media"], 14.0 / 3.0, places=4)
        self.assertAlmostEqual(res["turnaround_medio"], 9.0, places=4)

    # exemplo 7.1 no sjf sem memoria
    def test_7_1_sjf_sem_memoria(self):
        res = executar_simulacao(
            self._carga_7_1(),
            num_cpus=1,
            escalonador="sjf",
            custo_troca=1,
            usar_memoria=False,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [7, 0, 2])
        self.assertEqual(
            [p1.primeiro_despacho - p1.chegada, p2.primeiro_despacho - p2.chegada, p3.primeiro_despacho - p3.chegada],
            [7, 0, 2],
        )
        self.assertEqual(
            [p1.tempo_termino - p1.chegada, p2.tempo_termino - p2.chegada, p3.tempo_termino - p3.chegada],
            [13, 4, 5],
        )
        self.assertEqual(res["makespan"], 13)
        self.assertEqual(res["cpus"][0]["tempo_util"], 10)
        self.assertEqual(res["cpus"][0]["tempo_troca"], 3)
        self.assertEqual(res["cpus"][0]["tempo_ocioso"], 0)

    # exemplo 7.1 no round robin quantum 2 sem memoria
    def test_7_1_rr_quantum_2_sem_memoria(self):
        res = executar_simulacao(
            self._carga_7_1(),
            num_cpus=1,
            escalonador="rr",
            quantum=2,
            custo_troca=1,
            usar_memoria=False,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [8, 9, 4])
        self.assertEqual(
            [p1.primeiro_despacho - p1.chegada, p2.primeiro_despacho - p2.chegada, p3.primeiro_despacho - p3.chegada],
            [0, 3, 4],
        )
        self.assertEqual(
            [p1.tempo_termino - p1.chegada, p2.tempo_termino - p2.chegada, p3.tempo_termino - p3.chegada],
            [16, 14, 7],
        )
        self.assertEqual(res["makespan"], 16)
        self.assertEqual(res["cpus"][0]["tempo_util"], 10)
        self.assertEqual(res["cpus"][0]["tempo_troca"], 6)
        self.assertEqual(res["cpus"][0]["tempo_ocioso"], 0)

    # exemplo 7.2 com faults e fila
    def test_7_2_com_page_faults_e_fila(self):
        carga = [
            {"pid": 1, "chegada": 0, "classe": "curto", "paginas": 2, "bursts": [{"cpu": 2, "refs": [0, 1]}]},
            {"pid": 2, "chegada": 1, "classe": "curto", "paginas": 2, "bursts": [{"cpu": 2, "refs": [0, 1]}]},
            {"pid": 3, "chegada": 2, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 1, "refs": [0]}]},
        ]
        res = executar_simulacao(
            carga,
            num_cpus=1,
            escalonador="fcfs",
            politica_subst="lru",
            num_quadros=256,
            custo_troca=0,
            usar_memoria=True,
            duracao_fault=5,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_termino, p2.tempo_termino, p3.tempo_termino], [12, 13, 8])
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [0, 0, 0])
        self.assertEqual(
            [p1.tempo_termino - p1.chegada, p2.tempo_termino - p2.chegada, p3.tempo_termino - p3.chegada],
            [12, 12, 6],
        )
        self.assertEqual(res["makespan"], 13)
        self.assertEqual(res["page_faults_total"], 5)

    def _carga_7_3(self):
        return [
            {"pid": 1, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 4, "refs": [0, 0, 0, 0]}]},
            {"pid": 2, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 3, "refs": [0, 0, 0]}]},
            {"pid": 3, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 2, "refs": [0, 0]}]},
        ]

    # exemplo 7.3 no fcfs
    def test_7_3_fcfs(self):
        res = executar_simulacao(
            self._carga_7_3(),
            num_cpus=1,
            escalonador="fcfs",
            politica_subst="lru",
            num_quadros=256,
            custo_troca=0,
            usar_memoria=True,
            duracao_fault=20,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [0, 4, 7])
        self.assertAlmostEqual(res["espera_media"], 11.0 / 3.0, places=2)
        self.assertEqual(res["makespan"], 29)

    # exemplo 7.3 no sjf
    def test_7_3_sjf(self):
        res = executar_simulacao(
            self._carga_7_3(),
            num_cpus=1,
            escalonador="sjf",
            politica_subst="lru",
            num_quadros=256,
            custo_troca=0,
            usar_memoria=True,
            duracao_fault=20,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual([p1.tempo_espera, p2.tempo_espera, p3.tempo_espera], [5, 2, 0])
        self.assertAlmostEqual(res["espera_media"], 7.0 / 3.0, places=2)
        self.assertEqual(res["makespan"], 29)

    # verifica diferenca de vitima entre fifo e lru
    def test_escolha_vitima_fifo_vs_lru(self):
        carga = [
            {
                "pid": 1,
                "chegada": 0,
                "classe": "curto",
                "paginas": 3,
                "bursts": [{"cpu": 5, "refs": [0, 1, 0, 2, 0]}],
            }
        ]
        res_fifo = executar_simulacao(
            carga, num_cpus=1, escalonador="fcfs", politica_subst="fifo", num_quadros=2, custo_troca=0
        )
        res_lru = executar_simulacao(
            carga, num_cpus=1, escalonador="fcfs", politica_subst="lru", num_quadros=2, custo_troca=0
        )
        self.assertEqual(res_fifo["page_faults_total"], 4)
        self.assertEqual(res_lru["page_faults_total"], 3)

    # teste da protecao de pagina e retentativa se nao tiver vitima
    def test_protecao_pagina_e_retentativa_sem_vitima(self):
        carga = [
            {"pid": 1, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 2, "refs": [0, 0]}]},
            {"pid": 2, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 2, "refs": [0, 0]}]},
            {"pid": 3, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 2, "refs": [0, 0]}]},
        ]
        res = executar_simulacao(
            carga,
            num_cpus=1,
            escalonador="fcfs",
            politica_subst="lru",
            num_quadros=2,
            custo_troca=0,
            usar_memoria=True,
            duracao_fault=20,
        )
        p1, p2, p3 = res["processos"]
        self.assertEqual(res["page_faults_total"], 3)
        self.assertEqual(p1.tempo_termino, 22)
        self.assertEqual(p2.tempo_termino, 24)
        self.assertEqual(p3.tempo_termino, 42)

    # no rr se a fila esta vazia o mesmo processo continua sem troca
    def test_rr_sem_concorrente_continua_sem_troca(self):
        carga = [
            {"pid": 1, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 6, "refs": [0] * 6}]}
        ]
        res = executar_simulacao(
            carga,
            num_cpus=1,
            escalonador="rr",
            quantum=2,
            custo_troca=1,
            usar_memoria=False,
        )
        self.assertEqual(res["trocas_contexto_total"], 1)
        self.assertEqual(res["makespan"], 7)

    # com 4 cpus e 4 processos todos sao atendidos juntos
    def test_despacho_4_cpus_e_eventos_simultaneos(self):
        carga = [
            {"pid": i, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 3, "refs": [0, 0, 0]}]}
            for i in range(1, 5)
        ]
        res = executar_simulacao(
            carga,
            num_cpus=4,
            escalonador="fcfs",
            custo_troca=1,
            usar_memoria=False,
        )
        self.assertEqual(res["makespan"], 4)
        for c in res["cpus"]:
            self.assertEqual(c["tempo_troca"], 1)
            self.assertEqual(c["tempo_util"], 3)
            self.assertEqual(c["tempo_ocioso"], 0)

    # garante que processos com retorno simultaneo permaneçam em bloqueados ate seu proprio evento
    def test_preservacao_bloqueados_em_retornos_simultaneos(self):
        carga = [
            {"pid": 1, "chegada": 0, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 1, "refs": [0]}, {"es": 10}, {"cpu": 1, "refs": [0]}]},
            {"pid": 2, "chegada": 1, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 1, "refs": [0]}, {"es": 9}, {"cpu": 1, "refs": [0]}]},
            {"pid": 3, "chegada": 2, "classe": "curto", "paginas": 1, "bursts": [{"cpu": 1, "refs": [0]}, {"es": 8}, {"cpu": 1, "refs": [0]}]},
        ]
        res = executar_simulacao(
            carga, num_cpus=1, escalonador="fcfs", custo_troca=0, usar_memoria=False, ativar_log=True
        )
        retorno_p1 = [l for l in res["logs"] if "evento=RETORNO_ES | pid=P1" in l][0]
        self.assertIn("bloqueados=[P2(ret=11,ES), P3(ret=11,ES)]", retorno_p1)

    # testa a geracao da figura de gantt com paineis ampliados e rotulos curtos
    def test_geracao_figura_gantt(self):
        gantt = [
            [0, 0, 2, "OCIOSA"],
            [0, 2, 5, "TROCA"],
            [0, 5, 6, "P1"],
            [0, 6, 8, "P2"],
        ]
        caminho_teste = "resultados/teste_gantt_unitario.png"
        gerar_figura_gantt(gantt, 1, "Teste Unitário", caminho_teste, limite_janela=50)
        self.assertTrue(os.path.exists(caminho_teste))
        self.assertGreater(os.path.getsize(caminho_teste), 1000)
        if os.path.exists(caminho_teste):
            os.remove(caminho_teste)

    # le os dois arquivos json oficiais e confere se a soma bate
    def test_validacao_cargas_oficiais(self):
        for caminho in ("dados/cenario_A_t0.json", "dados/cenario_B_espacadas.json"):
            dados = carregar_e_validar_json(caminho)
            self.assertEqual(len(dados), 1000)
            soma_cpu = sum(b["cpu"] for p in dados for b in p["bursts"] if "cpu" in b)
            soma_refs = sum(len(b["refs"]) for p in dados for b in p["bursts"] if "refs" in b)
            self.assertEqual(soma_cpu, soma_refs)
            self.assertEqual(soma_cpu, 52678)


if __name__ == "__main__":
    unittest.main(verbosity=2)
