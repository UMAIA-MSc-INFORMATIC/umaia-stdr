# Experimentos

Este documento descreve o procedimento experimental utilizado para avaliar o comportamento temporal de uma comunicação MQTT local, implementada com um broker Mosquitto e dois processos Python baseados na biblioteca Paho MQTT: um publicador e um subscritor. O publicador envia 1000 mensagens, cada uma identificada por um número de sequência e pela respetiva marca temporal de envio. O subscritor regista a marca temporal de receção e calcula a latência de cada mensagem pela diferença entre os dois instantes.

O estudo combina duas variáveis independentes: o nível de qualidade de serviço MQTT, com QoS 0 e QoS 1, e o estado de carga do computador, sem carga artificial e com carga artificial de CPU. Da combinação destes fatores resultam quatro experiências distintas. Em todas as experiências são mantidos constantes o broker, a máquina, o tópico MQTT, o período de publicação, o número de mensagens e, tanto quanto possível, as restantes condições de execução.

Cada experiência deve ser repetida cinco vezes. Cada repetição cria automaticamente uma pasta independente com a estrutura `Experiments\<experimentName>\RunNNN\`, contendo os dados em JSONL, os metadados da execução, o resumo estatístico e o histograma das latências. Esta separação evita a mistura de observações pertencentes a condições ou repetições diferentes e permite preservar a rastreabilidade dos resultados.

Antes da recolha oficial deve ser realizada pelo menos uma execução de aquecimento, não incluída nos resultados. O aquecimento permite validar o broker, os scripts, as dependências Python, a criação das pastas e a comunicação entre publicador e subscritor. Durante as medições oficiais, devem ser evitadas alterações desnecessárias no ambiente, como atualizações do sistema, transferências, aplicações adicionais ou mudanças no plano de energia.

A análise de cada execução produz o mínimo, a média, o percentil 99, o máximo observado e o jitter da latência. Neste trabalho, o jitter é definido como a média das diferenças absolutas entre latências consecutivas:

\[
J = \frac{1}{N-1}\sum_{i=2}^{N}|L_i-L_{i-1}|
\]

O valor máximo deve ser apresentado como **máximo observado**, e não como pior caso absoluto, uma vez que a medição experimental de 1000 mensagens não constitui uma demonstração formal do pior tempo possível. Além das métricas solicitadas, devem ser verificados o número de mensagens perdidas e a existência de duplicados, sobretudo nas execuções com QoS 1.

## Experimento 1

### QoS 0 sem carga artificial
ExperimentName = "exp1_qos0_sem_carga"

### Metodologia utilizada

O Experimento 1 estabelece a condição de referência do estudo. O objetivo é medir o comportamento temporal da comunicação MQTT local com QoS 0, sem introdução deliberada de carga computacional. Nesta condição, o MQTT fornece entrega no modo *at most once*, sem confirmação ao nível do protocolo. Espera-se, por isso, menor sobrecarga de comunicação, embora não exista garantia de retransmissão caso uma mensagem não seja entregue.

Devem ser realizadas cinco repetições independentes, cada uma com 1000 mensagens e período de publicação de 10 ms. O computador deve permanecer sem carga artificial e com o menor número possível de aplicações adicionais em funcionamento. O `load_generator.py` não deve ser executado nesta experiência.

A sequência de execução em cada repetição é a seguinte:

1. Iniciar o subscritor e aguardar a confirmação de que a subscrição está ativa.
2. Iniciar o publicador num terminal separado.
3. Aguardar a conclusão do publicador e do subscritor.
4. Executar a análise da repetição concluída.
5. Repetir o processo até existirem cinco pastas `RunNNN` completas.

Nome da experiência utilizado nos comandos: `exp1_qos0_sem_carga`.

### Comandos para execução

**Terminal Subscriber**

```cmd
python subscriber.py --experiment exp1_qos0_sem_carga --qos 0 --count 1000
```

Aguardar a mensagem que confirma que a subscrição está ativa.

**Terminal Loader**

Não executar `load_generator.py` nesta experiência. O objetivo é preservar a condição sem carga artificial.

**Terminal Publisher**

```cmd
python publisher.py --experiment exp1_qos0_sem_carga --qos 0 --count 1000 --period-ms 10
```

**Terminal Analyzer**

Executar apenas depois de o publicador e o subscritor terminarem:

```cmd
python analyse.py --experiment exp1_qos0_sem_carga
```

Para analisar explicitamente uma repetição, substituir `<N>` pelo número da execução, sem os zeros do nome da pasta. Por exemplo, `Run000` corresponde a `--run 0`:

```cmd
python analyse.py --experiment exp1_qos0_sem_carga --run <N>
```

Repetir a sequência completa cinco vezes. O subscritor criará automaticamente `Run000`, `Run001`, `Run002`, `Run003` e `Run004`, desde que não existam execuções anteriores com o mesmo nome.

### Dados Observados

exp1_qos0_sem_carga / Run000
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.342400 ms | Média: 9.369717 ms
P99: 70.921531 ms | Máx: 100.560200 ms
Jitter médio absoluto: 3.725523 ms
Resultados: Experiments\exp1_qos0_sem_carga\Run000

exp1_qos0_sem_carga / Run001
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.353700 ms | Média: 12.378505 ms
P99: 105.033961 ms | Máx: 128.321400 ms
Jitter médio absoluto: 4.831653 ms
Resultados: Experiments\exp1_qos0_sem_carga\Run001

exp1_qos0_sem_carga / Run002
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.350200 ms | Média: 15.479155 ms
P99: 92.978533 ms | Máx: 108.887000 ms
Jitter médio absoluto: 5.719985 ms
Resultados: Experiments\exp1_qos0_sem_carga\Run002

exp1_qos0_sem_carga / Run003
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.340100 ms | Média: 17.166490 ms
P99: 98.040295 ms | Máx: 121.867500 ms
Jitter médio absoluto: 5.609917 ms
Resultados: Experiments\exp1_qos0_sem_carga\Run003

exp1_qos0_sem_carga / Run004
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.344700 ms | Média: 23.663184 ms
P99: 220.286875 ms | Máx: 246.629300 ms
Jitter médio absoluto: 5.058067 ms
Resultados: Experiments\exp1_qos0_sem_carga\Run004

## Experimento 2

### QoS 0 com carga artificial
ExperimentName = "exp2_qos0_com_carga"

### Metodologia utilizada

O Experimento 2 avalia o impacto da contenção de CPU sobre a comunicação MQTT com QoS 0. A configuração MQTT é igual à do Experimento 1, mas é introduzida carga computacional por meio de processos independentes. A comparação direta entre os Experimentos 1 e 2 permite isolar o efeito da carga artificial, mantendo constante o nível de QoS.

Devem ser realizadas cinco repetições independentes, com 1000 mensagens e período de 10 ms. Para garantir que a carga cobre toda a janela de publicação, o gerador deve funcionar durante 20 segundos, enquanto a publicação de 1000 mensagens a cada 10 ms dura aproximadamente 10 segundos, acrescida do tempo de preparação. A carga deve ser iniciada depois de o subscritor ficar ativo e imediatamente antes do publicador.

O número de `workers` deve permanecer constante nas cinco repetições e ser registado no relatório. O valor inicial sugerido é `6`, mas deve ser ajustado antes das execuções oficiais caso não produza carga suficientemente visível no Gestor de Tarefas. Depois de definido, não deve ser alterado entre repetições. O ciclo de atividade deve permanecer em 100%.

A sequência de execução em cada repetição é a seguinte:

1. Iniciar o subscritor e aguardar a confirmação da subscrição.
2. Iniciar o gerador de carga.
3. Iniciar imediatamente o publicador num terceiro terminal.
4. Aguardar a conclusão dos três processos.
5. Executar a análise.

Nome da experiência utilizado nos comandos: `exp2_qos0_com_carga`.

### Comandos para execução

**Terminal Subscriber**

```cmd
python subscriber.py --experiment exp2_qos0_com_carga --qos 0 --count 1000
```

**Terminal Loader**

Executar depois de o subscritor indicar que a subscrição está ativa:

```cmd
python load_generator.py --experiment exp2_qos0_com_carga --duration 20 --workers 6 --duty-cycle 100
```

**Terminal Publisher**

Executar imediatamente após o início do Loader:

```cmd
python publisher.py --experiment exp2_qos0_com_carga --qos 0 --count 1000 --period-ms 10
```

**Terminal Analyzer**

```cmd
python analyse.py --experiment exp2_qos0_com_carga
```

Para selecionar uma repetição específica:

```cmd
python analyse.py --experiment exp2_qos0_com_carga --run <N>
```

Repetir a sequência completa cinco vezes, sem alterar `--workers`, `--duty-cycle`, `--duration`, QoS ou período de publicação.

### Dados observados

exp2_qos0_com_carga / Run000
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.353700 ms | Média: 38.833393 ms
P99: 210.553945 ms | Máx: 225.422700 ms
Jitter médio absoluto: 5.228346 ms
Resultados: Experiments\exp2_qos0_com_carga\Run000

exp2_qos0_com_carga / Run001
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.337300 ms | Média: 12.045507 ms
P99: 119.103427 ms | Máx: 150.576600 ms
Jitter médio absoluto: 3.244153 ms
Resultados: Experiments\exp2_qos0_com_carga\Run001

exp2_qos0_com_carga / Run002
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.379600 ms | Média: 65.545994 ms
P99: 296.713517 ms | Máx: 332.995600 ms
Jitter médio absoluto: 5.778279 ms
Resultados: Experiments\exp2_qos0_com_carga\Run002

exp2_qos0_com_carga / Run003
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.332200 ms | Média: 76.317494 ms
P99: 456.953042 ms | Máx: 524.014500 ms
Jitter médio absoluto: 4.694121 ms
Resultados: Experiments\exp2_qos0_com_carga\Run003

exp2_qos0_com_carga / Run004
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.361900 ms | Média: 33.656662 ms
P99: 193.480042 ms | Máx: 204.052800 ms
Jitter médio absoluto: 4.338871 ms
Resultados: Experiments\exp2_qos0_com_carga\Run004

## Experimento 3

### QoS 1 sem carga artificial
ExperimentName = "exp3_qos1_sem_carga"

### Metodologia utilizada

O Experimento 3 mede o comportamento temporal da comunicação local com QoS 1 e sem carga artificial. Com QoS 1, a entrega segue o modelo *at least once*: o envio exige confirmação por `PUBACK` e uma mensagem pode, em determinadas circunstâncias, ser entregue mais de uma vez. O número de sequência permite distinguir mensagens únicas de eventuais duplicados.

A comparação direta entre os Experimentos 1 e 3 permite avaliar o efeito do nível de QoS em condições sem carga. Para que esta comparação seja válida, devem manter-se o mesmo número de mensagens, o período de publicação, o tópico, o broker e as condições gerais do computador.

Devem ser realizadas cinco repetições independentes, cada uma com 1000 mensagens e período de 10 ms. O `load_generator.py` não deve ser executado. Tanto o publicador como o subscritor devem ser configurados com QoS 1.

Nome da experiência utilizado nos comandos: `exp3_qos1_sem_carga`.

### Comandos para execução

**Terminal Subscriber**

```cmd
python subscriber.py --experiment exp3_qos1_sem_carga --qos 1 --count 1000
```

**Terminal Loader**

Não executar `load_generator.py` nesta experiência.

**Terminal Publisher**

```cmd
python publisher.py --experiment exp3_qos1_sem_carga --qos 1 --count 1000 --period-ms 10
```

**Terminal Analyzer**

```cmd
python analyse.py --experiment exp3_qos1_sem_carga
```

Para selecionar uma repetição específica:

```cmd
python analyse.py --experiment exp3_qos1_sem_carga --run <N>
```

Repetir a sequência completa cinco vezes. Na interpretação, além das latências, devem ser verificados os campos relativos a perdas e duplicados.

### Dados observados

exp3_qos1_sem_carga / Run000
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.375000 ms | Média: 19.277349 ms
P99: 106.779926 ms | Máx: 135.878000 ms
Jitter médio absoluto: 4.850526 ms
Resultados: Experiments\exp3_qos1_sem_carga\Run000

exp3_qos1_sem_carga / Run001
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.341000 ms | Média: 11.714679 ms
P99: 73.029844 ms | Máx: 87.862600 ms
Jitter médio absoluto: 4.615079 ms
Resultados: Experiments\exp3_qos1_sem_carga\Run001

exp3_qos1_sem_carga / Run002
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.364300 ms | Média: 11.010258 ms
P99: 75.913116 ms | Máx: 124.960600 ms
Jitter médio absoluto: 4.033141 ms
Resultados: Experiments\exp3_qos1_sem_carga\Run002

exp3_qos1_sem_carga / Run003
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.368500 ms | Média: 15.920947 ms
P99: 120.867875 ms | Máx: 148.154600 ms
Jitter médio absoluto: 4.542188 ms
Resultados: Experiments\exp3_qos1_sem_carga\Run003

exp3_qos1_sem_carga / Run004
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.350400 ms | Média: 21.382871 ms
P99: 121.862064 ms | Máx: 148.501100 ms
Jitter médio absoluto: 5.618421 ms
Resultados: Experiments\exp3_qos1_sem_carga\Run004

## Experimento 4

### QoS 1 com carga artificial
ExperimentName = "exp4_qos1_com_carga"

### Metodologia utilizada

O Experimento 4 combina QoS 1 com carga artificial de CPU. Esta é a condição de maior contenção prevista no estudo, pois reúne a necessidade de confirmação das publicações com a competição por recursos computacionais. A comparação entre os Experimentos 3 e 4 permite avaliar o efeito da carga quando se utiliza QoS 1. A comparação entre os Experimentos 2 e 4 permite avaliar o efeito do QoS sob a mesma condição de carga.

Devem ser realizadas cinco repetições independentes, com 1000 mensagens, período de 10 ms e a mesma configuração de carga utilizada no Experimento 2. A alteração do número de processos, do ciclo de atividade ou da duração entre os Experimentos 2 e 4 introduziria uma variável adicional e comprometeria a comparação.

A sequência de execução é igual à do Experimento 2: subscritor, gerador de carga, publicador e, após a recolha, analisador. Tanto o publicador como o subscritor devem utilizar QoS 1.

Nome da experiência utilizado nos comandos: `exp4_qos1_com_carga`.

### Comandos para execução

**Terminal Subscriber**

```cmd
python subscriber.py --experiment exp4_qos1_com_carga --qos 1 --count 1000
```

**Terminal Loader**

```cmd
python load_generator.py --experiment exp4_qos1_com_carga --duration 20 --workers 6 --duty-cycle 100
```

**Terminal Publisher**

Executar imediatamente depois de iniciar o Loader:

```cmd
python publisher.py --experiment exp4_qos1_com_carga --qos 1 --count 1000 --period-ms 10
```

**Terminal Analyzer**

```cmd
python analyse.py --experiment exp4_qos1_com_carga
```

Para selecionar uma repetição específica:

```cmd
python analyse.py --experiment exp4_qos1_com_carga --run <N>
```

Repetir a sequência completa cinco vezes, mantendo exatamente a mesma configuração de carga utilizada no Experimento 2.

### Dados Observados

exp4_qos1_com_carga / Run000
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.379200 ms | Média: 70.190694 ms
P99: 269.247565 ms | Máx: 302.254400 ms
Jitter médio absoluto: 5.970402 ms
Resultados: Experiments\exp4_qos1_com_carga\Run000

exp4_qos1_com_carga / Run001
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.332000 ms | Média: 160.660722 ms
P99: 523.790369 ms | Máx: 553.665400 ms
Jitter médio absoluto: 6.349144 ms
Resultados: Experiments\exp4_qos1_com_carga\Run001

exp4_qos1_com_carga / Run002
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.346400 ms | Média: 60.760691 ms
P99: 348.668764 ms | Máx: 392.397800 ms
Jitter médio absoluto: 5.884177 ms
Resultados: Experiments\exp4_qos1_com_carga\Run002

exp4_qos1_com_carga / Run003
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.334500 ms | Média: 61.806430 ms
P99: 289.988380 ms | Máx: 325.518500 ms
Jitter médio absoluto: 6.157022 ms
Resultados: Experiments\exp4_qos1_com_carga\Run003

exp4_qos1_com_carga / Run004
Únicas: 1000/1000 | Perda: 0.000% | Duplicados: 0
Mín: 0.349000 ms | Média: 84.593498 ms
P99: 285.628343 ms | Máx: 311.341600 ms
Jitter médio absoluto: 6.697078 ms
Resultados: Experiments\exp4_qos1_com_carga\Run004