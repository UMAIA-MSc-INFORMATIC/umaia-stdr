"""
SDTR · Módulo III — Simulador de um barramento CAN
1) Mostra a arbitragem bit a bit entre nós que começam a transmitir ao mesmo tempo.
2) Simula mensagens periódicas num barramento CAN (prioridade pelo identificador,
   transmissão não preemptiva) e mede o pior tempo de resposta de cada mensagem.

Executar num terminal:
    python sdtr_mod3.py
"""
import random

BITRATE = 500_000  # bit/s (CAN clássico até 1 Mbit/s)

# Mensagens: (nome, identificador de 11 bits, bytes de dados, período em ms)
MENSAGENS = [
    ("travagem", 0x010, 2, 5),
    ("motor", 0x0A0, 8, 10),
    ("direcao", 0x120, 4, 10),
    ("painel", 0x400, 8, 50),
    ("diagnostico", 0x005, 8, 2),
]


def bits_trama(n_bytes):
    """Pior caso de bits de uma trama CAN 2.0A com bit stuffing (Davis et al., 2007)."""
    return 8 * n_bytes + 47 + (34 + 8 * n_bytes - 1) // 4


def tempo_trama_ms(n_bytes):
    return bits_trama(n_bytes) / BITRATE * 1000


def arbitragem(ids):
    """Arbitragem bit a bit: o bit 0 (dominante) sobrepõe-se ao bit 1 (recessivo)."""
    ativos = list(ids)
    print("Arbitragem entre:", ", ".join(f"0x{i:03X}" for i in ids))
    for bit in range(10, -1, -1):
        valores = {i: (i >> bit) & 1 for i in ativos}
        barramento = min(valores.values())          # 0 dominante
        perdem = [i for i in ativos if valores[i] != barramento]
        if perdem:
            print(f"  bit {10 - bit:2d}: barramento={barramento} -> perdem "
                  + ", ".join(f"0x{i:03X}" for i in perdem))
        ativos = [i for i in ativos if valores[i] == barramento]
    print(f"  vence 0x{ativos[0]:03X} (identificador mais baixo = maior prioridade)\n")
    return ativos[0]


def simular(mensagens, duracao_ms=1000, passo_ms=0.001, desfasamento=True, semente=1):
    """Simulação em tempo discreto do barramento; devolve o pior tempo de resposta por mensagem."""
    random.seed(semente)
    fase = {m[0]: (random.uniform(0, m[3]) if desfasamento else 0.0) for m in mensagens}
    proxima = dict(fase)
    fila = []                      # [nome, id, instante_de_chegada, duracao]
    em_tx, fim_tx = None, 0.0
    pior = {m[0]: 0.0 for m in mensagens}
    t = 0.0
    while t < duracao_ms:
        for nome, ident, nb, per in mensagens:
            if t >= proxima[nome]:
                fila.append([nome, ident, proxima[nome], tempo_trama_ms(nb)])
                proxima[nome] += per
        if em_tx and t >= fim_tx:
            nome, _, chegada, _ = em_tx
            pior[nome] = max(pior[nome], fim_tx - chegada)
            em_tx = None
        if em_tx is None and fila:
            fila.sort(key=lambda m: m[1])  # arbitragem: identificador mais baixo primeiro
            em_tx = fila.pop(0)
            fim_tx = t + em_tx[3]
        t += passo_ms
    return pior


if __name__ == "__main__":
    arbitragem([0x0A0, 0x120, 0x010])
    print(f"Débito: {BITRATE // 1000} kbit/s")
    carga = sum(tempo_trama_ms(nb) / per for _, _, nb, per in MENSAGENS)
    print(f"Utilização do barramento: {100 * carga:.1f}%\n")
    aleatorio = simular(MENSAGENS, desfasamento=True)
    sincrono = simular(MENSAGENS, desfasamento=False)
    print(f"{'mensagem':10} {'ID':>6} {'bytes':>5} {'trama':>9} {'período':>8} {'pior (fases aleat.)':>20} {'pior (simultâneo)':>18}")
    for nome, ident, nb, per in MENSAGENS:
        print(f"{nome:10} 0x{ident:03X} {nb:>5} {tempo_trama_ms(nb):>6.3f} ms {per:>5} ms "
              f"{aleatorio[nome]:>17.3f} ms {sincrono[nome]:>15.3f} ms")