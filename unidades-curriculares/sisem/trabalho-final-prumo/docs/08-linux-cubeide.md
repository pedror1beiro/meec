# Executar o PRUMO no Linux com STM32CubeIDE

## O que está incluído

- Projeto C/HAL para STM32F103RBT6 com `.project` e `.cproject` do STM32CubeIDE.
- Código da aplicação, drivers MMA8452Q/ST7735, UI, arranque, linker e dependências HAL/CMSIS já incluídas.
- Build independente em Python para verificar o mesmo firmware com Arm GNU GCC.
- Testes da lógica/UI que correm no PC e um utilitário opcional de registo série.

O projeto tem configuração HAL escrita em C. **Não é necessário criar ou gerar um projeto novo no CubeMX para o compilar.** Não é fornecido um `.ioc` validado pelo CubeMX; para alterar pinos e clocks usar `board.c` e `prumo_config.h`. Não regenerar por cima destes ficheiros com um projeto CubeMX diferente.

## 1. Importar no CubeIDE (Eclipse)

1. Descomprimir a entrega numa pasta normal, por exemplo `~/SISEM`.
2. Abrir o STM32CubeIDE, escolhendo um workspace à parte.
3. Selecionar **File > Import > General > Existing Projects into Workspace**.
4. Em **Select root directory**, escolher `SISEM/firmware/PRUMO`.
5. Selecionar o projeto **PRUMO** e concluir. O projeto já tem todos os paths relativos.
6. Selecionar a configuração **Debug** e fazer **Project > Clean** e **Build Project**.
7. O executável será `Debug/PRUMO.elf`. Verificar que a consola usa `-mcpu=cortex-m3`, `-mthumb`, ABI `soft`, `STM32F103xB` e `USE_HAL_DRIVER`.

A importação gráfica e o debug dependem da versão do CubeIDE instalada e ainda não foram ensaiados nesta máquina. Os metadados XML foram verificados; o build independente foi usado para verificar compilação e ligação reais do código para Cortex-M3. Se houver problema de migração de metadados, usar a alternativa de compilação abaixo para produzir o ELF e selecionar esse ELF na configuração de debug do IDE.

## 2. Debug com ST-LINK

1. Ligar o USB do **ST-LINK da NUCLEO**, com a placa de expansão corretamente encaixada e alimentada.
2. Instalar as regras udev fornecidas pelo instalador ST no Linux, caso o ST-LINK não seja acessível. Voltar a ligar o USB após instalar as regras; não é necessário executar todo o IDE como root.
3. Abrir **Run > Debug Configurations** e criar uma configuração **STM32 C/C++ Application**.
4. Projeto: `PRUMO`. Aplicação: `Debug/PRUMO.elf`.
5. Debugger: **ST-LINK (ST-LINK GDB server)**, interface **SWD**. Selecionar o servidor fornecido pelo IDE. Se pedir o dispositivo, escolher STM32F103RBTx.
6. Ativar carregamento do executável e reset; colocar breakpoint em `main`.
7. Iniciar debug e continuar. A inicialização do TFT demora aproximadamente um segundo por causa dos atrasos exigidos no arranque.
8. Observar `prumo_debug`, `prumo_level` e `fatal_code` no debugger.

O debug deve manter SWD: o firmware desativa JTAG para libertar PB4, usado pelo reset do TFT. Para medir a taxa de aquisição, deixar correr sem breakpoints. Pausar o CPU altera os tempos.

## 3. Comportamento previsto

- Clock: HSI/2 × PLL16 = **64 MHz**, sem depender de cristal/MCO externo.
- I²C2: PB10/PB11, 100 kHz; SA0/PB12 alto, endereço 0x1D.
- Sensor: ±2 g, saída de 12 bits, ODR nominal 50 Hz; identificação esperada 0x2A.
- SPI1: PA5/PA7, 4 MHz, escrita de blocos de até 8 linhas.
- USART2: PA2 TX / PA3 RX, 115200 baud, 8N1; VCP do ST-LINK na configuração habitual da NUCLEO.
- Aquisição em polling nominal de 20 ms; UI pedida a cada 100 ms. Estes são alvos de configuração, não frequências físicas medidas.

O renderer envia no máximo 2 KiB por chamada e regressa ao loop para voltar a servir aquisição e botões. Não existe framebuffer completo nem uso de heap na aplicação. A formatação CSV é própria e não usa `printf`/alocação dinâmica. A USART transmite por interrupção; registos que não caibam no tempo disponível são contados em `uart_dropped`.

## 4. Botões

| Botão | Função |
|---|---|
| SW1 | Alternar entre bolha e eixos |
| SW2 | Aumentar tolerância |
| SW3 | HOLD: congelar/descongelar a UI |
| SW4 | Reduzir tolerância |
| SW5 | ZERO: guardar a referência atual e sair de HOLD |
| SW6 | Reset físico do microcontrolador |

ZERO e ativação de HOLD requerem uma leitura válida. A aquisição e o CSV continuam durante HOLD. Se o sensor falhar ou ficar sem dados novos, a UI deve mostrar erro em vez de apresentar uma leitura antiga como atual. Mudança de tolerância e ZERO são voláteis: não são guardados na Flash.

## 5. Se o TFT ficar branco, deslocado ou com cores trocadas

Abrir `Core/Inc/prumo_config.h` e recompilar após cada alteração:

