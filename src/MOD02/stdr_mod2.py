"""
SDTR · Módulo II — Simulador de escalonamento Rate Monotonic (RM) e EDF
Simula, em tempo discreto, um conjunto de tarefas periódicas num processador
e indica, para cada política, se algum deadline é falhado.

Executar num terminal:
    python sdtr_mod2.py
"""
from math import ceil, gcd
from functools import reduce

# Conjunto de tarefas: (nome, C = tempo de execução, T = período). Deadline D = T.
TAREFAS = [("T1", 2, 5), ("T2", 3, 7)]


def hiperperiodo(tarefas):
    return reduce(lambda a, b: a * b // gcd(a, b), [t for _, _, t in tarefas])


def utilizacao(tarefas):
    return sum(c / t for _, c, t in tarefas)


def limite_liu_layland(n):
    return n * (2 ** (1 / n) - 1)


def tempo_resposta_rm(tarefas):
    """Análise de tempo de resposta para prioridades fixas (RM: menor período = maior prioridade)."""
    ordenadas = sorted(tarefas, key=lambda x: x[2])
    resultados = {}
    for i, (nome, c, t) in enumerate(ordenadas):
        r = c
        while True:
            novo = c + sum(ceil(r / tj) * cj for _, cj, tj in ordenadas[:i])
            if novo == r or novo > t:
                r = novo
                break
            r = novo
        resultados[nome] = (r, r <= t)
    return resultados


def simular(tarefas, politica):
    """Devolve a linha temporal (quem executa em cada unidade) e a lista de deadlines falhados."""
    H = hiperperiodo(tarefas)
    pendentes = []          # [nome, restante, deadline_absoluto, periodo]
    linha, falhas = [], []
    for instante in range(H):
        for nome, c, t in tarefas:
            if instante % t == 0:
                pendentes.append([nome, c, instante + t, t])
        for p in pendentes:
            if p[1] > 0 and instante >= p[2]:
                falhas.append((p[0], p[2]))
                p[1] = 0
        pendentes = [p for p in pendentes if p[1] > 0]
        if pendentes:
            chave = (lambda p: p[3]) if politica == "RM" else (lambda p: p[2])
            atual = min(pendentes, key=chave)
            atual[1] -= 1
            linha.append(atual[0])
        else:
            linha.append("-")
    for p in pendentes:
        if p[1] > 0:
            falhas.append((p[0], p[2]))
    return linha, falhas


if __name__ == "__main__":
    n = len(TAREFAS)
    U = utilizacao(TAREFAS)
    print(f"Tarefas: {TAREFAS}")
    print(f"Utilização U = {U:.3f} | limite de Liu & Layland para n={n}: {limite_liu_layland(n):.3f}")
    print(f"Hiperperíodo: {hiperperiodo(TAREFAS)}")
    print("Análise de tempo de resposta (RM):")
    for nome, (r, ok) in tempo_resposta_rm(TAREFAS).items():
        print(f"  {nome}: R = {r} -> {'cumpre' if ok else 'FALHA'}")
    for politica in ("RM", "EDF"):
        linha, falhas = simular(TAREFAS, politica)
        print(f"\n{politica}: {''.join(x[-1] if x != '-' else '.' for x in linha)}")
        print(f"  deadlines falhados: {falhas if falhas else 'nenhum'}")