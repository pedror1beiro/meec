#include "ui.h"

#include <math.h>
#include <string.h>

#include "format.h"
#include "prumo_config.h"
#include "st7735.h"
/* 5x7 bitmap glyphs, stored as constant column masks in Flash. */
typedef struct {
    char c;
    uint8_t col[5];
} Glyph;
static const Glyph font[] = {
    {'A', {0x7E, 0x09, 0x09, 0x09, 0x7E}}, {'B', {0x7F, 0x49, 0x49, 0x49, 0x36}},
    {'C', {0x3E, 0x41, 0x41, 0x41, 0x22}}, {'D', {0x7F, 0x41, 0x41, 0x22, 0x1C}},
    {'E', {0x7F, 0x49, 0x49, 0x49, 0x41}}, {'F', {0x7F, 0x09, 0x09, 0x09, 0x01}},
    {'G', {0x3E, 0x41, 0x49, 0x49, 0x3A}}, {'H', {0x7F, 0x08, 0x08, 0x08, 0x7F}},
    {'I', {0x41, 0x41, 0x7F, 0x41, 0x41}}, {'J', {0x20, 0x40, 0x41, 0x3F, 0x01}},
    {'K', {0x7F, 0x08, 0x14, 0x22, 0x41}}, {'L', {0x7F, 0x40, 0x40, 0x40, 0x40}},
    {'M', {0x7F, 0x02, 0x0C, 0x02, 0x7F}}, {'N', {0x7F, 0x04, 0x08, 0x10, 0x7F}},
    {'O', {0x3E, 0x41, 0x41, 0x41, 0x3E}}, {'P', {0x7F, 0x09, 0x09, 0x09, 0x06}},
    {'Q', {0x3E, 0x41, 0x51, 0x21, 0x5E}}, {'R', {0x7F, 0x09, 0x19, 0x29, 0x46}},
    {'S', {0x46, 0x49, 0x49, 0x49, 0x31}}, {'T', {0x01, 0x01, 0x7F, 0x01, 0x01}},
    {'U', {0x3F, 0x40, 0x40, 0x40, 0x3F}}, {'V', {0x1F, 0x20, 0x40, 0x20, 0x1F}},
    {'W', {0x7F, 0x20, 0x18, 0x20, 0x7F}}, {'X', {0x63, 0x14, 0x08, 0x14, 0x63}},
    {'Y', {0x03, 0x04, 0x78, 0x04, 0x03}}, {'Z', {0x61, 0x51, 0x49, 0x45, 0x43}},
    {'0', {0x3E, 0x51, 0x49, 0x45, 0x3E}}, {'1', {0x00, 0x42, 0x7F, 0x40, 0x00}},
    {'2', {0x62, 0x51, 0x49, 0x49, 0x46}}, {'3', {0x22, 0x41, 0x49, 0x49, 0x36}},
    {'4', {0x18, 0x14, 0x12, 0x7F, 0x10}}, {'5', {0x27, 0x45, 0x45, 0x45, 0x39}},
    {'6', {0x3C, 0x4A, 0x49, 0x49, 0x30}}, {'7', {0x01, 0x71, 0x09, 0x05, 0x03}},
    {'8', {0x36, 0x49, 0x49, 0x49, 0x36}}, {'9', {0x06, 0x49, 0x49, 0x29, 0x1E}},
    {'+', {0x08, 0x08, 0x3E, 0x08, 0x08}}, {'-', {0x08, 0x08, 0x08, 0x08, 0x08}},
    {'.', {0x00, 0x60, 0x60, 0x00, 0x00}}, {'o', {0x06, 0x09, 0x09, 0x06, 0x00}},
    {'/', {0x60, 0x10, 0x08, 0x04, 0x03}}, {':', {0x00, 0x36, 0x36, 0x00, 0x00}}};
