#ifndef PRUMO_LEVEL_H
#define PRUMO_LEVEL_H
#include <stdbool.h>
#include <stdint.h>
typedef struct {
    float ax, ay, az, norm_g;
    float angle_x, angle_y, zero_x, zero_y;
    float held_x, held_y;
    bool seeded, valid, calibrated, hold, axes_view;
    uint8_t tolerance_index;
} LevelState;
typedef struct {
    uint8_t raw, stable;
    uint32_t changed[5];
} ButtonsState;
void Level_Init(LevelState *s);
void Level_Update(LevelState *s, float ax, float ay, float az, float alpha);
void Level_Zero(LevelState *s);
void Level_Hold(LevelState *s);
void Level_Display(const LevelState *s, float *x, float *y);
float Level_Tolerance(const LevelState *s);
void Level_ChangeTolerance(LevelState *s, int direction);
uint8_t Buttons_Update(ButtonsState *s, uint8_t raw, uint32_t now, uint32_t debounce);
int16_t MMA_Decode12(uint8_t msb, uint8_t lsb);
#endif
