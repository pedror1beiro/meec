#ifndef PRUMO_APP_H
#define PRUMO_APP_H
#include "level.h"
typedef struct {
    uint32_t sample_count, sample_ms, i2c_errors, missed_polls, uart_dropped, display_errors;
    uint32_t last_i2c_status, last_i2c_error, frame_count;
    int16_t raw_x, raw_y, raw_z;
    uint8_t who_am_i, sensor_ok;
    float angle_x, angle_y, relative_x, relative_y, norm_g;
} PrumoDebug;
extern volatile PrumoDebug prumo_debug;
extern LevelState prumo_level;
void App_Init(void);
void App_Task(void);
#endif
