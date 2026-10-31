#include "level.h"

#include <math.h>
#include <string.h>
static const float tolerances[] = {0.2f, 0.5f, 1.0f, 2.0f, 5.0f};
void Level_Init(LevelState *s) {
    memset(s, 0, sizeof(*s));
    s->tolerance_index = 2;
}
int16_t MMA_Decode12(uint8_t msb, uint8_t lsb) {
    int32_t n = ((uint16_t)msb << 4) | (lsb >> 4);
    if (n & 0x800) n -= 4096; /* explicit sign extension, no signed-shift assumption */
    return (int16_t)n;
}
void Level_Update(LevelState *s, float ax, float ay, float az, float alpha) {
    s->norm_g = sqrtf(ax * ax + ay * ay + az * az);
    if (!isfinite(s->norm_g) || s->norm_g < 0.01f) {
        s->valid = false;
        return;
    }
    if (!s->seeded) {
        s->ax = ax;
        s->ay = ay;
        s->az = az;
        s->seeded = true;
    } else {
        s->ax += alpha * (ax - s->ax);
        s->ay += alpha * (ay - s->ay);
        s->az += alpha * (az - s->az);
    }
    /* Two inclination angles relative to horizontal; no heading/yaw claim. */
    s->angle_x = atan2f(s->ax, sqrtf(s->ay * s->ay + s->az * s->az)) * 57.295779513f;
    s->angle_y = atan2f(s->ay, sqrtf(s->ax * s->ax + s->az * s->az)) * 57.295779513f;
    s->valid = s->norm_g >= 0.75f && s->norm_g <= 1.25f;
}
void Level_Zero(LevelState *s) {
    if (!s->valid) return;
    s->zero_x = s->angle_x;
    s->zero_y = s->angle_y;
    s->calibrated = true;
    s->hold = false;
}
void Level_Hold(LevelState *s) {
    if (s->hold) {
        s->hold = false;
        return;
    }
    if (!s->valid) return;
    s->held_x = s->angle_x - s->zero_x;
    s->held_y = s->angle_y - s->zero_y;
    s->hold = true;
}
void Level_Display(const LevelState *s, float *x, float *y) {
    *x = s->hold ? s->held_x : s->angle_x - s->zero_x;
    *y = s->hold ? s->held_y : s->angle_y - s->zero_y;
}
float Level_Tolerance(const LevelState *s) { return tolerances[s->tolerance_index]; }
void Level_ChangeTolerance(LevelState *s, int d) {
    int n = (int)s->tolerance_index + d;
    if (n >= 0 && n < 5) s->tolerance_index = (uint8_t)n;
}
uint8_t Buttons_Update(ButtonsState *s, uint8_t raw, uint32_t now, uint32_t debounce) {
    uint8_t pressed = 0;
    for (unsigned i = 0; i < 5; ++i) {
        uint8_t bit = (uint8_t)(1U << i);
        if ((raw ^ s->raw) & bit) {
            s->raw ^= bit;
            s->changed[i] = now;
        }
        if (((raw ^ s->stable) & bit) && (uint32_t)(now - s->changed[i]) >= debounce) {
            s->stable ^= bit;
            if (raw & bit) pressed |= bit;
        }
    }
    return pressed;
}
