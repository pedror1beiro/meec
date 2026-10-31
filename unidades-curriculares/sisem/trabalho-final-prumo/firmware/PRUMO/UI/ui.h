#ifndef PRUMO_UI_H
#define PRUMO_UI_H
#include <stdbool.h>
#include <stdint.h>
typedef struct {
    float x, y, tolerance;
    bool sensor_ok, valid, hold, relative, axes;
} UiFrame;
void UI_Request(const UiFrame *frame);
bool UI_Task(void); /* at most 8 rows / 2 KiB per call */
extern uint32_t ui_frames;
#endif
