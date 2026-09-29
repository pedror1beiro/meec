/**
 ******************************************************************************
 * @file    main.c
 * @author  3S0
 * @version V1.0
 * @date    24/09/2024
 * @brief   Default main function.
 ******************************************************************************
 */

#include "stm32f10x.h"


/* funcao atraso por software */
void delay(uint32_t tempo)
{
    volatile uint32_t i;

    for(i = 0; i < tempo; i++);
}


/* exercicio 3 */

void exercicio3(void)
{
    /* ativa o clock do GPIOA */
    RCC->APB2ENR = 0x00000004;

    /* PA5 como saida push-pull 50 MHz */
    GPIOA->CRL = 0x00300000;
    GPIOA->CRH = 0x00000000;

    while(1)
    {
        /* liga o LED */
        GPIOA->BSRR = 0x00000020;
        delay(1000000);

        /* desliga o LED */
        GPIOA->BSRR = 0x00200000;
        delay(1000000);
    }
}


/* exercicio 4 */

void exercicio4(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    /* ativa o clock do GPIOA */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    /* configura PA5 como saida push-pull 50 MHz */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOA, &GPIO_InitStructure);

    while(1)
    {
        /* liga o LED */
        GPIO_SetBits(GPIOA, GPIO_Pin_5);
        delay(1000000);

        /* desliga o LED */
        GPIO_ResetBits(GPIOA, GPIO_Pin_5);
        delay(1000000);
    }
}


/* exercicio 5 */

void exercicio5(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    /* ativa os clocks do GPIOA e GPIOC */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA |
                           RCC_APB2Periph_GPIOC, ENABLE);

    /* configura PA5 como saida */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;

    GPIO_Init(GPIOA, &GPIO_InitStructure);

    /* configura PC13 como entrada para o botao */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;

    GPIO_Init(GPIOC, &GPIO_InitStructure);

    while(1)
    {
        GPIO_SetBits(GPIOA, GPIO_Pin_5);

        /* botao pressionado: reduz o atraso para metade */
        if(GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_13) == 0)
            delay(500000);
        else
            delay(1000000);

        GPIO_ResetBits(GPIOA, GPIO_Pin_5);

        if(GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_13) == 0)
            delay(500000);
        else
            delay(1000000);
    }
}


int main(void)
{
    /* descomentar/comentar exercicio que se pretende executar */
    //exercicio3();
    //exercicio4();
    exercicio5();

    while(1);
}