#define BG 0x08A3U
#define HEAD 0x1166U
#define INK 0xEFBCU
#define MUTED 0x8D55U
#define GRID 0x3289U
#define GREEN 0xB72EU
#define AMBER 0xF5ECU
#define RED 0xF2C8U
static uint8_t tile[128 * 8 * 2];
static unsigned tile_y;
static UiFrame pending, active;
static bool dirty, busy;
uint32_t ui_frames;
static void pixel(int x, int y, uint16_t color) {
    if (x < 0 || x >= 128 || y < (int)tile_y || y >= (int)tile_y + 8) return;
    unsigned p = ((unsigned)(y - (int)tile_y) * 128U + (unsigned)x) * 2U;
    tile[p] = (uint8_t)(color >> 8);
    tile[p + 1] = (uint8_t)color;
}
static void box(int x, int y, int w, int h, uint16_t color) {
    int left = x < 0 ? 0 : x, right = x + w > 128 ? 128 : x + w;
    int top = y < (int)tile_y ? (int)tile_y : y;
    int bottom = y + h > (int)tile_y + 8 ? (int)tile_y + 8 : y + h;
    for (int yy = top; yy < bottom; ++yy)
        for (int xx = left; xx < right; ++xx) pixel(xx, yy, color);
}
static void text(int x, int y, const char *s, int scale, uint16_t color) {
    if (y + 7 * scale <= (int)tile_y || y >= (int)tile_y + 8) return;
    for (; *s; ++s, x += 6 * scale) {
        const Glyph *g = 0;
        for (unsigned i = 0; i < sizeof(font) / sizeof(font[0]); ++i)
            if (font[i].c == *s) {
                g = &font[i];
                break;
            }
        if (!g) continue;
        for (int xx = 0; xx < 5; ++xx)
            for (int yy = 0; yy < 7; ++yy)
                if (g->col[xx] & (1U << yy))
                    box(x + xx * scale, y + yy * scale, scale, scale, color);
    }
}
static void centered(int y, const char *s, uint16_t color) {
    text((128 - ((int)strlen(s) * 6 - 1)) / 2, y, s, 1, color);
}
static void circle(int cx, int cy, int r, uint16_t color, bool filled) {
    int y0 = cy - r < (int)tile_y ? (int)tile_y : cy - r;
    int y1 = cy + r >= (int)tile_y + 8 ? (int)tile_y + 7 : cy + r;
    for (int y = y0; y <= y1; ++y)
        for (int x = cx - r; x <= cx + r; ++x) {
            int d = (x - cx) * (x - cx) + (y - cy) * (y - cy);
            if (d <= r * r && (filled || d >= (r - 1) * (r - 1))) pixel(x, y, color);
        }
}
static void scene(void) {
    box(0, (int)tile_y, 128, 8, BG);
    if (PRUMO_TFT_TEST_PATTERN) {
        const uint16_t c[] = {0xF800, 0x07E0, 0x001F, 0xFFFF};
        for (unsigned i = 0; i < 4; ++i) box((int)i * 32, 0, 32, 160, c[i]);
        text(2, 2, "TOP", 1, 0);
        text(2, 151, "BOTTOM", 1, 0);
        return;
    }
    bool ok = active.sensor_ok && active.valid;
    bool level = ok && fabsf(active.x) <= active.tolerance && fabsf(active.y) <= active.tolerance;
    uint16_t color = level ? GREEN : AMBER;
    box(0, 0, 128, 15, HEAD);
    text(5, 4, "PRUMO", 1, INK);
    text(100, 4, active.hold ? "HOLD" : "LIVE", 1, active.hold ? AMBER : GREEN);
    centered(20,
             !active.sensor_ok ? "ERRO SENSOR"
             : !active.valid   ? "MOVIMENTO"
             : level           ? "NIVELADO"
                               : "INCLINADO",
             !active.sensor_ok ? RED : color);
    if (!ok) {
        centered(49, active.sensor_ok ? "MANTER IMOVEL" : "VERIFICAR I2C", MUTED);
        centered(66, active.sensor_ok ? "AGUARDAR" : "MMA8452Q", MUTED);
    } else if (active.axes) {
        text(6, 35, "EIXO X", 1, MUTED);
        box(8, 51, 112, 12, HEAD);
        box(64, 49, 1, 16, GRID);
        box(62 + (int)lroundf(fmaxf(-52, fminf(52, active.x * 5.2f))), 52, 5, 10, color);
        text(6, 72, "EIXO Y", 1, MUTED);
        box(8, 88, 112, 12, HEAD);
        box(64, 86, 1, 16, GRID);
        box(62 + (int)lroundf(fmaxf(-52, fminf(52, active.y * 5.2f))), 89, 5, 10, color);
    } else {
        circle(64, 66, 34, GRID, false);
        circle(64, 66, 17, GRID, false);
        box(29, 66, 71, 1, GRID);
        box(64, 31, 1, 71, GRID);
        int limit = (int)lroundf(active.tolerance * 2.8f);
        if (limit < 2) limit = 2;
        if (limit > 29) limit = 29;
        box(64 - limit, 66 - limit, 2 * limit + 1, 2 * limit + 1, HEAD);
        box(64 - limit, 66 - limit, 2 * limit + 1, 1, GREEN);
        box(64 - limit, 66 + limit, 2 * limit + 1, 1, GREEN);
        box(64 - limit, 66 - limit, 1, 2 * limit + 1, GREEN);
        box(64 + limit, 66 - limit, 1, 2 * limit + 1, GREEN);
        float dx = -active.x * 2.8f, dy = -active.y * 2.8f, len = sqrtf(dx * dx + dy * dy);
        if (len > 29) {
            dx *= 29 / len;
            dy *= 29 / len;
        }
        int bx = 64 + (int)lroundf(dx), by = 66 + (int)lroundf(dy);
        circle(bx, by, 5, color, true);
        box(bx, by - 2, 1, 5, BG);
        box(bx - 2, by, 5, 1, BG);
        text(58, 29, "+Y", 1, MUTED);
        text(12, 63, "+X", 1, MUTED);
    }
    char b[32];
    text(6, 111, "X", 1, MUTED);
    text(6, 132, "Y", 1, MUTED);
    if (ok) {
        Format_Angle(b, active.x);
        text(29, 106, b, 2, INK);
        Format_Angle(b, active.y);
        text(29, 127, b, 2, INK);
    } else {
        text(29, 106, "--.-o", 2, MUTED);
        text(29, 127, "--.-o", 2, MUTED);
    }
    box(0, 147, 128, 13, HEAD);
    unsigned t = (unsigned)lroundf(active.tolerance * 10);
    char tol[] = "TOL 0.0o";
    tol[4] = (char)('0' + t / 10);
    tol[6] = (char)('0' + t % 10);
    text(5, 150, tol, 1, MUTED);
    text(105, 150, active.relative ? "REL" : "ABS", 1, MUTED);
}
void UI_Request(const UiFrame *frame) {
    pending = *frame;
    dirty = true;
}
bool UI_Task(void) {
    if (!busy) {
        if (!dirty) return true;
        active = pending;
        dirty = false;
        busy = true;
        tile_y = 0;
    }
    scene();
    if (!TFT_WriteRows((uint16_t)tile_y, 8, tile)) {
        busy = false;
        return false;
    }
    tile_y += 8;
    if (tile_y == 160) {
        busy = false;
        ui_frames++;
    }
    return true;
}
