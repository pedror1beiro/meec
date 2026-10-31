# Compilação, debug e validação

Este documento começou como roteiro. Atualização: existe agora código completo em `firmware/PRUMO`, com build independente Debug/Release verificado. As etapas no hardware continuam pendentes. Para o projeto entregue, seguir [instruções Linux/CubeIDE](08-linux-cubeide.md); as tabelas seguintes documentam o planeamento inicial.

## Configuração inicial a gerar no CubeMX

| Item | Configuração proposta |
|---|---|
| MCU | STM32F103RBT6; verificar Flash de 128 KiB e RAM de 20 KiB |
| Projeto | C / HAL / STM32CubeIDE; nome PRUMO |
| SYS Debug | Serial Wire, mantendo SWD e libertando PB4 de JTAG |
| Clock | Começar com HSI interno para bring-up; definir PLL/HSE depois de verificar a placa |
| I2C2 | PB10/PB11, 100 kHz, endereçamento de 7 bits |
| SPI1 | Master, SCK PA5, MOSI PA7, NSS por software; escrita apenas |
| SPI inicial | CPOL baixo / primeira transição, MSB primeiro, 8 bits; frequência conservadora ≤1 MHz até validar o TFT |
| TFT GPIO | PA4 CS alto em repouso, PA8 D/C, PB4 RESET alto após inicialização, PA0 backlight |
| Sensor SA0 | PB12 alto, endereço 0x1D |
| Botões | PC13/PC10/PC11/PC12/PA1, entrada pull-up |
| USART2 | PA2 TX / PA3 RX, 115200 baud, 8N1; confirmar VCP |
| Temporização | Tick de 1 ms; aquisição alvo 50 Hz, UI inicial 10 Hz |

A frequência SPI tem de respeitar o datasheet do controlador e o clock APB2 real. A resolução/offsets e a ordem de cor do TFT devem ser verificadas com padrões antes da UI final.

## Estrutura futura do firmware

```text
firmware/PRUMO/
  PRUMO.ioc                  # a gerar com CubeMX
  Core/Inc/                  # arranque e interfaces gerados
  Core/Src/
  Drivers/                   # HAL/CMSIS do pacote escolhido
  App/                       # aquisição, processamento, botões e scheduler
  Board/                     # adaptação GPIO/I2C/SPI/USART desta board
  Components/                # MMA8452Q, TFT e fonte bitmap
  UI/                        # desenho e estado do nível
```

Manter o código de aplicação em ficheiros próprios e usar as secções `USER CODE` onde for necessário chamar a aplicação a partir de ficheiros gerados. Não editar startup/linker por tentativa: selecionar primeiro o alvo correto e verificar o projeto mínimo.

## Sequência de marcos

| Marco | Resultado a demonstrar | Evidência a guardar |
|---|---|---|
| M0 — ferramentas | Versões, projeto mínimo compila e entra em debug | Versões, `.ioc`, build log, captura do debugger |
| M1 — GPIO/tempo | LED ou contador confirma execução e tick | Captura do contador e configuração |
| M2 — USART | Mensagem e contador chegam ao PC sem erros | Log série, COM e baud |
| M3 — I²C | ACK no endereço e `WHO_AM_I = 0x2A` | Captura de variáveis e, se disponível, traço I²C |
| M4 — aceleração | Dados assinados coerentes com as orientações e gravidade | CSV das posições ±X/±Y/±Z |
| M5 — TFT | Cores e cantos corretos, texto legível e orientação certa | Fotografia real, offsets, ordem RGB/BGR |
| M6 — UI | Bolha, valores, ZERO, HOLD e tolerância funcionam | Vídeo/capturas e lista dos ensaios |
| M7 — resultados | Repetibilidade, erro e resposta documentados | CSV, gráficos, condições e tabela de erros |

Não marcar um marco como concluído só porque uma simulação ou a compilação passou. Distinguir compilação, execução e validação física.

## Build e debug

1. Registar versões de IDE, CubeMX, CubeF1 e compilador.
2. Gerar para STM32CubeIDE e importar/abrir segundo a versão instalada.
3. Fazer build Debug, com símbolos e otimização adequada à depuração (por exemplo, `-Og`).
4. Confirmar o tamanho de Flash/RAM no build e inspecionar o `.map`; não alocar framebuffer completo.
5. Ligar por ST-LINK, interface SWD. Confirmar MCU detetado.
6. Colocar breakpoint no arranque da aplicação; observar tick e contador de amostras.
7. Registar as primeiras variáveis de estado/erro do I²C e a identificação do sensor.
8. Remover breakpoints durante medições de latência ou temporização: parar o CPU perturba a aquisição e a comunicação.

Variáveis úteis propostas para observar: `sample_count`, `i2c_error_count`, `last_i2c_status`, `who_am_i`, `raw_xyz`, `accel_g`, `tilt_deg`, `zero_reference`, `ui_hold`, `tolerance_deg` e `render_time_ms`. Os nomes finais acompanharão o código.

## Processamento e limites

- Ler dados assinados de 12 bits, converter para g e aplicar filtro passa-baixo simples.
- Calcular inclinações pela projeção da gravidade, com `atan2f`/`sqrtf`, definindo explicitamente a convenção dos eixos antes das fórmulas finais.
- Acelerações de movimento contaminam a estimativa de inclinação; avaliar perto de repouso. Monitorizar também a norma da aceleração.
- ZERO deve guardar uma referência angular da posição atual; não deve remover indiscriminadamente a gravidade dos três eixos antes de estimar a orientação.
- O ajuste do filtro será escolhido por medições de ruído e resposta, não apenas por aparência.
- HOLD congela a UI; a telemetria deve continuar com indicação de HOLD. Falhas do sensor devem sobrepor-se a esse estado no aviso de erro.

## Registo proposto

Formato CSV preliminar, independente da UI:

```text
t_ms,seq,ax_g,ay_g,az_g,tilt_x_deg,tilt_y_deg,zero_x_deg,zero_y_deg,tolerance_deg,hold,sensor_ok
```

Formato por fechar na implementação. Preferir unidades explícitas e um cabeçalho estável. Para não aumentar desnecessariamente Flash com `printf` de floats, pode transmitir-se com inteiros escalados e formatação própria. Não fabricar ficheiros de medições enquanto não houver aquisição real.

## Ensaios para a apresentação

- Estabilidade: registar vários segundos com a board imóvel; indicar duração, frequência e número real de amostras.
- Repetibilidade: recolocar várias vezes na mesma superfície e comparar média/dispersão.
- Referência: usar suporte/transferidor de precisão conhecida; indicar a incerteza e evitar tratá-lo como perfeito.
- Resposta: mudar entre duas inclinações e medir o atraso/estabilização, antes e depois do filtro.
- Interface: testar pressões únicas, debounce, HOLD, ZERO, limites das tolerâncias e recuperação de erros.
