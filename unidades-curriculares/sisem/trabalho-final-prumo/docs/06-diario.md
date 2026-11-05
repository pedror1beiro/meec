# Diário de desenvolvimento

## 2026-10-31 — definição e preparação

### Decisões

- A ideia inicial de comando/rato evoluiu para um nível digital com validação quantitativa.
- O utilizador aprovou a interface com bolha e pediu que funcionasse no TFT da board.
- Foram propostas e explicadas funções para ZERO, HOLD, tolerância e vista alternativa; o utilizador concordou.
- O utilizador confirmou HAL/STM32CubeMX, NUCLEO-F103RB e ST-LINK para a base de desenvolvimento.
- O objetivo é compilar e depurar no STM32CubeIDE e guardar documentação para a apresentação.

### Trabalho realizado

- Leitura do enunciado, datasheets e esquema.
- Identificação de I²C2 em PB10/PB11, SPI1 do TFT, botões e alternativas USART.
- Verificação das dimensões e resolução do painel no desenho do modelo JD-T18003-T01.
- Criação e teste de simulação interativa com framebuffer de 128 × 160 píxeis e paleta limitada.
- Testes da simulação: zero relativo, HOLD, mudança de tolerância, alternância de vistas e adaptação a larguras de 320/360/736 píxeis; sem erros JavaScript observados. São testes do mockup, não do firmware.
- Pesquisa de bibliotecas oficiais e candidatos de driver do TFT; registadas origens e referências de versão.
- Identificação de exemplos locais SPL; preferência explícita por HAL prevaleceu.
- Preparação da documentação, fontes locais e roteiro de validação.

### Observações importantes

- Um framebuffer RGB565 completo excede a SRAM do STM32F103RB.
- PB4 é usado pelo reset do TFT e deve ser libertado de JTAG, mantendo SWD.
- PA9/PA10 são partilhados entre USART1 e ESP8266; preferir USART2/VCP, após confirmação da ligação.
- As versões e caminhos das ferramentas ainda não foram localizados nesta máquina.

### Estado dos marcos

M0–M7: pendentes. Não houve build, programação, sessão de debug ou medição física nesta sessão.

## 2026-10-31 — implementação para entrega em Linux

- Pedido do utilizador: desenvolver código para executar noutro PC Linux com STM32CubeIDE.
- Implementados drivers HAL de board, MMA8452Q, TFT, scheduler, filtro e ângulos, botões, UI por blocos, tratamento de erros e CSV por USART2/IT.
- Projeto nativo CubeIDE com configuração C e caminhos relativos; configuração gráfica `.ioc` não foi gerada nem alegada como validada.
- Incluído subconjunto HAL/CMSIS de CubeF1 v1.8.7 com commits, hashes e licenças; 111 ficheiros de fornecedor.
- Clock HSI/PLL de 64 MHz elimina dependência de cristal/MCO externo na primeira execução.
- Buffer de desenho de 2 KiB; não há framebuffer completo nem alocação dinâmica na aplicação. Formatação CSV própria evita dependência de `printf` com heap.
- Build independente Arm GNU 13.2.Rel1 passou em Debug e Release, sem avisos finais. Flash: Debug 19820 bytes / Release 17668 bytes; RAM reservada pelo linker: 5248 bytes, incluindo 2048 bytes de reserva mínima para stack.
- Testes no PC passaram: descodificação assinada, inclinação, calibração, HOLD, validade, filtro, tolerância, debounce com wrap do tick, formatação limitada e renderer de 128 × 160 por blocos.
- Verificados metadados XML, paths relativos, vetores/segmentos ELF, limites de Flash/RAM, hashes do fornecedor e cabeçalho CSV.
- O ZIP foi extraído numa pasta independente e o código voltou a compilar para Cortex-M3, sem recorrer a headers/fontes da pasta original. Isto verifica a completude da entrega, não a execução no Linux ou no hardware.
- Criadas instruções de importação/debug, logger opcional e pacote de entrega.
- **Ainda pendentes:** importar/compilar no CubeIDE/Linux do utilizador, debug ST-LINK físico, comunicação elétrica, offsets/cores/inicialização do painel e medições experimentais.
- M0: compilação cruzada concluída; importação gráfica/debug no alvo pendentes. M1–M7 físicos pendentes.

## 2026-10-31 — correção da leitura do projeto pelo CubeIDE

- Sintoma reportado: Build/Run/Debug sem efeito e configuração ativa indisponível, com um aviso de encoding.
- Identificado um erro nos metadados gerados: faltava `<?fileVersion 4.0.0?>` no `.cproject`. O leitor de configurações do Eclipse CDT exige uma processing instruction como primeiro nó DOM e rejeita o documento sem ela.
- Restaurado o marcador e adicionada a preferência explícita de encoding UTF-8. O aviso de encoding é independente do erro de leitura das configurações.
- Acrescentados testes de regressão que validam o primeiro nó DOM, as configurações Debug/Release, o builder e a preferência UTF-8. Um simples teste de sintaxe XML não detetava o problema anterior.
- A correção dos metadados não altera o código do firmware. A confirmação na instalação CubeIDE/Linux do utilizador continua pendente.
- Referência do leitor CDT: https://github.com/eclipse-cdt/cdt/blob/main/core/org.eclipse.cdt.core/model/org/eclipse/cdt/internal/core/settings/model/CProjectDescriptionStorageManager.java

## 2026-11-04 — revisão para entrega

- Consolidada a documentação para descrever a implementação existente: HAL em C, 64 MHz, SPI de 4 MHz, CSV de 17 campos e desenho completo por faixas.
- A apresentação do grupo relata execução na placa, TFT e controlos funcionais. Este relato atualiza o estado documental de 31 de outubro; a revisão não repetiu os ensaios físicos e não recebeu dados numéricos de aquisição.
- Acrescentados comentários pontuais e nomes para os registos do MMA8452Q, preservando os valores de configuração e o comportamento do firmware.
- Apresentação incluída na entrega, com dois slides técnicos de apoio. As simulações continuam identificadas.
- Os resultados da validação final ficam em `evidencias/revisao-final-2026-11-04.txt`. Os registos anteriores de compilação mantêm a sua data e âmbito.

## Modelo para novas entradas

```text
Data:
Objetivo:
Alteração efetuada:
Versões/commit:
Ensaio e condições:
Resultado observado:
Evidência e dados:
Limitações/problemas:
Próximo passo:
```
