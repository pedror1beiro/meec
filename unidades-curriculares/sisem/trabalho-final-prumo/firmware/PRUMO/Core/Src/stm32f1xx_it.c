#include "board.h"
void NMI_Handler(void) { Board_Fatal(10); }
void HardFault_Handler(void) { Board_Fatal(11); }
void MemManage_Handler(void) { Board_Fatal(12); }
void BusFault_Handler(void) { Board_Fatal(13); }
void UsageFault_Handler(void) { Board_Fatal(14); }
void SVC_Handler(void) {}
void DebugMon_Handler(void) {}
void PendSV_Handler(void) {}
void SysTick_Handler(void) { HAL_IncTick(); }
void USART2_IRQHandler(void) { HAL_UART_IRQHandler(&huart2); }
