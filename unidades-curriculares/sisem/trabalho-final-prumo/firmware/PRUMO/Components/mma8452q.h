#ifndef PRUMO_MMA8452Q_H
#define PRUMO_MMA8452Q_H
#include "board.h"
#include "level.h"
typedef struct {
    int16_t x, y, z;
} MMA_Raw;
HAL_StatusTypeDef MMA_Init(uint8_t *id);
/* HAL_BUSY means no new data yet, not a transaction failure. */
HAL_StatusTypeDef MMA_Read(MMA_Raw *raw);
#endif
