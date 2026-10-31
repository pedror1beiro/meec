#ifndef PRUMO_BOARD_H
#define PRUMO_BOARD_H
#include <stdbool.h>

#include "stm32f1xx_hal.h"
extern I2C_HandleTypeDef hi2c2;
extern SPI_HandleTypeDef hspi1;
extern UART_HandleTypeDef huart2;
void Board_Init(void);
void Board_Fatal(uint32_t code);
uint8_t Board_Buttons(void);
void Board_I2CRecover(void);
#endif
