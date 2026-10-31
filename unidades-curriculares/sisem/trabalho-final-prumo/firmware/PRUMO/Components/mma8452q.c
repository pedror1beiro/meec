#include "mma8452q.h"

#include "prumo_config.h"
static HAL_StatusTypeDef read_reg(uint8_t reg, uint8_t *v, uint16_t n) {
    return HAL_I2C_Mem_Read(&hi2c2, PRUMO_MMA_ADDR7 << 1, reg, I2C_MEMADD_SIZE_8BIT, v, n,
                            PRUMO_I2C_TIMEOUT_MS);
}
static HAL_StatusTypeDef write_reg(uint8_t reg, uint8_t v) {
    return HAL_I2C_Mem_Write(&hi2c2, PRUMO_MMA_ADDR7 << 1, reg, I2C_MEMADD_SIZE_8BIT, &v, 1,
                             PRUMO_I2C_TIMEOUT_MS);
}
HAL_StatusTypeDef MMA_Init(uint8_t *id) {
    uint8_t ctrl;
    *id = 0;
    HAL_StatusTypeDef ret = read_reg(0x0D, id, 1);
    if (ret != HAL_OK) return ret;
    if (*id != 0x2A) return HAL_ERROR;
    if ((ret = read_reg(0x2A, &ctrl, 1)) != HAL_OK) return ret;
    if ((ret = write_reg(0x2A, ctrl & 0xFEU)) != HAL_OK) return ret; /* standby */
    if ((ret = write_reg(0x0E, 0x00)) != HAL_OK) return ret;         /* +/-2g, no HPF */
    if ((ret = write_reg(0x2B, 0x00)) != HAL_OK) return ret;         /* normal, no sleep */
    if ((ret = write_reg(0x2D, 0x00)) != HAL_OK) return ret;         /* polling, no IRQ */
    return write_reg(0x2A, 0x21); /* DR=100 -> 50 Hz, F_READ=0, ACTIVE=1 */
}
HAL_StatusTypeDef MMA_Read(MMA_Raw *raw) {
    uint8_t status, bytes[6];
    HAL_StatusTypeDef ret = read_reg(0x00, &status, 1);
    if (ret != HAL_OK) return ret;
    if (!(status & 0x08U)) return HAL_BUSY;
    if ((ret = read_reg(0x01, bytes, 6)) != HAL_OK) return ret;
    raw->x = MMA_Decode12(bytes[0], bytes[1]);
    raw->y = MMA_Decode12(bytes[2], bytes[3]);
    raw->z = MMA_Decode12(bytes[4], bytes[5]);
    return HAL_OK;
}
