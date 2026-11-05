# Configuração, processamento e validação

## Configuração entregue

| Item | Valor no código |
|---|---|
| Alvo | STM32F103RBT6, Cortex-M3, soft-float, 128 KiB de Flash / 20 KiB de SRAM |
| Clock | HSI/2 × PLL16: 64 MHz nominais; APB1 a 32 MHz |
| I²C2 | PB10/PB11, 100 kHz, endereço de 7 bits 0x1D, SA0/PB12 alto |
| Sensor | MMA8452Q, ±2 g, 12 bits, 1024 contagens/g, ODR nominal de 50 Hz |
| SPI1 | PA5/PA7, modo 0, MSB primeiro, 8 bits, 4 MHz nominais |
| USART2 | PA2/TX e PA3/RX, 115200 baud, 8N1, transmissão por interrupção |
| Temporização | Consulta alvo de 20 ms; pedido de UI de 100 ms; debounce de 25 ms |
| Filtro | Média exponencial por componente, α = 0,18 |
| Validade | Norma da aceleração de entrada entre 0,75 g e 1,25 g |
| Dados antigos | Limite configurado de 200 ms, verificado pelo ciclo cooperativo |
| Recuperação | Nova tentativa do sensor após cerca de 1 s; TFT após cerca de 3 s |

São valores configurados. A taxa efetiva de leituras válidas, a atualização visual e a latência precisam de medição. As transações bloqueantes e a reinicialização do TFT podem atrasar o ciclo principal.

## Processamento

Os seis bytes do sensor são convertidos em três amostras assinadas de 12 bits. O código reconstrói `n = (MSB << 4) | (LSB >> 4)` e subtrai 4096 quando o bit de sinal está ativo. Em ±2 g, divide por 1024 para obter g.

Cada componente é filtrada por `a_f = a_f + α × (a − a_f)`. A primeira amostra inicializa o filtro. Diminuir α aumenta a suavização e o atraso de resposta.

As componentes filtradas originam duas inclinações em graus:

```text
X = atan2(ax, sqrt(ay² + az²)) × 180/π
Y = atan2(ay, sqrt(ax² + az²)) × 180/π
```

A estimativa usa a gravidade perto do repouso. Não fornece orientação completa em 3D nem yaw. O teste da norma rejeita algumas condições inadequadas, mas não garante ausência de aceleração dinâmica.

ZERO guarda os ângulos atuais e a apresentação subtrai essa referência. HOLD mantém os valores apresentados sem parar a aquisição ou o CSV. Uma falha ou leitura inválida sobrepõe o aviso aos valores da UI. A tolerância define um critério de nivelamento e não a exatidão do sensor.

## Estado dos ensaios

| Verificação | Resultado disponível | Alcance da evidência |
|---|---|---|
| Compilação Cortex-M3 Debug/Release | Relatórios anteriores em `evidencias/` | Construção e ligação do executável, sem provar execução física. |
| Lógica, formatação, botões e desenho no PC | Testes existentes passaram na revisão final | Entradas simuladas e saída TFT substituída por memória. |
| Metadados CubeIDE | Dois testes passaram na revisão final | Estrutura de Debug/Release, builder e UTF-8; não substitui abrir o IDE. |
| Execução na placa | Relatada pelo grupo no slide 8 | Teste funcional; condições detalhadas não disponibilizadas. |
| Informação no TFT | Relatada pelo grupo no slide 8 | Apresentação funcional; a imagem do slide 6 continua a ser uma simulação. |
| Botões e modos | Relatados pelo grupo no slide 8 | Resposta funcional; não há registo individual de cada pressão. |
| Registo série real e análise angular | Não disponibilizados | Sem valores medidos de erro, repetibilidade ou resposta. |

Fonte dos ensaios físicos: [apresentação do grupo](Nivel_Digital_SISEM.pptx), incluindo notas. A revisão final não repetiu os testes na placa. Os relatórios antigos mantêm a sua data e o seu âmbito; não foram reclassificados como ensaios físicos.

## Compilar e executar os testes

Seguir as [instruções Linux/CubeIDE](08-linux-cubeide.md). Para o alvo, usar o toolchain Arm GNU com newlib ou o compilador do CubeIDE. Para os testes no PC, executar `python3 tools/run_tests.py` com GCC nativo e Python 3.12 ou posterior.

O projeto tem configuração HAL em C, sem `.ioc` gerado/validado. As variáveis de diagnóstico são `prumo_debug`, `prumo_level` e `fatal_code`. A compilação independente anterior registou 19 820 bytes de Flash em Debug, 17 668 em Release e 5248 bytes de RAM reservada, incluindo 2048 bytes de reserva mínima de stack. O mapa não mede o pico real da stack.

## Telemetria e resultados

```text
t_ms,sample_ms,seq,ax_mg,ay_mg,az_mg,x_cdeg,y_cdeg,zero_x_cdeg,zero_y_cdeg,tol_cdeg,hold,sensor_ok,tilt_valid,i2c_errors,missed_polls,uart_dropped
```

Dividir `mg` por 1000 para obter g e `cdeg` por 100 para obter graus. As acelerações são as amostras originais convertidas. Os ângulos vêm das componentes filtradas, antes do ZERO; o relativo resulta de `x_cdeg − zero_x_cdeg`, e de modo equivalente para Y.

`sample_ms` é o tick associado à última leitura bem-sucedida, e não um timestamp de data-ready do sensor. `t_ms` é o tick usado ao preparar o registo. Verificar `seq`, `sensor_ok` e `tilt_valid`, pois também existem registos de erro sem nova amostra. `missed_polls` conta períodos do agendamento ultrapassados; `uart_dropped` conta tentativas de transmissão descartadas ou falhadas.

## Próxima caracterização experimental

Guardar um CSV real e registar firmware, montagem, duração, número de amostras e referência usada. Comparar vários ângulos conhecidos, repetir posições e calcular erro e dispersão. Para estudar a resposta, aplicar uma mudança de inclinação e medir o tempo de estabilização. Fotografias do ecrã e registos de USART devem acompanhar os ensaios que documentam.

O gráfico do slide 9 é sintético e serve apenas para explicar a suavização. Não permite atribuir ao protótipo uma precisão ou um tempo de resposta medidos.
