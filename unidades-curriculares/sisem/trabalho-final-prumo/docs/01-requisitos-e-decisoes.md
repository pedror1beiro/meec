# Requisitos e decisões

## Enquadramento

O [enunciado de SISEM 2026/27](referencias/FichaDeTrabalhoFinal.pdf), páginas 1–2, pede o estudo de um periférico do STM32, leitura de um dos sensores indicados, envio dos dados ao computador por USART, tratamento dos resultados e documentação em formato de apresentação.

Foi escolhido o MMA8452Q e o periférico I²C. A aplicação é um nível digital: a orientação da gravidade permite estimar a inclinação quando a placa está aproximadamente imóvel. O TFT por SPI e os botões acrescentam uma interface local.

## Decisões de implementação

| Decisão | Justificação |
|---|---|
| NUCLEO-F103RB / STM32F103RBT6 | Plataforma usada com a placa de expansão 3S0 Board 1.2. |
| HAL e CMSIS de STM32CubeF1 v1.8.7 | Acesso aos periféricos com dependências incluídas e identificadas. |
| Configuração HAL escrita em C | Projeto existente importável no CubeIDE, sem `.ioc` gerado/validado. |
| HSI/2 e PLL ×16, 64 MHz nominais | Evitar dependência de cristal ou MCO externo na configuração entregue. |
| Consulta do sensor a cada 20 ms | Alvo de aquisição compatível com a ODR configurada de 50 Hz. |
| Pedido de UI a cada 100 ms | Separar a aquisição do ritmo de apresentação. |
| Desenho em faixas de oito linhas | Buffer de 2 KiB, compatível com os 20 KiB de SRAM. |
| USART2 a 115200 baud, 8N1 | Transmissão dos valores e estados para o computador. |

O código usa HAL. Os exemplos de fichas que usam SPL são material separado e não fazem parte deste firmware.

## Funcionalidades implementadas

- Bolha e inclinações X/Y no TFT de 128 × 160 píxeis.
- ZERO guarda os ângulos atuais como referência relativa e cancela HOLD.
- HOLD mantém os valores apresentados, enquanto a aquisição e a telemetria continuam.
- Tolerância por eixo: 0,2°, 0,5°, 1°, 2° ou 5°; valor inicial de 1°.
- Vista alternativa com indicadores por eixo.
- CSV com acelerações, ângulos, referência e indicadores de validade/erro.
- Aviso de falha do sensor ou leitura inválida e tentativa limitada de recuperação do I²C.

O estado nivelado exige que os módulos dos dois ângulos apresentados sejam inferiores ou iguais à tolerância. ZERO e tolerância ficam em RAM e perdem-se com o reset. A tolerância é um critério de aceitação e não uma garantia de exatidão.

## Validação e limites

O grupo relata testes funcionais de execução, apresentação e controlos na placa, registados na [apresentação](Nivel_Digital_SISEM.pptx). Os testes no PC verificam lógica e desenho; os relatórios de compilação verificam construção do executável.

Não foram disponibilizados registos numéricos reais, uma referência angular ou medições de tempos. Esses resultados não devem ser inferidos das simulações. O teste de norma do vetor de aceleração deteta apenas algumas condições inadequadas e não garante ausência de movimento.
