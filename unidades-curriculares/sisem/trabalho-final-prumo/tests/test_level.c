#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "format.h"
#include "level.h"
static void near(float a, float b) { assert(fabsf(a - b) < 0.02f); }
int main(void) {
    char buf[64];
    CsvBuffer csv;
    Csv_Init(&csv, buf, sizeof(buf));
    Csv_Unsigned(&csv, UINT32_MAX);
    Csv_Signed(&csv, INT32_MIN);
    Csv_End(&csv);
    assert(csv.ok && !strcmp(buf, "4294967295,-2147483648\r\n"));
    Csv_Init(&csv, buf, 4);
    Csv_Unsigned(&csv, 10000);
    assert(!csv.ok);
    char angle[9];
    Format_Angle(angle, -3.2f);
    assert(!strcmp(angle, "-03.2o"));
    Format_Angle(angle, 180);
    assert(!strcmp(angle, "+180.0o"));
    assert(MMA_Decode12(0x7F, 0xF0) == 2047);
    assert(MMA_Decode12(0x80, 0x00) == -2048);
    assert(MMA_Decode12(0xFF, 0xF0) == -1);
    assert(MMA_Decode12(0x00, 0x1F) == 1);
    LevelState s;
    Level_Init(&s);
    near(Level_Tolerance(&s), 1);
    Level_Update(&s, 0, 0, 1, 1);
    assert(s.valid);
    near(s.angle_x, 0);
    near(s.angle_y, 0);
    Level_Update(&s, .5f, 0, .8660254f, 1);
    near(s.angle_x, 30);
    near(s.angle_y, 0);
    Level_Zero(&s);
    float x, y;
    Level_Display(&s, &x, &y);
    near(x, 0);
    assert(s.calibrated);
    Level_Update(&s, .7071068f, 0, .7071068f, 1);
    Level_Display(&s, &x, &y);
    near(x, 15);
    Level_Hold(&s);
    assert(s.hold);
    Level_Update(&s, 0, 0, 1, 1);
    Level_Display(&s, &x, &y);
    near(x, 15);
    near(s.angle_x, 0);
    Level_Hold(&s);
    Level_Display(&s, &x, &y);
    near(x, -30);
    Level_Update(&s, 0, 0, 2, 1);
    assert(!s.valid);
    Level_Zero(&s);
    near(s.zero_x, 30);
    Level_Hold(&s);
    assert(!s.hold);
    Level_Update(&s, 0, 0, 0, 1);
    assert(!s.valid);
    Level_Init(&s);
    Level_Update(&s, 0, 0, 1, .2f);
    Level_Update(&s, 1, 0, 0, .2f);
    near(s.ax, .2f);
    near(s.az, .8f);
    for (int i = 0; i < 10; ++i) Level_ChangeTolerance(&s, 1);
    near(Level_Tolerance(&s), 5);
    for (int i = 0; i < 10; ++i) Level_ChangeTolerance(&s, -1);
    near(Level_Tolerance(&s), .2f);
    ButtonsState b = {0};
    assert(!Buttons_Update(&b, 1, 10, 25));
    assert(!Buttons_Update(&b, 0, 15, 25));
    assert(!Buttons_Update(&b, 1, 20, 25));
    assert(!Buttons_Update(&b, 1, 44, 25));
    assert(Buttons_Update(&b, 1, 45, 25) == 1);
    assert(!Buttons_Update(&b, 1, 100, 25));
    assert(!Buttons_Update(&b, 0, 101, 25));
    assert(!Buttons_Update(&b, 0, 126, 25));
    assert(!Buttons_Update(&b, 1, 130, 25));
    assert(Buttons_Update(&b, 1, 155, 25) == 1);
    ButtonsState wrap = {0};
    assert(!Buttons_Update(&wrap, 16, UINT32_MAX - 10, 25));
    assert(Buttons_Update(&wrap, 16, 20, 25) == 16);
    puts(
        "PASS: signed samples, tilt, calibration, HOLD, validity, filtering, tolerance, debounce "
        "and tick wrap");
}
