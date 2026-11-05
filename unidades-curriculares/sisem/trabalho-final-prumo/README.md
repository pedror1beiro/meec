# Nível digital — SISEM

Aplicação para STM32F103RBT6 na NUCLEO-F103RB, com acelerómetro MMA8452Q por I²C e TFT da placa de expansão 3S0 Board 1.2. O projeto de firmware chama-se PRUMO.

O sistema estima duas inclinações a partir da gravidade, apresenta os valores e uma bolha no ecrã e transmite dados por USART2. Os botões permitem definir ZERO relativo, ativar HOLD, ajustar a tolerância e alternar a vista. A utilização pressupõe uma superfície aproximadamente horizontal e imóvel.

## Estado da entrega — 4 de novembro de 2026

- Firmware implementado com HAL/CMSIS incluídos e configuração de pinos e clocks em C. Não é necessário gerar um projeto CubeMX para o compilar.
- Compilação Debug/Release anteriormente verificada com Arm GNU 13.2.Rel1; relatórios em `evidencias/`.
- Testes de lógica, formatação, botões, desenho e metadados do projeto verificados no PC na revisão final.
- O grupo relata execução na placa, apresentação no TFT e funcionamento dos botões/modos. Estes ensaios são funcionais; não foram repetidos na revisão documental.
- Não foram disponibilizados dados numéricos de aquisição nem comparação com referência angular. A precisão, a repetibilidade e os tempos reais de resposta continuam por caracterizar.
- O gráfico e a ilustração da interface na apresentação são simulações identificadas como tal.

## Consultar e executar

1. [Apresentação final](docs/Nivel_Digital_SISEM.pptx): 10 slides principais e 2 slides técnicos de apoio.
2. [Importação, compilação e debug](docs/08-linux-cubeide.md): abrir `firmware/PRUMO` no STM32CubeIDE.
3. [Hardware e pinagem](docs/02-hardware-e-pinagem.md).
4. [Arquitetura e bibliotecas](docs/03-bibliotecas-e-ferramentas.md).
5. [Configuração, processamento e validação](docs/04-compilacao-debug-validacao.md).
6. [Requisitos e funcionalidades](docs/01-requisitos-e-decisoes.md).
7. [Guião da apresentação](docs/05-apresentacao.md), [fontes](docs/07-fontes.md) e [histórico de desenvolvimento](docs/06-diario.md).

Com GCC nativo e Python 3.12 ou posterior, os testes no PC correm com `python3 tools/run_tests.py`. Para compilar o alvo, é necessário o toolchain Arm GNU com newlib ou o compilador incluído no CubeIDE.

O logger opcional em `tools/log_serial.py` guarda os dados reais da USART. Os originais devem ficar em `dados/`, acompanhados das condições do ensaio.

## Preparar o pacote

Executar `python3 tools/package_delivery.py` a partir desta pasta. O pacote `entrega/Nivel_Digital_SISEM-entrega.zip` inclui apresentação, fontes, dependências, documentação e evidências disponíveis. Ficheiros temporários e ferramentas de desenvolvimento ficam excluídos.
