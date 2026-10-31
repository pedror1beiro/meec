# Requisitos e decisões

Data inicial: 2026-10-31. Contexto: SISEM 2026/27, trabalho ADC/SPI/I²C.

## Requisitos do enunciado

Fonte: [enunciado original](referencias/FichaDeTrabalhoFinal.pdf), páginas 1–2.

- Estudar um periférico do STM32 e ler um dos sensores propostos.
- O sensor escolhido é o MMA8452Q, ligado por I²C.
- Enviar os dados do microcontrolador para o computador por ligação série assíncrona através da USART.
- Tratar os resultados; o enunciado dá como exemplo uma demonstração e um gráfico.
- Documentar estudo do sensor, estudo do periférico/biblioteca, implementação, validação e resultados.
- Entregar documentação em formato de apresentação, que funciona como relatório.

Não foi fornecida uma grelha de avaliação. Não há evidência de que jogos, originalidade ou a estética tenham um peso específico. A opção por validação quantitativa é uma decisão nossa para demonstrar o trabalho técnico.

## Decisões confirmadas com o utilizador

| Decisão | Justificação |
|---|---|
| Nível digital PRUMO | Aplicação prática e fácil de validar com inclinações conhecidas. |
| Interface local no TFT | Aproveitar o ecrã da placa de expansão. |
| NUCLEO-F103RB / STM32F103RBT6 | Hardware indicado e confirmado pelo utilizador. |
| HAL / STM32CubeMX | Preferência confirmada pelo utilizador em 2026-10-31. |
| Compilação e debug no STM32CubeIDE | Objetivo explícito do utilizador. |
| Documentação contínua | Guardar decisões, fontes e evidências para a apresentação. |

Foram encontrados exemplos locais em `C:\meec\unidades-curriculares\sisem` que usam registos e Standard Peripheral Library. São apenas contexto; a indicação posterior do utilizador para HAL prevalece. Não misturar os dois conjuntos de bibliotecas no projeto.

## Funcionalidades propostas para a primeira versão

- Mostrar bolha e inclinações em dois eixos no TFT de 128 × 160 píxeis.
- Definir zero relativo por botão.
- Congelar a apresentação da leitura por HOLD; continuar a aquisição e a telemetria.
- Ajustar tolerância por eixo: 0,2°, 0,5°, 1°, 2° ou 5°.
- Alternar entre bolha e indicadores por eixo.
- Transmitir amostras e estados por USART2 para registo no computador.

Tolerância é um critério escolhido pelo utilizador, não uma garantia de precisão do sensor. Mostrar uma casa decimal também não demonstra precisão de 0,1°.

## Critérios de funcionamento a validar

- Nivelado: `abs(angulo_x) <= tolerancia` e `abs(angulo_y) <= tolerancia`.
- ZERO guarda a referência atual; não altera a sensibilidade física do sensor.
- HOLD congela a UI, mantendo visível essa condição.
- Perda de comunicação produz um estado de erro identificável; nunca apresentar uma leitura antiga como uma leitura atual válida.
- Os sinais e a correspondência entre ângulos, eixos físicos e movimento da bolha devem ser verificados na board.

## Questões técnicas ainda abertas

- Caminhos e versões de CubeIDE, CubeMX, compilador e pacote CubeF1 efetivamente instalados.
- Revisão da NUCLEO e origem real do clock: HSI, cristal HSE ou MCO do ST-LINK.
- Ligação física de USART2 ao VCP do ST-LINK, incluindo pontes da revisão da NUCLEO.
- Sequência de inicialização, offsets, ordem RGB/BGR e orientação exatos do TFT.
- Aprovação pelo docente das bibliotecas, se houver uma exigência adicional não presente no enunciado.
- Formato final de entrega: seguir o enunciado (apresentação); paper pode ser material complementar se fizer sentido.