- Para um padrão simples, definir `PRUMO_TFT_TEST_PATTERN` como `1`. Devem aparecer barras vermelha, verde, azul e branca com texto TOP/BOTTOM.
- Para vermelho/azul trocados, experimentar `PRUMO_TFT_MADCTL = 0xC8` em vez de `0xC0`.
- Alguns painéis necessitam de offsets. Começar pelo perfil `0,0`; se necessário testar X=2/Y=1 conforme a variante. Não tratar esse perfil como confirmado para este exemplar.
- Para imagem rodada 180°, experimentar MADCTL 0x00 (ou 0x08 para BGR).
- Se a comunicação parecer instável, reduzir `PRUMO_TFT_SPI_DIV` para `SPI_BAUDRATEPRESCALER_64` (1 MHz). A taxa de atualização visual diminuirá.

Não há MISO do TFT ligado, pelo que uma escrita SPI bem-sucedida só comprova que o periférico transmitiu. Não confirma que o painel recebeu ou mostrou a imagem. A compatibilidade da inicialização com o exemplar físico precisa do primeiro ensaio.

## 6. Se o acelerómetro não responder

- Consultar `prumo_debug.who_am_i`, `last_i2c_status`, `last_i2c_error` e `i2c_errors`.
- Confirmar a placa de expansão, 3,3 V e massa comum; confirmar PB10/PB11 e SA0 alto.
- O firmware tenta recuperar o barramento e reinicializar o sensor após erro. Essa tentativa é limitada e não substitui a verificação elétrica ou a análise de uma condição persistente.
- Se houver resposta mas os sentidos estiverem invertidos, validar fisicamente os eixos e ajustar `PRUMO_AXIS_X_SIGN` / `PRUMO_AXIS_Y_SIGN`.
- A estimativa destina-se a uma superfície aproximadamente horizontal em repouso. As duas inclinações são `atan2(ax,sqrt(ay²+az²))` e `atan2(ay,sqrt(ax²+az²))`, com convenção a confirmar pela montagem. Não é orientação completa em 3D nem mede yaw.
- A verificação de norma 0,75–1,25 g apenas deteta algumas situações de movimento. Não garante ausência de aceleração dinâmica. `MOVIMENTO` pede que a board fique imóvel.

## 7. Registar dados no computador

O CSV tem este cabeçalho:

```text
t_ms,sample_ms,seq,ax_mg,ay_mg,az_mg,x_cdeg,y_cdeg,zero_x_cdeg,zero_y_cdeg,tol_cdeg,hold,sensor_ok,tilt_valid,i2c_errors,missed_polls,uart_dropped
```

- `mg`: dividir por 1000 para obter g; os dados XYZ são as amostras originais convertidas.
- `cdeg`: dividir por 100 para obter graus; X/Y são os ângulos filtrados antes do zero relativo.
- Ângulo relativo: `x_cdeg - zero_x_cdeg` (idem para Y).
- `sample_ms` é o tempo da última amostra real; `t_ms` é o tempo de emissão do registo.
- `hold` afeta só a UI. Validar os dados com `sensor_ok` e `tilt_valid` e não assumir que todos os registos contêm amostras novas (há registos de erro).
- `missed_polls` conta períodos do scheduler perdidos; não é um contador exato de amostras perdidas dentro do sensor.

Logger opcional, a partir da raiz da entrega:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r tools/requirements-logger.txt
python3 tools/log_serial.py --port /dev/ttyACM0 --seconds 30 --output dados/repouso.csv
```

Substituir `/dev/ttyACM0` pela porta real. O logger escreve o cabeçalho, aceita apenas linhas numéricas com o número de colunas esperado e não altera os valores. É preciso ter permissões de acesso à porta; em muitas distribuições isso é gerido pelo grupo `dialout` ou `uucp`. Um terminal série aberto em simultâneo pode impedir o acesso. O logger ainda não foi ensaiado com esta board.

## 8. Compilação alternativa sem importação gráfica

É preciso ter o Arm GNU Toolchain completo com newlib (não basta um compilador C do PC). Pode usar-se o GCC incluído no CubeIDE:

```bash
cd firmware/PRUMO
python3 tools/build.py --toolchain /caminho/real/para/o/bin-do-gcc-arm
```

Ou, se `arm-none-eabi-gcc`, `arm-none-eabi-objcopy` e `arm-none-eabi-size` já estiverem no PATH:

```bash
python3 tools/build.py
python3 tools/build.py --release
```

É usado GNU GCC, C11, Cortex-M3, ABI soft-float, `libm` e newlib-nano. A saída fica em `Debug/` ou `Release/`, com ELF, HEX, BIN, MAP e `build-report.json`. O script recompila todas as fontes para evitar resultados antigos.

O linker script usa o atributo `READONLY` das versões recentes do GNU ld (o build foi verificado com GCC 13.2/binutils 2.41). Preferir um CubeIDE/toolchain recente; um GNU ld antigo que não reconheça `READONLY` exige atualização do toolchain ou adaptação consciente do script.

Os binários compilados neste PC servem de referência. Para depuração com as fontes no Linux, recompilar localmente; assim os caminhos DWARF correspondem ao PC de destino.

## 9. Testes no PC

Com GCC nativo instalado no Linux, a partir da raiz da entrega:

```bash
python3 tools/run_tests.py
```

Estes testes cobrem lógica numérica, formatação limitada, debounce e renderer por blocos. Não simulam eletricamente o I²C/SPI nem verificam o ST-LINK ou o painel.

## Fontes de ferramentas

- [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1/tree/v1.8.7)
- [Manual CubeIDE UM2609](https://www.st.com/resource/en/user_manual/um2609-stm32cubeide-user-manual-stmicroelectronics.pdf)
- [Servidor GDB ST-LINK UM2576](https://www.st.com/resource/en/user_manual/um2576-stm32cubeide-stlink-gdb-server-stmicroelectronics.pdf)
- [pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)
