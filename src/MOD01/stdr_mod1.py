"""
SDTR · Módulo I — Medir latência e deadlines entre dois processos
Um "sensor" envia leituras por UDP a cada PERIODO_MS; um "controlador"
recebe-as, mede a latência e conta quantas falharam o DEADLINE_MS.

Correr num terminal:
    python sdtr_mod1.py
"""
import json
import multiprocessing as mp
import random
import socket
import statistics
import time

HOST, PORTA = "127.0.0.1", 50007
PERIODO_MS = 10        # o sensor envia uma leitura a cada 10 ms
# PERIODO_MS = 1        # o sensor envia uma leitura a cada 10 ms
DEADLINE_MS = 2.0      # a leitura tem de chegar em menos de 2 ms
# DEADLINE_MS = 4.0      # a leitura tem de chegar em menos de 4 ms
N_MENSAGENS = 500
ATRASO_REDE_MS = (0.0, 3.0)   # atraso artificial: simula uma rede imprevisível


def sensor():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxima = time.perf_counter()
    for i in range(N_MENSAGENS):
        # atraso aleatório antes de enviar = "rede" a introduzir latência variável
        time.sleep(random.uniform(*ATRASO_REDE_MS) / 1000)
        msg = {"seq": i, "t_amostra": proxima, "valor": round(random.gauss(21, 0.5), 2)}
        s.sendto(json.dumps(msg).encode(), (HOST, PORTA))
        proxima += PERIODO_MS / 1000
        espera = proxima - time.perf_counter()
        if espera > 0:
            time.sleep(espera)
    s.sendto(b"FIM", (HOST, PORTA))


def controlador(pronto):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORTA))
    pronto.set()
    latencias, falhas = [], 0
    while True:
        dados, _ = s.recvfrom(1024)
        if dados == b"FIM":
            break
        t_chegada = time.perf_counter()
        msg = json.loads(dados)
        lat_ms = (t_chegada - msg["t_amostra"]) * 1000
        latencias.append(lat_ms)
        if lat_ms > DEADLINE_MS:
            falhas += 1

    latencias.sort()
    p99 = latencias[int(0.99 * (len(latencias) - 1))]
    jitter = statistics.pstdev(latencias)
    print(f"Variáveis:\nPERIODO_MS: {PERIODO_MS}\nDEADLINE_MS: {DEADLINE_MS}\nATRASO_REDE_MS: {ATRASO_REDE_MS}")
    print(f"Mensagens recebidas : {len(latencias)} de {N_MENSAGENS}")
    print(f"Latência mín / média: {latencias[0]:.3f} / {statistics.mean(latencias):.3f} ms")
    print(f"Latência p99 / máx  : {p99:.3f} / {latencias[-1]:.3f} ms")
    print(f"Jitter (desvio-pad.): {jitter:.3f} ms")
    print(f"Deadline {DEADLINE_MS} ms falhado em {falhas} mensagens "
          f"({100 * falhas / len(latencias):.1f}%)")
    print(f"Latência mín {latencias[0]:.3f} ms média: {statistics.mean(latencias):.3f} ms  -  p99: {p99:.3f} -  máx: {latencias[-1]:.3f} ms")


if __name__ == "__main__":
    # perf_counter só é comparável entre processos na mesma máquina (relógio monotónico do SO)
    pronto = mp.Event()
    c = mp.Process(target=controlador, args=(pronto,))
    c.start()
    pronto.wait()
    sensor()
    c.join()