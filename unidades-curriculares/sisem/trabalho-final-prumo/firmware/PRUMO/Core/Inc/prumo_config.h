#ifndef PRUMO_CONFIG_H
#define PRUMO_CONFIG_H
/* All board/panel choices are centralized here. HSI/PLL: no external crystal needed. */
#define PRUMO_SAMPLE_MS 20U
#define PRUMO_UI_MS 100U
#define PRUMO_DEBOUNCE_MS 25U
#define PRUMO_STALE_MS 200U
#define PRUMO_FILTER_ALPHA 0.18f
#define PRUMO_MMA_ADDR7 0x1DU
#define PRUMO_TFT_X_OFFSET 0U
#define PRUMO_TFT_Y_OFFSET 0U
/* MX|MY, RGB: change to 0xC8 if red and blue are swapped. */
#define PRUMO_TFT_MADCTL 0xC0U
#define PRUMO_TFT_INVERT 0U
#define PRUMO_TFT_SPI_DIV SPI_BAUDRATEPRESCALER_16
#define PRUMO_TFT_TEST_PATTERN 0U
#define PRUMO_AXIS_X_SIGN 1.0f
#define PRUMO_AXIS_Y_SIGN 1.0f
#define PRUMO_I2C_TIMEOUT_MS 8U
#define PRUMO_SPI_TIMEOUT_MS 25U
#endif
