#ifndef PRUMO_ST7735_H
#define PRUMO_ST7735_H
#include "board.h"
bool TFT_Init(void);
/* RGB565 big-endian byte order, already prepared by renderer. */
bool TFT_WriteRows(uint16_t y, uint16_t rows, const uint8_t *rgb565);
#endif
