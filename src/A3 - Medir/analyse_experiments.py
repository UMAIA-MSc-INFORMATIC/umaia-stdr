"""
Análise agregada dos quatro experimentos MQTT.

O script percorre automaticamente todas as pastas RunNNN existentes,
lê os respetivos data.jsonl, remove ocorrências duplicadas da mesma
sequência dentro de cada Run e gera um histograma agregado por condição.

Estrutura esperada:
Experiments/
  exp1_qos0_sem_carga/Run000/data.jsonl
  exp2_qos0_com_carga/Run000/data.jsonl
  exp3_qos1_sem_carga/Run000/data.jsonl
  exp4_qos1_com_carga/Run000/data.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import matplotlib.pyplot as plt


# Experimentos oficiais e nomes a apresentar nos gráficos/CSV.
EXPERIMENTS = {
    "exp1_qos0_sem_carga": "QoS 0 - sem carga",
    "exp2_qos0_com_carga": "QoS 0 - com carga",
    "exp3_qos1_sem_carga": "QoS 1 - sem carga",
    "exp4_qos1_com_carga": "QoS 1 - com carga",
}


def argumentos():
    parser = argparse.ArgumentParser(
        description="Gera histogramas e estatísticas agregadas de todas as Runs MQTT."
    )
    parser.add_argument(
        "--experiments-dir",
        default="Experiments",
        help="Pasta raiz dos experimentos (default: Experiments).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Pasta de saída. Default: <experiments-dir>/Aggregated.",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=50,
        help="Número de classes de cada histograma (default: 50).",
    )
    parser.add_argument(
        "--expected-runs",
        type=int,
        default=5,
        help="Número esperado de Runs por condição (default: 5).",
    )
    parser.add_argument(
        "--expected-per-run",
        type=int,
        default=1000,
        help="Número esperado de mensagens únicas por Run (default: 1000).",
    )
    return parser.parse_args()


def percentil_linear(valores: list[float], percentagem: float) -> float:
    """Calcula um percentil por interpolação linear."""
    ordenados = sorted(valores)
    posicao = (len(ordenados) - 1) * percentagem / 100.0
    inferior = math.floor(posicao)
    superior = math.ceil(posicao)
    if inferior == superior:
        return ordenados[inferior]
    peso = posicao - inferior
    return ordenados[inferior] * (1 - peso) + ordenados[superior] * peso


def carregar_run(data_path: Path) -> tuple[list[dict], int]:
    """
    Lê uma Run e conserva apenas a primeira ocorrência de cada sequence.
    Retorna os registos únicos e a quantidade de duplicados encontrada.
    """
    por_sequencia: dict[int, dict] = {}
    duplicados = 0

    with data_path.open("r", encoding="utf-8") as ficheiro:
        for numero_linha, linha in enumerate(ficheiro, 1):
            if not linha.strip():
                continue
            try:
                item = json.loads(linha)
                sequencia = int(item["sequence"])
                latencia = float(item["latency_ms"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as erro:
                raise ValueError(
                    f"{data_path}, linha {numero_linha}: registo inválido ({erro})."
                ) from erro

            # Não permitimos latências negativas silenciosamente.
            if latencia < 0:
                raise ValueError(
                    f"{data_path}, linha {numero_linha}: latency_ms negativa ({latencia})."
                )

            item["sequence"] = sequencia
            item["latency_ms"] = latencia

            if sequencia in por_sequencia:
                duplicados += 1
            else:
                por_sequencia[sequencia] = item

    return [por_sequencia[s] for s in sorted(por_sequencia)], duplicados


def calcular_jitter_global(registos_por_run: list[list[dict]]) -> float:
    """
    Calcula o jitter dentro de cada Run e agrega todas as diferenças.

    Não calcula a diferença artificial entre a última mensagem de uma Run
    e a primeira da Run seguinte, pois essas mensagens não são consecutivas
    na mesma execução experimental.
    """
    diferencas: list[float] = []
    for registos in registos_por_run:
        latencias = [r["latency_ms"] for r in registos]
        diferencas.extend(abs(b - a) for a, b in zip(latencias, latencias[1:]))
    return statistics.fmean(diferencas) if diferencas else 0.0


def main():
    args = argumentos()
    if args.bins <= 0 or args.expected_runs <= 0 or args.expected_per_run <= 0:
        raise SystemExit("--bins, --expected-runs e --expected-per-run devem ser > 0.")

    raiz = Path(args.experiments_dir)
    if not raiz.is_dir():
        raise SystemExit(f"Pasta de experimentos não encontrada: {raiz.resolve()}")

    saida = Path(args.output_dir) if args.output_dir else raiz / "Aggregated"
    saida.mkdir(parents=True, exist_ok=True)

    expected_total = args.expected_runs * args.expected_per_run
    resumos: list[dict] = []
    houve_aviso = False

    print("\nValidação das condições")
    print("=" * 72)

    for experiment_name, label in EXPERIMENTS.items():
        experiment_dir = raiz / experiment_name
        if not experiment_dir.is_dir():
            print(f"ERRO  {experiment_name}: pasta não encontrada.")
            houve_aviso = True
            continue

        # Apenas diretórios RunNNN que realmente têm data.jsonl são considerados.
        runs = sorted(
            p for p in experiment_dir.glob("Run[0-9][0-9][0-9]")
            if p.is_dir() and (p / "data.jsonl").is_file()
        )

        registos_por_run: list[list[dict]] = []
        duplicados_total = 0
        detalhes_runs = []

        for run_dir in runs:
            registos, duplicados = carregar_run(run_dir / "data.jsonl")
            registos_por_run.append(registos)
            duplicados_total += duplicados
            detalhes_runs.append((run_dir.name, len(registos), duplicados))

        latencias = [
            item["latency_ms"]
            for registos in registos_por_run
            for item in registos
        ]

        if not latencias:
            print(f"ERRO  {experiment_name}: nenhum dado válido encontrado.")
            houve_aviso = True
            continue

        runs_ok = len(runs) == args.expected_runs
        samples_ok = len(latencias) == expected_total
        status = "OK" if runs_ok and samples_ok else "AVISO"
        print(
            f"{status:5} {experiment_name}: {len(runs)} Runs | "
            f"{len(latencias)} mensagens únicas | {duplicados_total} duplicados"
        )
        if not runs_ok or not samples_ok:
            houve_aviso = True
            print(
                f"      Esperado: {args.expected_runs} Runs e {expected_total} mensagens únicas."
            )
            for nome_run, quantidade, duplicados in detalhes_runs:
                print(f"      {nome_run}: {quantidade} únicas, {duplicados} duplicados")

        # Métricas agregadas são recalculadas diretamente sobre todas as observações.
        resumo = {
            "experiment": experiment_name,
            "condition": label,
            "runs": len(runs),
            "samples_unique": len(latencias),
            "duplicates": duplicados_total,
            "min_ms": min(latencias),
            "mean_ms": statistics.fmean(latencias),
            "median_ms": statistics.median(latencias),
            "p99_ms": percentil_linear(latencias, 99),
            "max_ms": max(latencias),
            "jitter_mean_abs_ms": calcular_jitter_global(registos_por_run),
            "standard_deviation_ms": statistics.stdev(latencias) if len(latencias) > 1 else 0.0,
        }
        resumos.append(resumo)

        # Um histograma por condição com todas as observações das Runs existentes.
        plt.figure(figsize=(10, 5.5))
        plt.hist(latencias, bins=args.bins, edgecolor="black")
        plt.title(f"Distribuição agregada das latências - {label}")
        plt.xlabel("Latência (ms)")
        plt.ylabel("Frequência")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        hist_path = saida / f"histogram_{experiment_name}.png"
        plt.savefig(hist_path, dpi=180)
        plt.close()

    if not resumos:
        raise SystemExit("Nenhum experimento pôde ser analisado.")

    # CSV consolidado para utilização direta no relatório.
    csv_path = saida / "aggregated_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as ficheiro:
        writer = csv.DictWriter(ficheiro, fieldnames=list(resumos[0].keys()))
        writer.writeheader()
        writer.writerows(resumos)

    print("\nResumo agregado")
    print("=" * 118)
    print(
        f"{'Condição':24} {'N':>6} {'Mín':>10} {'Média':>10} {'Mediana':>10} "
        f"{'P99':>10} {'Máx':>10} {'Jitter':>10}"
    )
    print("-" * 118)
    for r in resumos:
        print(
            f"{r['condition'][:24]:24} {r['samples_unique']:6d} "
            f"{r['min_ms']:10.4f} {r['mean_ms']:10.4f} {r['median_ms']:10.4f} "
            f"{r['p99_ms']:10.4f} {r['max_ms']:10.4f} "
            f"{r['jitter_mean_abs_ms']:10.4f}"
        )

    print(f"\nResultados criados em: {saida.resolve()}")
    print(f"Resumo CSV: {csv_path.name}")
    print("Histogramas: um PNG agregado por condição.")
    if houve_aviso:
        print("\nATENÇÃO: foram encontrados desvios face ao número esperado de Runs/mensagens.")
        print("Confirme os avisos acima antes de utilizar os gráficos no relatório.")


if __name__ == "__main__":
    main()
