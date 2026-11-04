# menu interativo de terminal para rodar o simulador
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def escolher(titulo, opcoes, padrao=None):
    print('\n' + titulo)
    for chave, descricao in opcoes.items():
        print(f'  [{chave}] {descricao}')
    while True:
        dica = f' [Enter = {padrao}]' if padrao is not None else ''
        resposta = input(f'Opção{dica}: ').strip()
        if not resposta and padrao is not None:
            resposta = padrao
        if resposta in opcoes:
            return resposta
        print('Opção inválida. Digite um dos números acima.')


def ler_inteiro(titulo, padrao, minimo):
    while True:
        texto = input(f'{titulo} [Enter = {padrao}]: ').strip()
        try:
            valor = int(texto) if texto else padrao
            if valor >= minimo:
                return valor
        except ValueError:
            pass
        print(f'Digite um inteiro maior ou igual a {minimo}.')


def configurar():
    cenario = escolher('1. Escolha o cenário:', {
        '1': 'Cenário A (1000 processos em t = 0)',
        '2': 'Cenário B (chegadas espaçadas no tempo)',
        '0': 'Sair',
    })
    if cenario == '0':
        return None
    arquivo = 'cenario_A_t0.json' if cenario == '1' else 'cenario_B_espacadas.json'
    cpus = escolher('2. Quantidade de CPUs:', {'1': '1 CPU', '2': '4 CPUs'})
    sched = escolher('3. Escalonador:', {'1': 'FCFS', '2': 'SJF', '3': 'Round Robin (RR)'})
    comando = [sys.executable, '-X', 'utf8', 'simulador.py', '--arquivo', 'dados/' + arquivo,
               '--cpus', '1' if cpus == '1' else '4',
               '--sched', {'1': 'fcfs', '2': 'sjf', '3': 'rr'}[sched]]
    if sched == '3':
        comando += ['--quantum', str(ler_inteiro('Quantum do RR', 10, 1))]
    subst = escolher('4. Política de memória:', {'1': 'LRU', '2': 'FIFO'}, padrao='1')
    print('\n5. Memória e troca de contexto:')
    quadros = ler_inteiro('Quantidade de quadros', 256, 1)
    custo = ler_inteiro('Custo da troca', 1, 0)
    log = escolher('6. Gerar log detalhado? (Com 1000 processos, o arquivo pode ser grande.)',
                   {'1': 'Não', '2': 'Sim'}, padrao='1')
    comando += ['--subst', 'lru' if subst == '1' else 'fifo',
                '--quadros', str(quadros), '--custo-troca', str(custo)]
    if log == '2':
        comando.append('--log')
    return comando


def main():
    try:
        while True:
            print('\n' + '=' * 55)
            print('SIMULADOR DE SISTEMAS OPERACIONAIS - MENU')
            print('=' * 55)
            comando = configurar()
            if comando is None:
                break
            print('\nComando equivalente (na pasta do projeto):')
            print('python ' + ' '.join(comando[3:]))
            print('\nExecutando...\n', flush=True)
            # Reutiliza a interface oficial, sem duplicar regras de simulação.
            resultado = subprocess.run(comando, cwd=RAIZ)
            if resultado.returncode != 0:
                print('\nA execução falhou. Confira a mensagem acima.')
            novamente = escolher('\nExecutar outra configuração?', {'1': 'Sim', '0': 'Sair'}, padrao='0')
            if novamente == '0':
                break
    except (KeyboardInterrupt, EOFError):
        print('\nMenu encerrado.')


if __name__ == '__main__':
    main()
