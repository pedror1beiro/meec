#include "stm32f10x.h"


/* configuracao do relogio a 72 MHz */

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


/* configuracao do LED PB0 */

void LED_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    GPIO_ResetBits(GPIOB, GPIO_Pin_0);
}


/* TIM3: update a cada 0,5 segundos */

void TIM3_Init(void)
{
    TIM_TimeBaseInitTypeDef TIM_InitStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);

    /* 72 MHz / 7200 / 5000 = 2 Hz */
    TIM_InitStructure.TIM_Prescaler = 7199;
    TIM_InitStructure.TIM_Period = 4999;
    TIM_InitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_InitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM3, &TIM_InitStructure);

    TIM_ClearFlag(TIM3, TIM_FLAG_Update);
    TIM_Cmd(TIM3, ENABLE);
}


/* conta os updates do TIM3 para verificar no debugger */

volatile uint32_t eventos = 0;


/* exercicio 1: alterna o LED PB0 a cada update */

uint8_t AtualizarLED(void)
{
    if(TIM_GetFlagStatus(TIM3, TIM_FLAG_Update) == RESET)
        return 0;

    TIM_ClearFlag(TIM3, TIM_FLAG_Update);
    eventos++;

    if(GPIO_ReadOutputDataBit(GPIOB, GPIO_Pin_0) == Bit_SET)
        GPIO_ResetBits(GPIOB, GPIO_Pin_0);
    else
        GPIO_SetBits(GPIOB, GPIO_Pin_0);

    return 1;
}


/* exercicio 2: TIM3 canal 4 em modo Toggle (PB1) */

void TIM3_Toggle_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    TIM_OCInitTypeDef TIM_OCInitStructure;

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    TIM_OCStructInit(&TIM_OCInitStructure);
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_Toggle;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 2500;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OC4Init(TIM3, &TIM_OCInitStructure);
}


/* exercicio 3: PWM de 1 kHz com TIM4 */

void TIM4_PWM_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    TIM_TimeBaseInitTypeDef TIM_InitStructure;
    TIM_OCInitTypeDef TIM_OCInitStructure;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);

    /* PB6 vermelho; PB7 e PB8 a confirmar na placa */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7 | GPIO_Pin_8;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    /* 72 MHz / 72 / 1000 = 1 kHz */
    TIM_InitStructure.TIM_Prescaler = 71;
    TIM_InitStructure.TIM_Period = 999;
    TIM_InitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_InitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM4, &TIM_InitStructure);

    TIM_OCStructInit(&TIM_OCInitStructure);
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_Low;

    TIM_OC1Init(TIM4, &TIM_OCInitStructure);
    TIM_OC2Init(TIM4, &TIM_OCInitStructure);
    TIM_OC3Init(TIM4, &TIM_OCInitStructure);

    TIM_OC1PreloadConfig(TIM4, TIM_OCPreload_Enable);
    TIM_OC2PreloadConfig(TIM4, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(TIM4, TIM_OCPreload_Enable);
    TIM_ARRPreloadConfig(TIM4, ENABLE);

    TIM_ClearFlag(TIM4, TIM_FLAG_Update);
    TIM_Cmd(TIM4, ENABLE);
}


/* exercicio 5: valores de 0 a 255 para cada cor */

void SetRGBColor(uint8_t red, uint8_t green, uint8_t blue)
{
    TIM_SetCompare1(TIM4, ((uint32_t)red * 1000) / 255);
    TIM_SetCompare2(TIM4, ((uint32_t)green * 1000) / 255);
    TIM_SetCompare3(TIM4, ((uint32_t)blue * 1000) / 255);
}


/* exercicio 1 */

void exercicio1(void)
{
    while(1)
    {
        AtualizarLED();
    }
}


/* exercicio 2 */

void exercicio2(void)
{
    TIM3_Toggle_Init();

    while(1)
    {
        AtualizarLED();
    }
}


/* exercicio 3 */

void exercicio3(void)
{
    uint8_t contagem = 0;
    uint8_t pwm_alto = 0;

    TIM3_Toggle_Init();
    TIM4_PWM_Init();
    TIM_SetCompare1(TIM4, 50); /* 5% */

    while(1)
    {
        if(AtualizarLED())
        {
            contagem++;

            /* muda o duty cycle a cada 2 segundos */
            if(contagem == 4)
            {
                contagem = 0;
                pwm_alto = !pwm_alto;

                if(pwm_alto)
                    TIM_SetCompare1(TIM4, 950); /* 95% */
                else
                    TIM_SetCompare1(TIM4, 50);  /* 5% */
            }
        }
    }
}


/* exercicio 4 */

void exercicio4(void)
{
    uint8_t ms = 0;
    uint16_t brilho = 0;
    int8_t direcao = 1;

    TIM3_Toggle_Init();
    TIM4_PWM_Init();

    while(1)
    {
        AtualizarLED();

        /* cada update do TIM4 corresponde a 1 ms */
        if(TIM_GetFlagStatus(TIM4, TIM_FLAG_Update) != RESET)
        {
            TIM_ClearFlag(TIM4, TIM_FLAG_Update);
            ms++;

            if(ms == 20)
            {
                ms = 0;

                if(direcao > 0)
                {
                    brilho += 10;
                    if(brilho == 1000)
                        direcao = -1;
                }
                else
                {
                    brilho -= 10;
                    if(brilho == 0)
                        direcao = 1;
                }

                TIM_SetCompare1(TIM4, brilho);
            }
        }
    }
}


/* exercicio 5 */

void exercicio5(void)
{
    uint8_t contagem = 0;
    uint8_t cor = 0;

    TIM3_Toggle_Init();
    TIM4_PWM_Init();
    SetRGBColor(255, 0, 255); /* magenta */

    while(1)
    {
        if(AtualizarLED())
        {
            contagem++;

            /* muda de cor a cada 2 segundos */
            if(contagem == 4)
            {
                contagem = 0;
                cor++;
                if(cor == 4)
                    cor = 0;

                if(cor == 0) SetRGBColor(255, 0, 255); /* magenta */
                if(cor == 1) SetRGBColor(255, 0, 0);   /* vermelho */
                if(cor == 2) SetRGBColor(0, 255, 0);   /* verde */
                if(cor == 3) SetRGBColor(0, 0, 255);   /* azul */
            }
        }
    }
}


int main(void)
{
    RCC_Config_HSE_PLL_Max();
    LED_Init();
    TIM3_Init();

    /* descomentar apenas o exercicio pretendido */

    /* exercicio 1 */
    //exercicio1();

    /* exercicio 2 */
    //exercicio2();

    /* exercicio 3 */
    //exercicio3();

    /* exercicio 4 */
    exercicio4();

    /* exercicio 5 */
    //exercicio5();

    while(1);
}
