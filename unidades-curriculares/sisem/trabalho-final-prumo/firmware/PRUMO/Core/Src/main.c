#include "app.h"
#include "board.h"
int main(void) {
    Board_Init();
    App_Init();
    for (;;) App_Task();
}
