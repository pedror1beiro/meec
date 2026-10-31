#ifndef PRUMO_FORMAT_H
#define PRUMO_FORMAT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef struct {
    char *data;
    size_t capacity, length;
    bool ok;
} CsvBuffer;
void Csv_Init(CsvBuffer *b, char *data, size_t capacity);
void Csv_Unsigned(CsvBuffer *b, uint32_t value);
void Csv_Signed(CsvBuffer *b, int32_t value);
void Csv_End(CsvBuffer *b);
void Format_Angle(char out[9], float angle);
#endif
