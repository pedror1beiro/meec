#include "board.h"

#include "prumo_config.h"
I2C_HandleTypeDef hi2c2;
SPI_HandleTypeDef hspi1;
UART_HandleTypeDef huart2;
volatile uint32_t fatal_code;

void HAL_MspInit(void) {
    __HAL_RCC_AFIO_CLK_ENABLE();
    __HAL_RCC_PWR_CLK_ENABLE();
    /* TFT RESET = PB4/NJTRST. Disable JTAG, retain SWD PA13/PA14. */
    __HAL_AFIO_REMAP_SWJ_NOJTAG();
}
static void clock_init(void) {
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
    osc.PLL.PLLMUL = RCC_PLL_MUL16; /* 8/2 * 16 = 64 MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) Board_Fatal(1);
    clk.ClockType =
        RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2; /* 32 MHz <= APB1 limit */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) Board_Fatal(2);
}
static void gpio_init(void) {
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4 | GPIO_PIN_6, GPIO_PIN_SET); /* TFT/SD CS */
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0 | GPIO_PIN_8, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_4 | GPIO_PIN_12, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_SET); /* unused LIS SPI CS */
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Pin = GPIO_PIN_0 | GPIO_PIN_4 | GPIO_PIN_6 | GPIO_PIN_8;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_0 | GPIO_PIN_4 | GPIO_PIN_12;
    HAL_GPIO_Init(GPIOB, &g);
    g.Pin = GPIO_PIN_2;
    HAL_GPIO_Init(GPIOD, &g);
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    g.Pin = GPIO_PIN_1;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_13;
    HAL_GPIO_Init(GPIOC, &g);
}
void HAL_I2C_MspInit(I2C_HandleTypeDef *h) {
    if (h->Instance != I2C2) return;
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_I2C2_CLK_ENABLE();
    g.Pin = GPIO_PIN_10 | GPIO_PIN_11;
    g.Mode = GPIO_MODE_AF_OD;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &g);
}
static void i2c_init(void) {
    hi2c2.Instance = I2C2;
    hi2c2.Init.ClockSpeed = 100000;
    hi2c2.Init.DutyCycle = I2C_DUTYCYCLE_2;
    hi2c2.Init.OwnAddress1 = 0;
    hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c2.Init.OwnAddress2 = 0;
    hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c2) != HAL_OK) Board_Fatal(3);
}
void HAL_SPI_MspInit(SPI_HandleTypeDef *h) {
    if (h->Instance != SPI1) return;
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_SPI1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    g.Pin = GPIO_PIN_5 | GPIO_PIN_7;
    g.Mode = GPIO_MODE_AF_PP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &g);
}
static void spi_init(void) {
    hspi1.Instance = SPI1;
    hspi1.Init.Mode = SPI_MODE_MASTER;
    hspi1.Init.Direction = SPI_DIRECTION_1LINE;
    hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
    hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
    hspi1.Init.NSS = SPI_NSS_SOFT;
    hspi1.Init.BaudRatePrescaler = PRUMO_TFT_SPI_DIV;
    hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
    hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial = 7;
    if (HAL_SPI_Init(&hspi1) != HAL_OK) Board_Fatal(4);
}
void HAL_UART_MspInit(UART_HandleTypeDef *h) {
    if (h->Instance != USART2) return;
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    g.Pin = GPIO_PIN_2;
    g.Mode = GPIO_MODE_AF_PP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_3;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &g);
    HAL_NVIC_SetPriority(USART2_IRQn, 3, 0);
    HAL_NVIC_EnableIRQ(USART2_IRQn);
}
static void uart_init(void) {
    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart2) != HAL_OK) Board_Fatal(5);
}
void Board_Init(void) {
    HAL_Init();
    clock_init();
    gpio_init();
    uart_init();
    i2c_init();
    spi_init();
}
uint8_t Board_Buttons(void) {
    return (uint8_t)((!HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13) ? 1 : 0) |
                     (!HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_10) ? 2 : 0) |
                     (!HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_11) ? 4 : 0) |
                     (!HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_12) ? 8 : 0) |
                     (!HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_1) ? 16 : 0));
}
void Board_I2CRecover(void) {
    /* Bounded bus clear: recovery attempt, not proof that the bus is healthy. */
    GPIO_InitTypeDef g = {0};
    (void)HAL_I2C_DeInit(&hi2c2);
    __HAL_RCC_I2C2_FORCE_RESET();
    __HAL_RCC_I2C2_RELEASE_RESET();
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10 | GPIO_PIN_11, GPIO_PIN_SET);
    g.Pin = GPIO_PIN_10 | GPIO_PIN_11;
    g.Mode = GPIO_MODE_OUTPUT_OD;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &g);
    for (unsigned i = 0; i < 9; ++i) {
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, GPIO_PIN_RESET);
        HAL_Delay(1);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, GPIO_PIN_SET);
        HAL_Delay(1);
    }
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_RESET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, GPIO_PIN_SET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_SET);
    HAL_Delay(1);
    i2c_init();
}
void Board_Fatal(uint32_t code) {
    fatal_code = code;
    __disable_irq();
    for (;;) {
        __NOP();
    } /* inspect fatal_code / call stack in debugger */
}
