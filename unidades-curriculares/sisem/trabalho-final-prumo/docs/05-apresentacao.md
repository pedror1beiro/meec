# Base para a apresentação

Documento vivo; o enunciado pede formato de apresentação. Podemos transformar esta estrutura em PowerPoint no final. Um paper exige confirmar se é aceite como entrega ou se será apenas complementar.

**Estado atual: firmware implementado, compilação e testes no PC verificados; ainda sem resultados físicos.** A imagem `evidencias/ui-render-host.png` foi produzida pelo renderer C e deve ser identificada como simulação.

## Mensagem central

Desenvolver um nível digital com STM32F103RB e acelerómetro MMA8452Q, estudar o I²C e demonstrar aquisição, processamento, interface local e envio de dados ao computador.

## Estrutura proposta de 10–12 slides

| Slide | Conteúdo | Material a recolher |
|---|---|---|
| 1 | Título PRUMO, autores e objetivo | Nomes/grupo; fotografia do protótipo final |
| 2 | Requisitos do trabalho e aplicação escolhida | Enunciado e diagrama de blocos |
| 3 | Hardware: STM32, sensor e ecrã | Esquema anotado e fotografia |
| 4 | MMA8452Q: princípio, eixos e registos usados | Datasheet, escala, ODR e WHO_AM_I |
| 5 | I²C2 e sequência de leitura | Endereço, ACK, registos, traço do analisador se disponível |
| 6 | Arquitetura do firmware e bibliotecas | Diagrama e versões efetivas HAL/CMSIS |
| 7 | Conversão, inclinação e filtragem | Fórmulas com convenção definida; parâmetros efetivos |
| 8 | UI e controlos no TFT | Fotografia real; mockup identificado como simulação |
| 9 | Validação experimental | Montagem, referência, condições e incerteza |
| 10 | Resultados quantitativos | Gráficos de estabilidade, erro e resposta |
| 11 | Limitações e melhorias | Movimento, ruído, calibração, memória e rendimento |
| 12 | Conclusões e demonstração | O que foi demonstrado e quais os objetivos atingidos |

## Factos já utilizáveis

- Aplicação escolhida e funções dos botões aprovadas como proposta.
- Hardware identificado pelo esquema e pelo utilizador.
- TFT com área ativa de 28,03 × 35,04 mm e grelha 128 × 160, conforme desenho do modelo indicado.
- Cálculo de memória: framebuffer RGB565 completo de 40 KiB excede a SRAM de 20 KiB do MCU; desenho por regiões é a estratégia prevista.
- Utilização prevista de I²C2, SPI1 e USART2; HAL/STM32CubeMX confirmados pelo utilizador.

Todos estes pontos têm fontes ou decisões registadas noutros documentos. Nenhum comprova que o firmware já correu no alvo.

## Resultados que ainda faltam

- Identificação e leituras reais do sensor.
- Debug físico bem-sucedido na board e build local no CubeIDE/Linux. O build independente para Cortex-M3 já foi verificado e os relatórios estão em `evidencias/`.
- Fotografia do TFT a apresentar a UI real.
- Frequências reais de aquisição e atualização; tempo de desenho.
- Erro face à referência, repetibilidade, ruído e resposta ao filtro.

Não escrever valores de precisão, tempos, frequências efetivas ou taxas de sucesso até existirem ensaios. Uma tolerância selecionada na UI não é uma medição de precisão.

## Organização das evidências

- Guardar em `evidencias/` ficheiros com data e descrição.
- Guardar os dados de origem em `dados/`; manter a versão original sem tratamento.
- Para cada gráfico: identificar ficheiro, ensaio, amostras excluídas e transformação aplicada.
- Para cada imagem: registar se é fotografia, captura de debugger, desenho ou simulação.
- Preservar autoria, URLs, revisões de datasheets e licenças das bibliotecas reutilizadas.
