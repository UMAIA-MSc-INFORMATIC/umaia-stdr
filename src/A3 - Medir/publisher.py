"""Publicador MQTT que se associa à execução ativa criada pelo subscritor."""

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from clock_utils import now_ns, clock_metadata

import paho.mqtt.client as mqtt

from experiment_utils import get_active_run, update_metadata, utc_now


def argumentos():
    p = argparse.ArgumentParser(description="Publica mensagens na execução ativa.")
    p.add_argument("--experiment", required=True, help="Nome da experiência ativa.")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="mestrado/mqtt/latencia")
    p.add_argument("--qos", type=int, choices=(0, 1, 2), default=0)
    p.add_argument("--count", type=int, default=1000)
    p.add_argument("--period-ms", type=float, default=10.0)
    p.add_argument("--username", default=None)
    p.add_argument("--password", default=None)
    p.add_argument("--connect-timeout", type=float, default=10.0)
    p.add_argument("--ack-timeout", type=float, default=10.0)
    p.add_argument("--start-delay", type=float, default=1.0)
    return p.parse_args()


def main():
    args = argumentos()
    if args.count <= 0 or args.period_ms < 0:
        raise SystemExit("--count deve ser > 0 e --period-ms >= 0.")
    run_number, run_dir = get_active_run(args.experiment)

    def register(m):
        mqtt_data = m.setdefault("mqtt", {})
        mqtt_data.update({"host": args.host, "port": args.port, "topic": args.topic,
                          "publisher_qos": args.qos})
        measurement = m.setdefault("measurement", {})
        measurement.update({"publisher_count": args.count, "period_ms": args.period_ms})
        m["publisher"] = {"started_at_utc": utc_now(), "completed_at_utc": None, "status": "running"}
    update_metadata(run_dir, register)

    ligado = False
    def on_connect(client, userdata, flags, reason_code, properties):
        nonlocal ligado
        ligado = reason_code == 0

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"publisher-{args.experiment}-{run_number:03d}-{uuid.uuid4().hex[:6]}",
                         protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    if args.username:
        client.username_pw_set(args.username, args.password)

    status = "failed"
    sent = 0
    try:
        client.connect(args.host, args.port, keepalive=60)
        client.loop_start()
        deadline = time.monotonic() + args.connect_timeout
        while not ligado and time.monotonic() < deadline:
            time.sleep(0.01)
        if not ligado:
            raise TimeoutError("Não foi possível ligar ao broker.")

        print(f"Associado a {run_dir}. QoS={args.qos}, mensagens={args.count}.")
        time.sleep(max(0.0, args.start_delay))
        period_ns = int(args.period_ms * 1_000_000)
        next_send = time.perf_counter_ns()
        for sequence in range(args.count):
            if period_ns:
                while (remaining := next_send - time.perf_counter_ns()) > 0:
                    time.sleep(remaining / 1_000_000_000)
            sent_ns = now_ns()
            payload = {
                "experiment": args.experiment, "run": run_number, "sequence": sequence,
                "sent_ns": sent_ns,
                "qos_requested": args.qos,
            }
            info = client.publish(args.topic, json.dumps(payload, separators=(",", ":")),
                                  qos=args.qos, retain=False)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Falha ao publicar sequência {sequence}: {info.rc}")
            info.wait_for_publish(timeout=args.ack_timeout)
            if not info.is_published():
                raise TimeoutError(f"Timeout ao publicar sequência {sequence}")
            sent += 1
            next_send += period_ns
            if sent % 100 == 0 or sent == args.count:
                print(f"Publicadas {sent}/{args.count}")
        status = "completed"
    except Exception as erro:
        print(f"Erro no publicador: {erro}")
    finally:
        try:
            client.disconnect(); client.loop_stop()
        except Exception:
            pass
        def finish(m):
            pub = m.setdefault("publisher", {})
            pub.update({"status": status, "sent_messages": sent, "completed_at_utc": utc_now()})
        update_metadata(run_dir, finish)
    print(f"Publicador terminado com estado: {status}")
    if status != "completed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
