#include "st7735.h"

#include "prumo_config.h"
static bool command(uint8_t cmd, const uint8_t *data, uint16_t n) {
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET);
    HAL_StatusTypeDef r = HAL_SPI_Transmit(&hspi1, &cmd, 1, PRUMO_SPI_TIMEOUT_MS);
    if (r == HAL_OK && n) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);
        r = HAL_SPI_Transmit(&hspi1, (uint8_t *)data, n, PRUMO_SPI_TIMEOUT_MS);
    }
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);
    return r == HAL_OK;
}
/* Register values from the ST7735R programming sequence. Each complete
 * register payload is sent in one transaction, not as repeated commands. */
bool TFT_Init(void) {
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4, GPIO_PIN_RESET);
    HAL_Delay(20);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4, GPIO_PIN_SET);
    HAL_Delay(120);
    if (!command(0x01, 0, 0)) return false;
    HAL_Delay(150);
    if (!command(0x11, 0, 0)) return false;
    HAL_Delay(150);
    static const struct {
        uint8_t cmd, n, data[16];
    } init[] = {{0xB1, 3, {0x01, 0x2C, 0x2D}},
                {0xB2, 3, {0x01, 0x2C, 0x2D}},
                {0xB3, 6, {0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D}},
                {0xB4, 1, {0x07}},
                {0xC0, 3, {0xA2, 0x02, 0x84}},
                {0xC1, 1, {0xC5}},
                {0xC2, 2, {0x0A, 0x00}},
                {0xC3, 2, {0x8A, 0x2A}},
                {0xC4, 2, {0x8A, 0xEE}},
                {0xC5, 1, {0x0E}},
                {0xE0,
                 16,
                 {0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00,
                  0x01, 0x03, 0x10}},
                {0xE1,
                 16,
                 {0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00,
                  0x00, 0x02, 0x10}},
                {0x36, 1, {PRUMO_TFT_MADCTL}},
                {0x3A, 1, {0x05}}};
    for (unsigned i = 0; i < sizeof(init) / sizeof(init[0]); ++i)
        if (!command(init[i].cmd, init[i].data, init[i].n)) return false;
    if (!command(PRUMO_TFT_INVERT ? 0x21 : 0x20, 0, 0)) return false;
    if (!command(0x13, 0, 0)) return false;
    HAL_Delay(10);
    if (!command(0x29, 0, 0)) return false;
    HAL_Delay(100);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);
    return true;
}
bool TFT_WriteRows(uint16_t y, uint16_t rows, const uint8_t *pixels) {
    if (y >= 160 || !rows || rows > 8 || y + rows > 160) return false;
    uint16_t x0 = PRUMO_TFT_X_OFFSET, x1 = x0 + 127;
    uint16_t y0 = y + PRUMO_TFT_Y_OFFSET, y1 = y0 + rows - 1;
    uint8_t col[] = {x0 >> 8, x0 & 255, x1 >> 8, x1 & 255};
    uint8_t row[] = {y0 >> 8, y0 & 255, y1 >> 8, y1 & 255};
    return command(0x2A, col, 4) && command(0x2B, row, 4) &&
           command(0x2C, pixels, (uint16_t)(128 * rows * 2));
}
