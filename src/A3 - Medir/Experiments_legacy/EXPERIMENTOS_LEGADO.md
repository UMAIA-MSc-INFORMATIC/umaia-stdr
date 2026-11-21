# Experimentos legados

## Objetivo deste registo

Este documento regista uma primeira campanha de medições MQTT que foi posteriormente **rejeitada para a análise final**. Os dados não foram eliminados, pois continuam úteis para documentar a evolução da metodologia, mas não devem ser utilizados para sustentar as conclusões quantitativas finais sobre latência ou jitter.

A rejeição ocorreu após ser identificada uma limitação na fonte temporal utilizada para calcular a latência. O problema não estava relacionado com o funcionamento do Mosquitto, com a receção das mensagens ou com a estrutura dos experimentos, mas com a capacidade do relógio utilizado em Python para distinguir intervalos temporais pequenos no ambiente Windows em que as medições foram executadas.

## Configuração da campanha original

A campanha original avaliou quatro condições:

| Experimento | QoS | Carga artificial |
|---|---:|---|
| Experimento 1 | 0 | Sem carga |
| Experimento 2 | 0 | 6 workers, 100% duty cycle |
| Experimento 3 | 1 | Sem carga |
| Experimento 4 | 1 | 6 workers, 100% duty cycle |

Nas condições com carga, a utilização observada da CPU situou-se aproximadamente entre **85% e 89%**. Cada condição foi repetida cinco vezes, com 1000 mensagens por execução e período nominal de publicação de 10 ms.

O procedimento experimental, a separação das Runs e a recolha dos dados funcionaram como esperado. O problema foi identificado especificamente na forma como eram produzidas as marcas temporais de envio e receção.

## Método de medição utilizado originalmente

No publicador, o instante de envio era registado através de:

```python
sent_ns = time.time_ns()
```

O valor era incluído na mensagem MQTT. No subscritor, o instante de receção era obtido através da mesma função:

```python
received_ns = time.time_ns()
```

A latência era então calculada por:

```python
latency_ns = received_ns - sent_ns
```

ou, conceptualmente:

\[
L_i = T_{receção,i} - T_{envio,i}
\]

A utilização de `time.time_ns()` sugeria inicialmente uma representação suficientemente fina para o experimento, porque o valor devolvido é expresso em nanossegundos. Contudo, **a unidade utilizada para representar um timestamp não corresponde necessariamente à resolução efetiva da fonte temporal subjacente**.

## Identificação do problema

Durante a análise agregada foi observado que uma percentagem elevada das mensagens apresentava latência calculada exatamente igual a zero.

| Condição | Latências iguais a zero | Percentagem |
|---|---:|---:|
| QoS 0, sem carga | 1283 / 5000 | 25,66% |
| QoS 0, com carga | 361 / 5000 | 7,22% |
| QoS 1, sem carga | 2043 / 5000 | 40,86% |
| QoS 1, com carga | 227 / 5000 | 4,54% |

A quantidade de valores nulos, principalmente nas condições sem carga, era demasiado elevada para ser tratada como um conjunto reduzido de observações ocasionais.

Uma latência calculada igual a zero não significa que a mensagem tenha atravessado instantaneamente o caminho composto pelo cliente Python, biblioteca Paho MQTT, broker Mosquitto e subscritor. Significa que as duas leituras temporais utilizadas na subtração não foram distinguidas pela fonte temporal usada na medição.

## Verificação da resolução temporal

A fonte temporal foi posteriormente inspecionada diretamente no mesmo ambiente Python utilizado nos experimentos:

```cmd
python -c "import time; print(time.get_clock_info('time'))"
```

O resultado obtido foi:

```text
namespace(implementation='GetSystemTimeAsFileTime()', monotonic=False, adjustable=True, resolution=0.015625)
```

Assim, o relógio associado a `time` apresentava uma resolução reportada de:

\[
0,015625\ s = 15,625\ ms
\]

Foi também verificado o relógio de alta resolução disponível através de `perf_counter`:

```cmd
python -c "import time; print(time.get_clock_info('perf_counter'))"
```

Resultado:

```text
namespace(implementation='QueryPerformanceCounter()', monotonic=True, adjustable=False, resolution=1e-07)
```

Neste caso, a resolução reportada corresponde a:

\[
10^{-7}\ s = 0,0001\ ms = 100\ ns
\]

A diferença entre as duas fontes temporais é, portanto, significativa para um estudo cujo objetivo é precisamente observar latências e jitter em comunicação local.

## Relação entre a resolução e as latências iguais a zero

A resolução de 15,625 ms explica por que duas chamadas distintas a `time.time_ns()` podem produzir marcas temporais que, para efeitos da medição, não permitem distinguir um intervalo suficientemente curto.

De forma simplificada:

```text
Publicador                         Subscritor
    |                                  |
    | sent_ns = X                      |
    | -------- mensagem MQTT --------> |
    |                                  | received_ns = X
    |                                  |
                     Latência = X - X = 0
```

O valor zero representa, neste contexto, uma **limitação de observação** e não uma latência física nula.

O padrão encontrado nos dados é coerente com esta explicação. As condições sem carga, nas quais se esperavam comunicações mais rápidas, apresentaram uma proporção muito superior de latências iguais a zero. Sob carga, as latências aumentaram e uma maior proporção das mensagens passou a produzir diferenças distinguíveis pelo relógio.

## Impacto sobre os resultados

