# Bibliotecas e ferramentas

Escolha confirmada: HAL, configuração com STM32CubeMX, compilação e debug no STM32CubeIDE, MCU STM32F103RBT6.

## Conjunto mínimo

| Componente | Origem | Utilização | Estado |
|---|---|---|---|
| STM32CubeF1 | STMicroelectronics | Pacote compatível com STM32F1, incluindo HAL e CMSIS | Subconjunto v1.8.7 incluído, com hashes |
| STM32F1 HAL | Dentro do mesmo CubeF1 | GPIO, RCC, I2C2, SPI1, USART2 e temporização | Integrado; configuração HAL em C |
| CMSIS Core e Device F1 | Dentro do mesmo CubeF1 | Definições Cortex-M3, registos, sistema e suporte de arranque | Integrado com versões do pacote |
| Driver MMA8452Q | Código nosso, sobre HAL I2C | Inicialização, identificação e leitura de amostras | Implementado e compilado; ensaio físico pendente |
| Driver TFT ST7735 | Código nosso, sobre HAL SPI | Reset, comandos, regiões e envio de cores RGB565 | Implementado e compilado; perfil físico pendente |
| Gráficos e fonte bitmap | Código nosso, em Flash | Linhas, círculos, texto e UI de 128 × 160 | Implementados; renderer testado no PC |
| Biblioteca matemática `libm` | Toolchain Arm GNU | `atan2f`, `sqrtf` e cálculo de inclinação | Ligação verificada com `-lm` |

A primeira versão usa primitivas gráficas pequenas e não precisa de uma framework de GUI ou de um sistema operativo. A comunicação USART faz parte da aplicação, sem USB Device próprio no STM32: o VCP pode ser fornecido pelo ST-LINK.

## Versão de referência do pacote

Subconjunto integrado em 2026-10-31: **STM32CubeF1 v1.8.7**, commit `d12e75247d5bcedc734f829b394517ab4c2726e3`. Os ficheiros vendorizados, commits HAL/Device e hashes estão em `firmware/PRUMO/vendor-manifest.json`. O build independente passou; o ensaio do hardware e a importação gráfica no IDE/Linux ainda estão pendentes.

A versão individual da HAL e os commits de CMSIS devem ser os que esse pacote referencia. Não juntar headers retirados de um pacote SPL aos headers HAL/CMSIS de CubeF1.

Fontes: [pacote oficial](https://github.com/STMicroelectronics/STM32CubeF1), [tag proposta](https://github.com/STMicroelectronics/STM32CubeF1/tree/v1.8.7), [organização dos pacotes](https://wiki.st.com/stm32mcu/wiki/Getting_started_with_STM32Cube_MCU_Package).

## Driver do sensor

O MMA8452Q usa agora um módulo pequeno escrito a partir do datasheet, com operações HAL sobre registos. Isso permite explicar a comunicação I²C e os registos na apresentação.

Implementado: identificação e configuração em `MMA_Init`, estado/amostras em `MMA_Read` e descodificação assinada em `MMA_Decode12`. Todas as transações têm timeout finito. A aplicação regista erros e tenta recuperar a comunicação após falha.

## Driver do TFT

O esquema disponibiliza SPI de escrita, CS, D/C, reset e controlo de backlight. As rotinas específicas da placa devem ficar separadas do desenho da UI.

Foram examinadas duas referências, **ainda não incorporadas**:

1. [Componente oficial ST7735 da ST](https://github.com/STMicroelectronics/stm32-st7735), tag v2.0.4, commit `354b04160fdbda6e4320dcfe20ad329df83bed97`. Oferece operações de desenho e callbacks de barramento. A configuração e a sequência de inicialização precisam de validação no painel concreto.
2. [stm32-st7735 de afiskon](https://github.com/afiskon/stm32-st7735), commit `b9408107226246a8494e6a729dfaeebfa0a75a5d`, licença MIT. O código consultado vem configurado para F4, pinos de outra placa e 128 × 128; não pode ser copiado e usado sem adaptação. Algumas rotinas `Fast` usam alocação dinâmica, que não deve ser usada para um ecrã inteiro neste MCU.

Decisão de arquitetura: criar um driver pequeno para esta board, com interface HAL e buffers estáticos limitados. Se for reutilizado código de uma das referências, registar commit, adaptações e preservar os avisos/licenças correspondentes antes de o incorporar.

## Limite de memória

Um framebuffer RGB565 completo exige `128 × 160 × 2 = 40960 bytes` (40 KiB), superior aos 20 KiB de SRAM do STM32F103RB. Usar a RAM interna do controlador do TFT e escrever apenas regiões alteradas, com um buffer pequeno por linha/bloco. Por exemplo, uma linha RGB565 de 128 píxeis exige 256 bytes. Fontes e tabelas constantes devem residir em Flash.

O desenho deve atualizar os valores e a região da bolha sem apagar todo o ecrã a cada amostra. A atualização da UI não tem de ocorrer à mesma frequência da aquisição. Medir tempo de atualização e ocupação real no ficheiro `.map`.

## Ferramentas de desenvolvimento

- STM32CubeIDE: editar, compilar, ligar, gravar e depurar via ST-LINK/SWD.
- STM32CubeMX: configurar pinos/periféricos/clocks, guardar `.ioc` e gerar o projeto HAL para STM32CubeIDE.
- STM32CubeF1: pacote de firmware para o MCU.
- Toolchain Arm GNU e servidor ST-LINK: normalmente fornecidos pelo conjunto de ferramentas ST; confirmar versões instaladas.
- Monitor série para o primeiro teste de USART. Python/pyserial pode ser acrescentado depois para registo CSV; não é dependência do firmware.

Nas versões CubeIDE 2.x, a configuração CubeMX é separada; versões antigas podiam integrá-la no IDE. As instruções de abertura do `.ioc` devem acompanhar a versão efetivamente instalada. Fontes: [CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html), [CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html), [explicação da ST para CubeIDE 2.0](https://community.st.com/stm32cubeide-mcus-28/issue-in-ioc-file-generation-162056).

## Inventário local desta sessão

Na preparação inicial não foram localizados CubeIDE/CubeMX/Arm GCC. Na implementação foi obtido o Arm GNU Toolchain 13.2.Rel1 portátil, do fornecedor, e verificado o SHA-256; foi usado para compilar Debug e Release. O projeto passou a incluir `.project`/`.cproject`, HAL/CMSIS e build independente. O IDE gráfico/Linux e a board ainda não foram ensaiados. Não foi criada uma configuração `.ioc` fictícia: a configuração HAL está em C e o projeto pode ser importado diretamente no IDE.
