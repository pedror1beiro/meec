# PRUMO — STM32F103RB / HAL

Importar esta pasta pelo STM32CubeIDE: **File > Import > Existing Projects into Workspace**. Selecionar o projeto PRUMO e fazer build Debug.

Instruções completas: [Linux, compilação e debug](../../docs/08-linux-cubeide.md).

Este projeto já inclui o HAL/CMSIS de STM32CubeF1 v1.8.7, arranque, linker e código de aplicação. A configuração está em C; não há `.ioc` gerado/validado pelo CubeMX. Não é preciso gerar código novo para compilar o projeto existente.

Principais ficheiros:

- `Core/Src/board.c`: clock interno de 64 MHz e periféricos/pinos.
- `Core/Inc/prumo_config.h`: configuração do painel, sinais dos eixos, frequências e timeouts.
- `Components/mma8452q.c`: driver do sensor.
- `Components/st7735.c`: escrita SPI do TFT.
- `App/level.c`: filtro, ângulos e controlos.
- `App/app.c`: aquisição, recuperação, scheduling e CSV.
- `UI/ui.c`: desenho do ecrã em blocos de 8 linhas, buffer estático de 2 KiB.
- `vendor-manifest.json`: origens e hashes das dependências ST/Arm incluídas.

O firmware foi preparado para a 3S0 Board 1.2 do esquema fornecido. O build e os testes em PC são distintos da validação física, que precisa de ser feita na board. Os offsets, RGB/BGR e a inicialização do TFT podem exigir ajuste no primeiro ensaio.
