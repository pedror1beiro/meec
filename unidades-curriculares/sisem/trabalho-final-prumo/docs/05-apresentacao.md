# Guião da apresentação

A [apresentação final](Nivel_Digital_SISEM.pptx) tem 10 slides principais e 2 slides de apoio técnico. Os slides de apoio podem ser usados durante a defesa sem alongar a exposição principal.

| Slide | Mensagem a explicar |
|---|---|
| 1 — Nível digital | Objetivo, autores e plataforma STM32. |
| 2 — Objetivo | Indicar se uma superfície está nivelada dentro da tolerância escolhida. |
| 3 — Componentes principais | Acelerómetro, microcontrolador, ecrã e botões. |
| 4 — Comunicação com o sensor | I²C: STM32 mestre, dados em SDA e relógio em SCL. |
| 5 — Tratamento das leituras | Ler acelerações, suavizar e calcular inclinações usando a gravidade. |
| 6 — Utilização | ZERO, HOLD, tolerância e mudança de vista. |
| 7 — Dados no computador | USART2 e formato para guardar e analisar as leituras. |
| 8 — Testes realizados | Execução, informação no TFT e resposta aos controlos relatadas pelo grupo. |
| 9 — Exemplo de leitura | Simulação que ilustra suavização e atraso, sem representar medições reais. |
| 10 — Conclusões | Integração funcional e caracterização angular como passo seguinte. |
| 11 — Configuração técnica | Alvo, sensor, I²C, SPI, USART e registos principais. |
| 12 — Processamento e arquitetura | Conversão, filtro, fórmulas, tarefas e memória. |

## Pontos a defender

- O sensor fornece acelerações; os ângulos são calculados pelo STM32.
- A escala ±2 g corresponde a 1024 contagens/g no modo de 12 bits usado.
- A ODR nominal de 50 Hz, o barramento I²C a 100 kHz e a consulta a cada 20 ms são grandezas distintas.
- O filtro é aplicado às componentes de aceleração; α menor suaviza mais e atrasa a resposta.
- ZERO define uma referência relativa. HOLD mantém a apresentação e deixa continuar a aquisição e o CSV.
- O código desenha uma imagem completa em vinte faixas de oito linhas, com buffer de 2 KiB.
- A tolerância e uma casa decimal no ecrã não demonstram exatidão angular.

## Resultados e fontes

Os testes na placa apresentados são funcionais e relatados pelo grupo. Os testes no PC e relatórios de compilação têm âmbito próprio. Não foi disponibilizado um CSV real ou uma comparação com referência angular para esta entrega documental.

A fotografia do slide 2 identifica o hardware. A interface do slide 6 e o gráfico do slide 9 são simulações identificadas. As fontes constam das notas dos slides e de [fontes e proveniência](07-fontes.md). A configuração efetiva e os limites estão em [configuração e validação](04-compilacao-debug-validacao.md).
