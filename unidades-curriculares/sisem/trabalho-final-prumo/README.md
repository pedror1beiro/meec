# PRUMO — nível digital para SISEM.

Projeto com STM32F103RBT6 numa NUCLEO-F103RB, acelerómetro MMA8452Q por I²C e interface no TFT da placa de expansão 3S0 Board 1.2.

## Estado em 2026-10-31

- Aplicação e interface aprovadas: bolha, ângulos X/Y, zero relativo, HOLD, tolerância e vista alternativa por eixos.
- Utilizador confirmou HAL/STM32CubeMX e NUCLEO-F103RB com ST-LINK.
- Firmware HAL implementado em [firmware/PRUMO](firmware/PRUMO/README.md): sensor, TFT, UI, botões, tratamento de erros e telemetria.
- Dependências HAL/CMSIS incluídas e fixadas; projeto nativo STM32CubeIDE com paths relativos.
- Compilação cruzada Debug e Release verificada com Arm GNU 13.2.Rel1. A importação gráfica no CubeIDE/Linux e o ensaio na board continuam pendentes.
- Testes da lógica numérica, controlo, formatação e renderer passaram no PC. A imagem `evidencias/ui-render-host.png` foi produzida pelo renderer C, com valores simulados.
- Nenhuma medição física foi recolhida. O perfil de inicialização/offsets/cores do TFT precisa da confirmação no exemplar real.

## Documentação de trabalho

1. [Requisitos, decisões e dúvidas](docs/01-requisitos-e-decisoes.md)
2. [Hardware e pinagem](docs/02-hardware-e-pinagem.md)
3. [Bibliotecas e ferramentas](docs/03-bibliotecas-e-ferramentas.md)
4. [Compilação, debug e validação](docs/04-compilacao-debug-validacao.md)
5. [Base para a apresentação](docs/05-apresentacao.md)
6. [Diário de desenvolvimento](docs/06-diario.md)
7. [Referências e proveniência](docs/07-fontes.md)
8. **[Como compilar e depurar em Linux](docs/08-linux-cubeide.md)**

Os PDFs originais ficam em `docs/referencias/`, com nomes e hashes em `docs/referencias/manifest.json`. O desenho interativo escolhido está em `design/prumo-tft-board.html`; é um fragmento para pré-visualização, não código para o STM32.

## Próximo marco

Importar `firmware/PRUMO` no STM32CubeIDE do PC Linux, compilar localmente e entrar em debug por SWD. Validar USART2, identificação do sensor e o TFT na board. O clock interno foi escolhido para o firmware não depender da configuração HSE/MCO da NUCLEO.

Cada marco deve acrescentar evidência real à pasta `evidencias/` e uma entrada ao diário. O texto da apresentação deve distinguir proposta, simulação, cálculo e resultado medido.