A limitação não afeta todas as métricas da mesma forma.

O **mínimo** é diretamente comprometido, uma vez que todas as condições apresentaram valores iguais a zero. As regiões iniciais dos histogramas também ficam quantizadas pela resolução do mecanismo de temporização.

A **média, mediana e jitter** podem igualmente ser influenciados, porque uma fração relevante das observações foi registada como zero, principalmente nas condições sem carga. O problema é particularmente importante para o jitter, pois a métrica depende diretamente das diferenças entre latências consecutivas.

Valores elevados de P99 e máximo observado encontram-se muito acima da resolução de 15,625 ms e, por isso, continuam a indicar que existiram episódios de elevada latência. No entanto, o objetivo do trabalho é comparar de forma consistente toda a distribuição temporal entre condições. Manter apenas as métricas consideradas menos afetadas produziria um conjunto metodologicamente heterogéneo.

Por esta razão, decidiu-se **não utilizar a campanha original para as conclusões quantitativas finais**.

## Por que os dados não foram simplesmente corrigidos

Os valores iguais a zero não foram removidos nem substituídos por valores estimados. Qualquer uma dessas opções introduziria informação que não foi efetivamente medida.

Por exemplo, remover todas as latências iguais a zero aumentaria artificialmente a média e alteraria os histogramas. Substituir `0` por um valor arbitrário, como `0,001 ms` ou metade da resolução conhecida, também criaria observações sintéticas sem suporte experimental.

Da mesma forma, não é possível reconstruir retroativamente as latências reais a partir dos timestamps existentes. Quando `sent_ns` e `received_ns` apresentam o mesmo instante observável, a informação necessária para determinar a diferença real já não está presente nos dados gravados.

A decisão metodologicamente mais conservadora foi, portanto, preservar os dados originais como **legado**, corrigir a estratégia de aquisição temporal e repetir as medições.

## Decisão experimental

A campanha original foi classificada como **experimento legado** e excluída da análise final pelos seguintes motivos:

1. a variável principal do estudo é a latência temporal;
2. a fonte temporal usada apresentava resolução de 15,625 ms no ambiente experimental;
3. foram observadas percentagens elevadas de latências calculadas exatamente iguais a zero, atingindo 40,86% numa das condições;
4. mínimo, média, mediana, jitter e forma das distribuições podem ser afetados pela resolução insuficiente;
5. os dados existentes não permitem reconstruir retroativamente os intervalos reais;
6. existe no mesmo ambiente uma fonte temporal de resolução substancialmente superior, baseada em `QueryPerformanceCounter`, permitindo melhorar a metodologia e repetir a experiência.

A rejeição destes dados não significa que a primeira campanha não tenha produzido informação útil. A campanha permitiu validar a arquitetura experimental, identificar uma limitação de instrumentação e melhorar o desenho da medição antes da elaboração das conclusões finais.

## Critério para a nova campanha

A nova campanha deverá preservar o desenho experimental original sempre que possível:

- quatro condições resultantes da combinação entre QoS 0/QoS 1 e ausência/presença de carga;
- cinco Runs independentes por condição;
- 1000 mensagens por Run;
- período nominal de 10 ms;
- 6 workers e 100% de duty cycle nas condições sob carga;
- mesma máquina, broker Mosquitto e implementação Python/Paho MQTT.

A alteração central deverá estar no mecanismo de aquisição temporal, utilizando uma fonte de alta resolução adequada à medição de intervalos curtos. Antes das 20 execuções oficiais, a nova implementação deverá ser validada através de uma execução de aquecimento, verificando-se explicitamente a ausência do padrão sistemático de timestamps indistinguíveis observado na campanha legada.

## Conclusão

Os dados da primeira campanha foram rejeitados porque a instrumentação temporal não apresentava resolução suficiente para caracterizar com confiança as latências mais curtas observadas no ambiente local. A função `time.time_ns()` fornecia timestamps representados em nanossegundos, mas o relógio `time` utilizado nesse ambiente Windows reportava uma resolução efetiva de 15,625 ms. A existência de 1283, 361, 2043 e 227 latências iguais a zero nas quatro condições, respetivamente, tornou esta limitação material para a análise.

Em vez de eliminar ou ajustar seletivamente essas observações, optou-se por preservar integralmente a campanha como registo legado e repetir o estudo com uma estratégia de temporização de maior resolução. Esta decisão mantém a rastreabilidade do processo e evita sustentar conclusões quantitativas em medições cuja precisão é insuficiente para parte relevante da distribuição observada.

# Analises de latencia = 0 no experimento 
python -c "import json,glob,collections,os; c=collections.Counter(); [(c.update([os.path.basename(os.path.dirname(os.path.dirname(f)))]) if json.loads(l)['latency_ns']==0 else None) for f in glob.glob(r'Experiments\exp*\Run*\data.jsonl') for l in open(f,encoding='utf-8')]; print(*c.items(),sep='\n')"
('exp1_qos0_sem_carga', 1283)
('exp2_qos0_com_carga', 361)
('exp3_qos1_sem_carga', 2043)
('exp4_qos1_com_carga', 227)

python -c "import time; print(time.get_clock_info('time'))"
namespace(implementation='GetSystemTimeAsFileTime()', monotonic=False, adjustable=True, resolution=0.015625)

python -c "import time; print(time.get_clock_info('perf_counter'))"
namespace(implementation='QueryPerformanceCounter()', monotonic=True, adjustable=False, resolution=1e-07)