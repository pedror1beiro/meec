# Hardware e pinagem

Fontes principais: [esquema 3S0 Board 1.2](referencias/sisem.pdf), [datasheet STM32](referencias/STMicroelectronics-STM32F103RBT6-datasheet.pdf), [datasheet MMA8452Q](referencias/I2C_MMA8452Q.pdf).

## Recursos do microcontrolador

STM32F103RBT6: Cortex-M3, até 72 MHz, 128 KiB de Flash e 20 KiB de SRAM. Não tem FPU. Não assumir 72 MHz no código antes de confirmar e configurar o clock da placa principal.

## Acelerómetro — I²C2

| Sinal | GPIO | Configuração inicial |
|---|---|---|
| SCL | PB10 | I2C2_SCL, alternate function open-drain |
| SDA | PB11 | I2C2_SDA, alternate function open-drain |
| SA0 | PB12 | Saída alta ou entrada sem pull-down, mantendo o pull-up externo; endereço de 7 bits 0x1D |
| INT1 | PC8 | Opcional na primeira versão |
| INT2 | PC9 | Opcional na primeira versão |

O esquema já inclui pull-ups de 10 kΩ para SCL, SDA e SA0, alimentação de 3,3 V e condensadores. PB12 baixo seleciona 0x1C. Nas funções HAL I2C que recebem `DevAddress`, usar o endereço de 7 bits deslocado uma posição para a esquerda: `0x1D << 1`.

Primeiro teste: ler `WHO_AM_I`, registo 0x0D, cujo valor esperado é 0x2A. Depois configurar standby, escala ±2 g, ODR de 50 Hz e modo ativo. Em 12 bits e ±2 g, usar 1024 contagens/g; combinar MSB/LSB e fazer corretamente a extensão de sinal. Aceleração em repouso inclui a gravidade.

## TFT — SPI1

Embora o símbolo do ecrã use os nomes SDA e SCL, estas linhas correspondem à interface série SPI do TFT, independente do I²C do acelerómetro.

| Sinal no TFT | GPIO | Função |
|---|---|---|
| SCL | PA5 | SPI1_SCK |
| SDA | PA7 | SPI1_MOSI |
| CS | PA4 | GPIO de seleção, ativo a zero |
| RS | PA8 | GPIO de comando/dados (D/C) |
| RESET | PB4 | GPIO de reset, ativo a zero |
| LEDK via Q1 | PA0 | Controlo da retroiluminação; nível alto liga o MOSFET |

Não há uma linha MISO do TFT neste esquema. A validação inicial deve usar padrões visuais, sem depender de leitura de ID do controlador. A linha PA6 pertence ao cartão SD no esquema; o SD fica desativado na primeira versão. Manter os chip-selects dos outros dispositivos do mesmo SPI em estado inativo, se esses componentes estiverem montados.

**PB4 é partilhado com NJTRST.** Configurar `SYS > Debug = Serial Wire`, mantendo SWD em PA13/PA14 e libertando os pinos de JTAG. Verificar que o código HAL gerado aplica o remapeamento de SWJ para JTAG desativado / SWD ativo.

Painel indicado: JD-T18003-T01, família de controlador ST7735. O desenho do fabricante indica:

- Área ativa: 28,03 × 35,04 mm.
- Resolução: 128 × 160 píxeis, em retrato.
- Contorno do módulo LCD: 34 × 45,83 mm; não confundir com a área ativa nem com a placa de expansão.
- A variante exata e a inicialização devem ser confirmadas por teste; fornecedores também referem ST7735R.

Fonte: [desenho técnico](https://dl.singtown.com/datasheet/JD-T18003-T01.pdf), página 5. A fotografia foi usada para reconhecer orientação e disposição, não como instrumento de medição.

## Botões

| Botão | GPIO | Função proposta |
|---|---|---|
| SW1 | PC13 | Alternar vista |
| SW2 | PC10 | Aumentar tolerância |
| SW3 | PC11 | HOLD |
| SW4 | PC12 | Reduzir tolerância |
| SW5 | PA1 | ZERO relativo |
| SW6 | NRST | Reset físico do MCU |

SW1–SW5: entrada com pull-up; pressionado equivale a nível baixo. O circuito tem RC, mas acrescentar debounce e deteção de uma transição por pressão em software. SW6 não é um GPIO de aplicação e não deve ser tratado como um evento de botão comum.

## USART e debug

- Preferência: USART2, PA2 = TX e PA3 = RX. No esquema P2, PA2 e PA3 estão nos contactos 35 e 37.
- A NUCLEO-F103RB dispõe de ST-LINK e VCP; confirmar a ligação USART2/VCP e as pontes na revisão física utilizada antes do ensaio.
- O manual UM1724 descreve a ligação USART2/VCP por defeito com SB13/SB14 fechadas e SB62/SB63 abertas; verificar o esquema e as pontes da revisão real, sem as alterar por suposição. Fonte: [UM1724, secção USART communication](https://www.st.com.cn/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf).
- Algumas anotações no esquema rotulam PA2/PA3 de forma ambígua. Usar os papéis TX/RX do datasheet do MCU e do esquema da NUCLEO.
- Alternativa USART1 no P7: contacto 3 = PA10/RX, 4 = PA9/TX, 2 = GND, 1 = 3,3 V, 5 = PC4.
- PA9/PA10 também estão ligados ao ESP8266. Não usar essa alternativa sem resolver a partilha elétrica com o módulo.
- SWD: PA13/SWDIO, PA14/SWCLK; usar ST-LINK integrado.

PB6/PB7 estão ligados ao LED RGB; não usar a pinagem genérica de I²C1 sugerida antes de se conhecer o esquema.
