"""Funções partilhadas para organizar e documentar execuções experimentais."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BASE_DIR = Path("Experiments")
RUN_PATTERN = re.compile(r"^Run(\d{3})$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_experiment_name(name: str) -> str:
    # Evita nomes que escapem da pasta Experiments ou sejam inválidos no Windows.
    if not name or name in {".", ".."}:
        raise ValueError("O nome da experiência não pode estar vazio.")
    if any(c in name for c in '<>:"/\\|?*') or name.endswith((".", " ")):
        raise ValueError("Nome de experiência inválido para uma pasta Windows.")
    return name


def experiment_dir(name: str) -> Path:
    return BASE_DIR / validate_experiment_name(name)


def create_next_run(experiment: str) -> tuple[int, Path]:
    """Cria atomicamente o primeiro RunNNN disponível."""
    root = experiment_dir(experiment)
    root.mkdir(parents=True, exist_ok=True)
    existing = []
    for item in root.iterdir():
        match = RUN_PATTERN.match(item.name) if item.is_dir() else None
        if match:
            existing.append(int(match.group(1)))
    candidate = max(existing, default=-1) + 1
    while candidate <= 999:
        run_dir = root / f"Run{candidate:03d}"
        try:
            run_dir.mkdir()
            return candidate, run_dir
        except FileExistsError:
            candidate += 1
    raise RuntimeError("Foi atingido o limite Run999 para esta experiência.")


def active_pointer(experiment: str) -> Path:
    return experiment_dir(experiment) / ".active_run.json"


def set_active_run(experiment: str, run_number: int, run_dir: Path) -> None:
    write_json_atomic(active_pointer(experiment), {
        "experiment": experiment,
        "run": run_number,
        "run_directory": run_dir.name,
        "activated_at_utc": utc_now(),
    })


def clear_active_run(experiment: str, run_number: int) -> None:
    pointer = active_pointer(experiment)
    if not pointer.exists():
        return
    try:
        data = read_json(pointer)
        if int(data.get("run", -1)) == run_number:
            pointer.unlink(missing_ok=True)
    except (OSError, ValueError, json.JSONDecodeError):
        pass


def get_active_run(experiment: str) -> tuple[int, Path]:
    pointer = active_pointer(experiment)
    if not pointer.exists():
        raise RuntimeError(
            f"Não existe uma execução ativa para '{experiment}'. "
            "Inicie primeiro subscriber.py."
        )
    data = read_json(pointer)
    run_number = int(data["run"])
    run_dir = experiment_dir(experiment) / str(data["run_directory"])
    if not run_dir.is_dir():
        raise RuntimeError(f"A pasta da execução ativa não existe: {run_dir}")
    metadata = read_json(run_dir / "metadata.json")
    if metadata.get("status") != "active":
        raise RuntimeError("A execução indicada já não está ativa. Inicie novamente subscriber.py.")
    return run_number, run_dir


def resolve_run(experiment: str, run_number: int | None = None) -> tuple[int, Path]:
    root = experiment_dir(experiment)
    if run_number is not None:
        run_dir = root / f"Run{run_number:03d}"
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Execução não encontrada: {run_dir}")
        return run_number, run_dir

    candidates = []
    if root.exists():
        for item in root.iterdir():
            match = RUN_PATTERN.match(item.name) if item.is_dir() else None
            if match and (item / "data.jsonl").exists():
                candidates.append((int(match.group(1)), item))
    if not candidates:
        raise FileNotFoundError(f"Nenhuma execução com dados encontrada para '{experiment}'.")
    return max(candidates, key=lambda x: x[0])


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def _acquire_lock(lock_path: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timeout ao bloquear {lock_path}")
            time.sleep(0.02)


def update_metadata(run_dir: Path, updater: Callable[[dict[str, Any]], None]) -> None:
    """Atualiza metadata.json com bloqueio entre processos e escrita atómica."""
    metadata_path = run_dir / "metadata.json"
    lock_path = run_dir / ".metadata.lock"
    _acquire_lock(lock_path)
    try:
        data = read_json(metadata_path) if metadata_path.exists() else {}
        updater(data)
        data["metadata_updated_at_utc"] = utc_now()
        write_json_atomic(metadata_path, data)
    finally:
        lock_path.unlink(missing_ok=True)
