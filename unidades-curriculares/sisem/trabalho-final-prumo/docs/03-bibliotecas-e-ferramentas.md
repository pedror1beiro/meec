# Arquitetura, bibliotecas e ferramentas

## Organização do firmware

| Módulo | Responsabilidade |
|---|---|
| `Core/Src/main.c` | Inicializar a placa e a aplicação e repetir `App_Task()`. |
| `Core/Src/board.c` | Configurar clocks, pinos, periféricos e recuperação do barramento I²C. |
| `Components/mma8452q.c` | Identificar, configurar e ler o acelerómetro. |
| `App/level.c` | Descodificar amostras, filtrar, calcular ângulos e gerir controlos/debounce. |
| `App/app.c` | Coordenar aquisição, telemetria, interface e estados de erro. |
| `App/format.c` | Formatar CSV e ângulos em buffers limitados. |
| `UI/ui.c` | Desenhar a interface em faixas de oito linhas. |
| `Components/st7735.c` | Inicializar o TFT e transmitir comandos e píxeis por SPI. |

O ciclo principal usa agendamento cooperativo pelo tick de 1 ms da HAL. O sensor e os botões são consultados periodicamente. A USART transmite por interrupção; I²C e SPI usam funções bloqueantes com timeout. A aplicação não usa RTOS, DMA ou alocação dinâmica.

## Dependências incluídas

| Componente | Origem e utilização |
|---|---|
| STM32CubeF1 v1.8.7 | Subconjunto HAL/CMSIS incluído no projeto, com commits e hashes fixados. |
| STM32F1 HAL | GPIO, RCC, I²C2, SPI1, USART2 e temporização. |
| CMSIS Core / Device F1 | Definições Cortex-M3, registos, arranque e sistema. |
| Drivers MMA8452Q e TFT | Módulos específicos deste projeto, sobre HAL. |
| Desenho e fonte bitmap | Código do projeto, com tabelas constantes em Flash. |
| `libm` | `atan2f`, `sqrtf` e restantes operações matemáticas. |

O manifesto `firmware/PRUMO/vendor-manifest.json` identifica os 111 ficheiros externos e respetivos hashes. As licenças e origens estão em `firmware/PRUMO/THIRD_PARTY.md`, `Drivers/` e `Licenses/`. As bibliotecas ST7735 da ST e de afiskon foram consultadas como referências e não estão incorporadas como dependências de código.

## Memória e apresentação

Um framebuffer RGB565 de 128 × 160 ocupa 40 960 bytes, acima dos 20 KiB de SRAM. O código usa um buffer estático de `128 × 8 × 2 = 2048` bytes e a memória interna do TFT.

Cada chamada a `UI_Task()` desenha e transmite uma faixa. Um frame completo tem vinte faixas e mantém uma cópia estável do estado apresentado. O código atual redesenha a imagem completa por faixas; a atualização apenas de regiões alteradas é uma melhoria possível.

## Ferramentas

- STM32CubeIDE: importar, compilar e depurar o projeto por ST-LINK/SWD.
- Arm GNU Toolchain com newlib: compilação alternativa com `firmware/PRUMO/tools/build.py`.
- Python 3.12 ou posterior e GCC nativo: testes no PC e preparação da entrega.
- Python/pyserial: logger opcional da ligação série; não é uma dependência do firmware.

A configuração HAL entregue está em C. Não existe um `.ioc` gerado/validado pelo CubeMX e não é necessário criar um projeto novo para compilar este firmware. As [instruções Linux/CubeIDE](08-linux-cubeide.md) descrevem os passos e os limites da validação disponível.
