# Fontes e proveniência

Consultadas em 2026-10-31. As cópias locais dos PDFs e da fotografia estão em `referencias/`; o manifesto JSON regista origem, tamanho e SHA-256. Não foram alterados os originais fornecidos pelo utilizador.

## Documentos do utilizador

| Documento | Uso |
|---|---|
| [Ficha de trabalho](referencias/FichaDeTrabalhoFinal.pdf) | Requisitos e formato de entrega, páginas 1–2 |
| [MMA8452Q](referencias/I2C_MMA8452Q.pdf) | NXP Rev. 10, 04/2016; pinos, endereços, conversão e registos |
| [STM32F103x8/xB](referencias/STMicroelectronics-STM32F103RBT6-datasheet.pdf) | DocID13587 Rev. 17; recursos e funções dos pinos, em especial páginas 29–32 |
| [Esquema da board](referencias/sisem.pdf) | 3S0 Board 1.2, 2016-09-23; ligações e componentes |
| [Fotografia da board](referencias/board-frente.png) | Orientação do ecrã e disposição física dos botões |

## Fontes externas principais

- [Desenho do módulo JD-T18003-T01](https://dl.singtown.com/datasheet/JD-T18003-T01.pdf): dimensões e resolução na página 5; cópia local em `referencias/JD-T18003-T01.pdf`.
- [Joy-IT RB-TFT1.8](https://www.joy-it.net/en/products/RB-TFT1.8): referência complementar ao mesmo painel; não confundir as dimensões da placa Joy-IT com as do LCD da nossa board.
- [NXP AN3461](https://www.nxp.com/docs/en/application-note/AN3461.pdf): inclinação pela gravidade e limitações sob movimento.
- [STM32CubeF1 oficial](https://github.com/STMicroelectronics/STM32CubeF1): HAL, CMSIS, exemplos e dependências de submódulos.
- [STM32CubeF1 v1.8.7](https://github.com/STMicroelectronics/STM32CubeF1/tree/v1.8.7): referência de versão do pacote, ainda não integrada.
- [Estrutura de um pacote Cube](https://wiki.st.com/stm32mcu/wiki/Getting_started_with_STM32Cube_MCU_Package).
- [RM0008 — manual de referência STM32F1](https://www.st.com/resource/en/reference_manual/cd00171190-stm32f101-103-105-107-stm32f100-series-armbased-32bit-mcus-stmicroelectronics.pdf): consultar os capítulos GPIO/AFIO, RCC, SPI, I²C, USART e debug ao implementar os periféricos.
- [UM1724 — Nucleo-64 MB1136](https://www.st.com.cn/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf): referência para clocks, ST-LINK e pontes de USART2/VCP; conferir a revisão física.
- [STM32CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html): compilação e debug ST-LINK.
- [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html): configuração e geração.
- [Resposta da ST sobre CubeIDE 2.0/CubeMX separado](https://community.st.com/stm32cubeide-mcus-28/issue-in-ioc-file-generation-162056).
- [Driver ST7735 oficial](https://github.com/STMicroelectronics/stm32-st7735): referência de API; não incorporado.
- [Driver ST7735 afiskon](https://github.com/afiskon/stm32-st7735): referência HAL/MIT; não incorporado.
- [Standard Peripheral Library STSW-STM32054](https://www.st.com/en/embedded-software/stsw-stm32054.html): pesquisada por existirem exemplos locais SPL, mas não escolhida como base.

## Exemplos locais consultados, sem alteração

- `C:\meec\unidades-curriculares\sisem\ficha-1\main.c`
- `C:\meec\unidades-curriculares\sisem\ficha-2\main.c`
- `C:\meec\unidades-curriculares\sisem\mainf3.c`

Apresentam acessos a registos e funções SPL. Serviram para identificar uma possível diferença em relação à base HAL confirmada posteriormente pelo utilizador. Não constituem instrução para mudar de biblioteca nem são prova de que um clock externo de 12 MHz exista na NUCLEO utilizada.
