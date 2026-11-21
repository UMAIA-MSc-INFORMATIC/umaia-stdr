"""Analisa uma RunNNN e grava resultados na própria pasta."""

import argparse
import csv
import json
import math
import statistics

import matplotlib.pyplot as plt

from experiment_utils import resolve_run, update_metadata, utc_now


def argumentos():
    p = argparse.ArgumentParser(description="Analisa a execução mais recente ou uma Run específica.")
    p.add_argument("--experiment", required=True, help="Nome da experiência.")
    p.add_argument("--run", type=int, default=None, help="Número da Run; omitir usa a mais recente com dados.")
    p.add_argument("--bins", type=int, default=40)
    p.add_argument("--expected", type=int, default=None,
                   help="Substitui o esperado do metadata; normalmente não é necessário.")
    return p.parse_args()


def percentile(values, pct):
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct / 100
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper: return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def main():
    args = argumentos()
    if args.bins <= 0:
        raise SystemExit("--bins deve ser > 0.")
    run_number, run_dir = resolve_run(args.experiment, args.run)
    data_path = run_dir / "data.jsonl"
    metadata_path = run_dir / "metadata.json"
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    expected = args.expected or int(metadata.get("measurement", {}).get("expected_messages", 1000))

    records = []
    with data_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip(): continue
            try:
                item = json.loads(line)
                item["sequence"] = int(item["sequence"])
                item["latency_ms"] = float(item["latency_ms"])
                records.append(item)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Linha {line_no} inválida: {error}") from error
    if not records:
        raise SystemExit("O ficheiro data.jsonl não contém registos válidos.")

    by_sequence = {}
    duplicates = 0
    for item in records:
        if item["sequence"] in by_sequence: duplicates += 1
        else: by_sequence[item["sequence"]] = item
    unique = [by_sequence[s] for s in sorted(by_sequence)]
    latencies = [r["latency_ms"] for r in unique]
    jitter = statistics.fmean(abs(b - a) for a, b in zip(latencies, latencies[1:])) if len(latencies) > 1 else 0.0
    summary = {
        "experiment": args.experiment, "run": run_number,
        "received_unique": len(unique), "expected": expected,
        "lost": max(0, expected - len(unique)),
        "loss_pct": max(0, expected - len(unique)) / expected * 100,
        "duplicates": duplicates, "min_ms": min(latencies),
        "mean_ms": statistics.fmean(latencies), "p99_ms": percentile(latencies, 99),
        "max_ms": max(latencies), "jitter_mean_abs_ms": jitter,
        "standard_deviation_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
    }

    summary_path = run_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=summary.keys())
        writer.writeheader(); writer.writerow(summary)

    histogram_path = run_dir / "histogram.png"
    plt.figure(figsize=(9, 5))
    plt.hist(latencies, bins=args.bins, edgecolor="black")
    plt.title(f"Histograma das latências - {args.experiment} / Run{run_number:03d}")
    plt.xlabel("Latência (ms)"); plt.ylabel("Frequência")
    plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(histogram_path, dpi=160); plt.close()

    def register(m):
        m["analysis"] = {"status": "completed", "analysed_at_utc": utc_now(),
                         "jitter_definition": "mean(abs(L_i - L_(i-1)))", **summary}
        m.setdefault("files", {}).update({"summary": "summary.csv", "histogram": "histogram.png"})
    update_metadata(run_dir, register)

    print(f"\n{args.experiment} / Run{run_number:03d}")
    print(f"Únicas: {len(unique)}/{expected} | Perda: {summary['loss_pct']:.3f}% | Duplicados: {duplicates}")
    print(f"Mín: {summary['min_ms']:.6f} ms | Média: {summary['mean_ms']:.6f} ms")
    print(f"P99: {summary['p99_ms']:.6f} ms | Máx: {summary['max_ms']:.6f} ms")
    print(f"Jitter médio absoluto: {jitter:.6f} ms")
    print(f"Resultados: {run_dir}")


if __name__ == "__main__":
    main()
