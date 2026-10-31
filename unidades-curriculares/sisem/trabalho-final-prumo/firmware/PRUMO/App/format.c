#include "format.h"

#include <math.h>
static void add(CsvBuffer *b, char c) {
    if (!b->ok) return;
    if (b->length + 1 >= b->capacity) {
        b->ok = false;
        return;
    }
    b->data[b->length++] = c;
    b->data[b->length] = 0;
}
static void digits(CsvBuffer *b, uint32_t value) {
    char rev[10];
    unsigned n = 0;
    do {
        rev[n++] = (char)('0' + value % 10);
        value /= 10;
    } while (value);
    while (n) add(b, rev[--n]);
}
void Csv_Init(CsvBuffer *b, char *data, size_t n) {
    b->data = data;
    b->capacity = n;
    b->length = 0;
    b->ok = n > 0;
    if (n) data[0] = 0;
}
void Csv_Unsigned(CsvBuffer *b, uint32_t value) {
    if (b->length) add(b, ',');
    digits(b, value);
}
void Csv_Signed(CsvBuffer *b, int32_t value) {
    if (b->length) add(b, ',');
    if (value < 0) {
        add(b, '-');
        digits(b, 0U - (uint32_t)value);
    } else
        digits(b, (uint32_t)value);
}
void Csv_End(CsvBuffer *b) {
    add(b, '\r');
    add(b, '\n');
}
void Format_Angle(char out[9], float angle) {
    unsigned n = (unsigned)lroundf(fminf(fabsf(angle), 180.0f) * 10.0f);
    unsigned p = 0;
    out[p++] = angle < -0.05f ? '-' : '+';
    if (n >= 1000) out[p++] = (char)('0' + n / 1000);
    out[p++] = (char)('0' + n / 100 % 10);
    out[p++] = (char)('0' + n / 10 % 10);
    out[p++] = '.';
    out[p++] = (char)('0' + n % 10);
    out[p++] = 'o';
    out[p] = 0;
}
