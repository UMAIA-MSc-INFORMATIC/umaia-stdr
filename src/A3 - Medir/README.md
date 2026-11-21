# MQTT Experiment v2

## Estrutura automática

```text
Experiments/<experiment>/Run000/
  data.jsonl
  metadata.json
  summary.csv
  histogram.png
```

O `subscriber.py` cria a nova Run e deve ser iniciado primeiro. `publisher.py` e `load_generator.py` associam-se à Run ativa. `analyse.py` usa a Run mais recente com dados ou `--run N`.

## Warm-up

Terminal 1:
```cmd
python subscriber.py --experiment warmup --qos 0 --count 10
```

Terminal 2, opcionalmente:
```cmd
python load_generator.py --experiment warmup --duration 15 --workers 2 --duty-cycle 50
```

Terminal 3:
```cmd
python publisher.py --experiment warmup --qos 0 --count 10 --period-ms 10
```

Após o subscritor terminar, Terminal 4:
```cmd
python analyse.py --experiment warmup
```

Uma nova repetição com o mesmo nome cria automaticamente `Run001`, depois `Run002`, etc.
