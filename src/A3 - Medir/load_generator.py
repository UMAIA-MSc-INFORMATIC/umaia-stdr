"""Gera carga CPU e documenta-a na execução ativa."""

import argparse
import math
import multiprocessing as mp
import os
import time

from experiment_utils import get_active_run, update_metadata, utc_now


def argumentos():
    p = argparse.ArgumentParser(description="Gera carga CPU para a execução ativa.")
    p.add_argument("--experiment", required=True, help="Nome da experiência ativa.")
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--duty-cycle", type=float, default=100.0)
    return p.parse_args()


def worker(end, duty):
    cycle = 0.1
    active = cycle * duty / 100.0
    x = 0.123456789
    while time.perf_counter() < end:
        start = time.perf_counter()
        while time.perf_counter() - start < active and time.perf_counter() < end:
            x = math.sin(x) ** 2 + math.cos(x) ** 2 + 0.0000001
        remaining = cycle - (time.perf_counter() - start)
        if remaining > 0:
            time.sleep(remaining)


def main():
    args = argumentos()
    if args.duration <= 0 or args.workers <= 0 or not 1 <= args.duty_cycle <= 100:
        raise SystemExit("Valores inválidos: duration/workers > 0 e duty-cycle entre 1 e 100.")
    run_number, run_dir = get_active_run(args.experiment)

    def register(m):
        m["load"] = {
            "enabled": True, "status": "running", "workers": args.workers,
            "duty_cycle_pct": args.duty_cycle, "duration_s": args.duration,
            "started_at_utc": utc_now(), "completed_at_utc": None,
        }
    update_metadata(run_dir, register)

    end = time.perf_counter() + args.duration
    processes = [mp.Process(target=worker, args=(end, args.duty_cycle)) for _ in range(args.workers)]
    status = "completed"
    print(f"Carga associada a Run{run_number:03d}: {args.workers} processos, {args.duty_cycle:.0f}%, {args.duration:.1f}s.")
    try:
        for p in processes: p.start()
        for p in processes: p.join()
    except KeyboardInterrupt:
        status = "cancelled"
        for p in processes: p.terminate()
        for p in processes: p.join()
    finally:
        def finish(m):
            load = m.setdefault("load", {})
            load.update({"status": status, "completed_at_utc": utc_now()})
        update_metadata(run_dir, finish)
    print(f"Carga terminada com estado: {status}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
