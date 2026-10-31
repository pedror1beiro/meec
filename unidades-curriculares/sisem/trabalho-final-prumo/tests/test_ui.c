#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "ui.h"
static uint8_t screen[128 * 160 * 2];
bool TFT_WriteRows(uint16_t y, uint16_t rows, const uint8_t *pixels) {
    assert(rows == 8 && y + rows <= 160);
    memcpy(screen + y * 128 * 2, pixels, rows * 128 * 2);
    return true;
}
static uint32_t hash(void) {
    uint32_t h = 2166136261U;
    for (unsigned i = 0; i < sizeof(screen); ++i) h = (h ^ screen[i]) * 16777619U;
    return h;
}
static void preview(void) {
    FILE *f = fopen("tmp/tests/ui-preview.ppm", "wb");
    assert(f);
    fputs("P6\n128 160\n255\n", f);
    for (unsigned i = 0; i < sizeof(screen); i += 2) {
        uint16_t c = (uint16_t)((screen[i] << 8) | screen[i + 1]);
        unsigned char rgb[] = {(unsigned char)(((c >> 11) & 31) * 255 / 31),
                               (unsigned char)(((c >> 5) & 63) * 255 / 63),
                               (unsigned char)((c & 31) * 255 / 31)};
        assert(fwrite(rgb, 1, 3, f) == 3);
    }
    fclose(f);
}
static void frame(UiFrame *f) {
    UI_Request(f);
    for (unsigned i = 0; i < 20; ++i) assert(UI_Task());
}
int main(void) {
    UiFrame f = {.sensor_ok = true, .valid = true, .tolerance = 1};
    frame(&f);
    uint32_t flat = hash();
    f.x = 3.2f;
    f.y = -1.4f;
    frame(&f);
    assert(hash() != flat);
    uint32_t tilted = hash();
    preview();
    f.axes = true;
    frame(&f);
    assert(hash() != tilted);
    f.sensor_ok = false;
    f.hold = true;
    frame(&f);
    uint32_t failed = hash();
    f.hold = false;
    frame(&f);
    assert(hash() != failed); /* HOLD header visible but sensor error overrides numbers */
    assert(ui_frames == 5);
    puts("PASS: 128x160 renderer, bounded stripes, changing views and error/HOLD states");
}
