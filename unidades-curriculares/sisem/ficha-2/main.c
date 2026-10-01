#include "stm32f10x.h"

void delay(uint32_t tempo)
{
    volatile uint32_t i;

    for(i = 0; i < tempo; i++);
}


/* exercicio 1 */

void RCC_Config_HSI_Default(void)
{
    RCC_DeInit();

    RCC_HSICmd(ENABLE);

    while(RCC_GetFlagStatus(RCC_FLAG_HSIRDY) == RESET);

    FLASH_SetLatency(FLASH_Latency_0);

    RCC_HCLKConfig(RCC_SYSCLK_Div1);
    RCC_PCLK1Config(RCC_HCLK_Div1);
    RCC_PCLK2Config(RCC_HCLK_Div1);

    RCC_SYSCLKConfig(RCC_SYSCLKSource_HSI);

    while(RCC_GetSYSCLKSource() != 0x00);
}


/* exercicio 2 */

void RCC_Config_HSI_PLL_Max(void)
{
    RCC_DeInit();

    RCC_HSICmd(ENABLE);

    while(RCC_GetFlagStatus(RCC_FLAG_HSIRDY) == RESET);

    FLASH_PrefetchBufferCmd(FLASH_PrefetchBuffer_Enable);
    FLASH_SetLatency(FLASH_Latency_2);

    RCC_HCLKConfig(RCC_SYSCLK_Div1);
    RCC_PCLK1Config(RCC_HCLK_Div2);
    RCC_PCLK2Config(RCC_HCLK_Div1);

    /* HSI / 2 = 4 MHz
       4 x 16 = 64 MHz */
    RCC_PLLConfig(RCC_PLLSource_HSI_Div2, RCC_PLLMul_16);

    RCC_PLLCmd(ENABLE);

    while(RCC_GetFlagStatus(RCC_FLAG_PLLRDY) == RESET);

    RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);

    while(RCC_GetSYSCLKSource() != 0x08);
}


/* exercicio 3 */

void RCC_Config_HSE_Default(void)
{
    RCC_DeInit();

    RCC_HSEConfig(RCC_HSE_ON);

    while(RCC_WaitForHSEStartUp() != SUCCESS);

    FLASH_SetLatency(FLASH_Latency_0);

    RCC_HCLKConfig(RCC_SYSCLK_Div1);
    RCC_PCLK1Config(RCC_HCLK_Div1);
    RCC_PCLK2Config(RCC_HCLK_Div1);

    RCC_SYSCLKConfig(RCC_SYSCLKSource_HSE);

    while(RCC_GetSYSCLKSource() != 0x04);
}


/* exercicio 4 */

void RCC_Config_HSE_PLL_Max(void)
{
    RCC_DeInit();

    RCC_HSEConfig(RCC_HSE_ON);

    while(RCC_WaitForHSEStartUp() != SUCCESS);

    FLASH_PrefetchBufferCmd(FLASH_PrefetchBuffer_Enable);
    FLASH_SetLatency(FLASH_Latency_2);

    RCC_HCLKConfig(RCC_SYSCLK_Div1);
    RCC_PCLK1Config(RCC_HCLK_Div2);
    RCC_PCLK2Config(RCC_HCLK_Div1);

    /* 12 x 6 = 72 MHz */
    RCC_PLLConfig(RCC_PLLSource_HSE_Div1, RCC_PLLMul_6);

    RCC_PLLCmd(ENABLE);

    while(RCC_GetFlagStatus(RCC_FLAG_PLLRDY) == RESET);

    RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);

    while(RCC_GetSYSCLKSource() != 0x08);
}


/* exercicio 5 */

void RCC_Config_30MHz(void)
{
    RCC_DeInit();

    RCC_HSEConfig(RCC_HSE_ON);

    while(RCC_WaitForHSEStartUp() != SUCCESS);

    FLASH_PrefetchBufferCmd(FLASH_PrefetchBuffer_Enable);
    FLASH_SetLatency(FLASH_Latency_1);

    RCC_HCLKConfig(RCC_SYSCLK_Div1);
    RCC_PCLK1Config(RCC_HCLK_Div1);
    RCC_PCLK2Config(RCC_HCLK_Div1);

    /* HSE / 2 = 6 MHz
       6 x 5 = 30 MHz */
    RCC_PLLConfig(RCC_PLLSource_HSE_Div2, RCC_PLLMul_5);

    RCC_PLLCmd(ENABLE);

    while(RCC_GetFlagStatus(RCC_FLAG_PLLRDY) == RESET);

    RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);

    while(RCC_GetSYSCLKSource() != 0x08);
}


/* configuracao do LED */

void LED_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOA, &GPIO_InitStructure);
}


void piscar10(void)
{
    uint8_t i;

    for(i = 0; i < 10; i++)
    {
        GPIO_SetBits(GPIOA, GPIO_Pin_5);
        delay(1000000);

        GPIO_ResetBits(GPIOA, GPIO_Pin_5);
        delay(1000000);
    }
}


/* exercicio 6 */

void exercicio6(void)
{
    RCC_Config_30MHz();

    LED_Init();

    while(1)
    {
        /* 10 piscadelas a 30 MHz */
        piscar10();

        /* HSI + PLL = 64 MHz */
        RCC_Config_HSI_PLL_Max();

        /* 10 piscadelas a 64 MHz */
        piscar10();

        /* volta aos 30 MHz */
        RCC_Config_30MHz();
    }
}


int main(void)
{
    RCC_ClocksTypeDef clocks;

    /* usado apenas para testar as frequencias */
    (void)clocks;

    /* descomentar apenas o exercicio pretendido */

    /* exercicio 1 */
    //RCC_Config_HSI_Default();
    //RCC_GetClocksFreq(&clocks);

    /* exercicio 2 */
    //RCC_Config_HSI_PLL_Max();
    //RCC_GetClocksFreq(&clocks);

    /* exercicio 3 */
    //RCC_Config_HSE_Default();
    //RCC_GetClocksFreq(&clocks);

    /* exercicio 4 */
    //RCC_Config_HSE_PLL_Max();
    //RCC_GetClocksFreq(&clocks);

    /* exercicio 5 */
    //RCC_Config_30MHz();
    //RCC_GetClocksFreq(&clocks);

    /* exercicio 6 */
    exercicio6();

    while(1);
}
