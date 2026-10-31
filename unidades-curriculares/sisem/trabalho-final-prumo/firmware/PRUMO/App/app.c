#include "app.h"

#include <math.h>

#include "board.h"
#include "format.h"
#include "mma8452q.h"
#include "prumo_config.h"
#include "st7735.h"
#include "ui.h"
volatile PrumoDebug prumo_debug;
LevelState prumo_level;
static ButtonsState buttons;
static bool connected, display_ready;
static uint32_t last_poll, last_ui, last_retry, last_tft_retry, last_fault_log;
static uint8_t uart_line[256]; /* never modified while TX interrupt owns it */
static int scaled(float v, float factor) { return (int)lroundf(v * factor); }
static void telemetry(uint32_t now) {
    if (huart2.gState != HAL_UART_STATE_READY) {
        prumo_debug.uart_dropped++;
        return;
    }
    CsvBuffer b;
    Csv_Init(&b, (char *)uart_line, sizeof(uart_line));
    Csv_Unsigned(&b, now);
    Csv_Unsigned(&b, prumo_debug.sample_ms);
    Csv_Unsigned(&b, prumo_debug.sample_count);
    Csv_Signed(&b, scaled(prumo_debug.raw_x / 1024.0f, 1000));
    Csv_Signed(&b, scaled(prumo_debug.raw_y / 1024.0f, 1000));
    Csv_Signed(&b, scaled(prumo_debug.raw_z / 1024.0f, 1000));
    Csv_Signed(&b, scaled(prumo_level.angle_x, 100));
    Csv_Signed(&b, scaled(prumo_level.angle_y, 100));
    Csv_Signed(&b, scaled(prumo_level.zero_x, 100));
    Csv_Signed(&b, scaled(prumo_level.zero_y, 100));
    Csv_Signed(&b, scaled(Level_Tolerance(&prumo_level), 100));
    Csv_Unsigned(&b, prumo_level.hold);
    Csv_Unsigned(&b, prumo_debug.sensor_ok);
    Csv_Unsigned(&b, prumo_debug.sensor_ok && prumo_level.valid);
    Csv_Unsigned(&b, prumo_debug.i2c_errors);
    Csv_Unsigned(&b, prumo_debug.missed_polls);
    Csv_Unsigned(&b, prumo_debug.uart_dropped);
    Csv_End(&b);
    if (!b.ok || HAL_UART_Transmit_IT(&huart2, uart_line, (uint16_t)b.length) != HAL_OK)
        prumo_debug.uart_dropped++;
}
static void probe(bool recover) {
    if (recover) Board_I2CRecover();
    uint8_t id = 0;
    HAL_StatusTypeDef r = MMA_Init(&id);
    prumo_debug.who_am_i = id;
    prumo_debug.last_i2c_status = r;
    prumo_debug.last_i2c_error = HAL_I2C_GetError(&hi2c2);
    connected = r == HAL_OK;
    if (!connected) prumo_debug.i2c_errors++;
    prumo_debug.sensor_ok = 0;
    prumo_level.seeded = false;
    prumo_level.valid = false;
}
void App_Init(void) {
    Level_Init(&prumo_level);
    buttons.raw = buttons.stable = Board_Buttons();
    static const char header[] =
        "t_ms,sample_ms,seq,ax_mg,ay_mg,az_mg,x_cdeg,y_cdeg,zero_x_cdeg,zero_y_cdeg,tol_cdeg,hold,"
        "sensor_ok,tilt_valid,i2c_errors,missed_polls,uart_dropped\r\n";
    (void)HAL_UART_Transmit(&huart2, (const uint8_t *)header, sizeof(header) - 1, 100);
    probe(false);
    display_ready = TFT_Init();
    if (!display_ready) prumo_debug.display_errors++;
    last_poll = last_retry = last_ui = last_tft_retry = last_fault_log = HAL_GetTick();
    UiFrame f = {.tolerance = 1};
    UI_Request(&f);
}
void App_Task(void) {
    uint32_t now = HAL_GetTick();
    uint8_t pressed = Buttons_Update(&buttons, Board_Buttons(), now, PRUMO_DEBOUNCE_MS);
    if (pressed & 1) prumo_level.axes_view = !prumo_level.axes_view;
    if (pressed & 2) Level_ChangeTolerance(&prumo_level, 1);
    if (pressed & 8) Level_ChangeTolerance(&prumo_level, -1);
    if (prumo_debug.sensor_ok && prumo_level.valid) {
        if (pressed & 4) Level_Hold(&prumo_level);
        if (pressed & 16) Level_Zero(&prumo_level);
    } else if ((pressed & 4) && prumo_level.hold)
        prumo_level.hold = false;
    if (!connected && (uint32_t)(now - last_retry) >= 1000) {
        last_retry = now;
        probe(true);
        now = HAL_GetTick();
    }
    if ((uint32_t)(now - last_poll) >= PRUMO_SAMPLE_MS) {
        uint32_t periods = (uint32_t)(now - last_poll) / PRUMO_SAMPLE_MS;
        prumo_debug.missed_polls += periods - 1;
        last_poll += periods * PRUMO_SAMPLE_MS;
        if (connected) {
            MMA_Raw raw;
            HAL_StatusTypeDef r = MMA_Read(&raw);
            prumo_debug.last_i2c_status = r;
            prumo_debug.last_i2c_error = HAL_I2C_GetError(&hi2c2);
            if (r == HAL_OK) {
                prumo_debug.raw_x = raw.x;
                prumo_debug.raw_y = raw.y;
                prumo_debug.raw_z = raw.z;
                Level_Update(&prumo_level, PRUMO_AXIS_X_SIGN * raw.x / 1024.0f,
                             PRUMO_AXIS_Y_SIGN * raw.y / 1024.0f, raw.z / 1024.0f,
                             PRUMO_FILTER_ALPHA);
                prumo_debug.sample_ms = now;
                prumo_debug.sample_count++;
                prumo_debug.sensor_ok = 1;
                telemetry(now);
            } else if (r != HAL_BUSY) {
                connected = false;
                prumo_debug.sensor_ok = 0;
                prumo_level.valid = false;
                prumo_debug.i2c_errors++;
                last_retry = now;
            }
            if ((uint32_t)(now - prumo_debug.sample_ms) > PRUMO_STALE_MS) {
                if (prumo_debug.sensor_ok || (uint32_t)(now - last_retry) > PRUMO_STALE_MS) {
                    connected = false;
                    prumo_debug.sensor_ok = 0;
                    prumo_level.valid = false;
                    prumo_debug.i2c_errors++;
                    last_retry = now;
                }
            }
        }
    }
    if (!prumo_debug.sensor_ok && (uint32_t)(now - last_fault_log) >= 100) {
        telemetry(now);
        last_fault_log = now;
    }
    if ((uint32_t)(now - last_ui) >= PRUMO_UI_MS || pressed) {
        float x, y;
        Level_Display(&prumo_level, &x, &y);
        UiFrame f = {.x = x,
                     .y = y,
                     .tolerance = Level_Tolerance(&prumo_level),
                     .sensor_ok = prumo_debug.sensor_ok,
                     .valid = prumo_level.valid,
                     .hold = prumo_level.hold,
                     .relative = prumo_level.calibrated,
                     .axes = prumo_level.axes_view};
        UI_Request(&f);
        last_ui = now;
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, prumo_debug.sensor_ok ? GPIO_PIN_SET : GPIO_PIN_RESET);
    }
    if (display_ready) {
        if (!UI_Task()) {
            display_ready = false;
            prumo_debug.display_errors++;
            last_tft_retry = now;
        }
    } else if ((uint32_t)(now - last_tft_retry) >= 3000) {
        last_tft_retry = now;
        display_ready = TFT_Init();
    }
    prumo_debug.angle_x = prumo_level.angle_x;
    prumo_debug.angle_y = prumo_level.angle_y;
    prumo_debug.relative_x = prumo_level.angle_x - prumo_level.zero_x;
    prumo_debug.relative_y = prumo_level.angle_y - prumo_level.zero_y;
    prumo_debug.norm_g = prumo_level.norm_g;
    prumo_debug.frame_count = ui_frames;
}
