"""Subscritor MQTT e proprietário do ciclo de vida de cada RunNNN."""

import argparse
import json
import platform
import socket
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from clock_utils import now_ns, clock_metadata

import paho.mqtt.client as mqtt

from experiment_utils import (clear_active_run, create_next_run, set_active_run,
                              update_metadata, utc_now, write_json_atomic)


def argumentos():
    p = argparse.ArgumentParser(description="Cria uma execução e regista latências MQTT em JSONL.")
    p.add_argument("--experiment", required=True, help="Nome da experiência/pasta.")
    p.add_argument("--host", default="localhost", help="Endereço do broker MQTT.")
    p.add_argument("--port", type=int, default=1883, help="Porta TCP do broker.")
    p.add_argument("--topic", default="mestrado/mqtt/latencia", help="Tópico MQTT.")
    p.add_argument("--qos", type=int, choices=(0, 1, 2), default=0, help="QoS pedido na subscrição.")
    p.add_argument("--count", type=int, default=1000, help="Número esperado de mensagens únicas.")
    p.add_argument("--timeout", type=float, default=120.0, help="Timeout após subscrição, em segundos.")
    p.add_argument("--username", default=None, help="Utilizador MQTT, se necessário.")
    p.add_argument("--password", default=None, help="Password MQTT, se necessária.")
    return p.parse_args()


def main():
    args = argumentos()
    if args.count <= 0 or args.timeout <= 0:
        raise SystemExit("--count e --timeout devem ser > 0.")

    run_number, run_dir = create_next_run(args.experiment)
    data_path = run_dir / "data.jsonl"
    client_id = f"subscriber-{args.experiment}-{run_number:03d}-{uuid.uuid4().hex[:6]}"
    metadata = {
        "schema_version": 2,
        "experiment": args.experiment,
        "run": run_number,
        "run_name": run_dir.name,
        "status": "active",
        "created_at_utc": utc_now(),
        "completed_at_utc": None,
        "environment": {
            "hostname": socket.gethostname(),
            "operating_system": platform.platform(),
            "python_version": sys.version.split()[0],
            "paho_mqtt_version": getattr(mqtt, "__version__", "unknown"),
        },
        "mqtt": {
            "host": args.host, "port": args.port, "topic": args.topic,
            "subscriber_qos": args.qos, "publisher_qos": None,
        },
        "measurement": {
            "expected_messages": args.count, "received_unique": 0,
            "duplicate_records": 0, "lost_messages": None,
            "period_ms": None, "subscriber_timeout_s": args.timeout,
        },
        "measurement_clock": clock_metadata(),
        "load": {"enabled": False},
        "files": {"data": "data.jsonl", "summary": None, "histogram": None},
    }
    write_json_atomic(run_dir / "metadata.json", metadata)
    set_active_run(args.experiment, run_number, run_dir)
    print(f"Execução criada: {run_dir}")

    terminou = threading.Event()
    subscrito = threading.Event()
    recebidas = 0
    duplicados = 0
    sequencias = set()
    lock = threading.Lock()
    ficheiro = data_path.open("w", encoding="utf-8", buffering=1)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(f"Falha na ligação MQTT: {reason_code}")
            return
        client.subscribe(args.topic, qos=args.qos)

    def on_subscribe(client, userdata, mid, reason_codes, properties):
        subscrito.set()
        print(f"Subscrição ativa em {args.topic}, QoS {args.qos}.")
        print("Agora inicie load_generator.py (se aplicável) e publisher.py.")

    def on_message(client, userdata, msg):
        nonlocal recebidas, duplicados
        recebido_ns = now_ns()
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if payload.get("experiment") != args.experiment or int(payload.get("run", -1)) != run_number:
                return
            seq = int(payload["sequence"])
            envio_ns = int(payload["sent_ns"])
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as erro:
            print(f"Mensagem inválida ignorada: {erro}")
            return

        registo = {
            **payload,
            "received_ns": recebido_ns,
            "latency_ns": recebido_ns - envio_ns,
            "latency_ms": (recebido_ns - envio_ns) / 1_000_000,
            "topic": msg.topic, "qos_received": msg.qos, "mqtt_duplicate_flag": bool(msg.dup),
        }
        with lock:
            ficheiro.write(json.dumps(registo, ensure_ascii=False) + "\n")
            if seq in sequencias:
                duplicados += 1
            else:
                sequencias.add(seq)
                recebidas += 1
            if recebidas % 100 == 0 or recebidas == args.count:
                print(f"Sequências únicas recebidas: {recebidas}/{args.count}")
            if recebidas >= args.count:
                terminou.set()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id,
                         protocol=mqtt.MQTTv311)
    client.on_connect, client.on_subscribe, client.on_message = on_connect, on_subscribe, on_message
    if args.username:
        client.username_pw_set(args.username, args.password)

    status = "failed"
    try:
        client.connect(args.host, args.port, keepalive=60)
        client.loop_start()
        if not subscrito.wait(timeout=10):
            raise TimeoutError("A subscrição não ficou ativa dentro de 10 segundos.")
        completo = terminou.wait(timeout=args.timeout)
        status = "completed" if completo else "timeout"
    except KeyboardInterrupt:
        status = "cancelled"
        print("Execução interrompida pelo utilizador.")
    except Exception as erro:
        status = "failed"
        print(f"Erro: {erro}")
    finally:
        try:
            client.disconnect(); client.loop_stop()
        except Exception:
            pass
        ficheiro.close()
        def finish(m):
            measurement = m.setdefault("measurement", {})
            measurement["received_unique"] = recebidas
            measurement["duplicate_records"] = duplicados
            measurement["lost_messages"] = max(0, args.count - recebidas)
            m["status"] = status
            m["completed_at_utc"] = utc_now()
        update_metadata(run_dir, finish)
        clear_active_run(args.experiment, run_number)

    print(f"Estado: {status}. Dados: {data_path}")
    if status != "completed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
