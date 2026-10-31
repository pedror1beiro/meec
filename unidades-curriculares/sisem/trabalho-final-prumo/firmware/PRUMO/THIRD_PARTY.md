# Third-party components

The application/board/sensor/renderer source files were written for this project. External HAL, CMSIS, startup and system files retain their original copyright notices and licenses.

- STM32CubeF1 v1.8.7, commit `d12e75247d5bcedc734f829b394517ab4c2726e3`.
- STM32F1 HAL driver, commit `fee494a92b5ad331f92ad21f76c66a5cb83773ee`: license in `Drivers/STM32F1xx_HAL_Driver/LICENSE.md` (BSD-3-Clause).
- CMSIS Core headers from the CubeF1 snapshot: `Drivers/CMSIS/LICENSE.txt` (Apache-2.0).
- CMSIS Device F1, startup and system code, commit `c8e9a4a4f16b6d2cb2a2083cbe5161025280fb22`: license in `Drivers/CMSIS/Device/ST/STM32F1xx/License.md`.
- `.project`/`.cproject` structure adapted from the official STM32CubeF4 UART_Printf CubeIDE example, with MCU, include paths, source paths, float ABI and libraries changed for this project. Reference: https://github.com/STMicroelectronics/STM32CubeF4/tree/master/Projects/STM32446E-Nucleo/Examples/UART/UART_Printf/STM32CubeIDE

ST7735 register initialization values follow the controller documentation. Neither the afiskon library nor the ST BSP ST7735 component is included as a source dependency.

GNU Arm toolchain libraries used at link time retain their own licenses (newlib and libgcc). Runtime notices are included in `Licenses/`, with the upstream source noted in `Licenses/README.txt`. The toolchain installer is not part of this source delivery.
