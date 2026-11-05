#include "mma8452q.h"

#include "prumo_config.h"

enum {
    MMA_REG_STATUS = 0x00,
    MMA_REG_OUT_X_MSB = 0x01,
    MMA_REG_WHO_AM_I = 0x0D,
    MMA_REG_XYZ_DATA_CFG = 0x0E,
    MMA_REG_CTRL1 = 0x2A,
    MMA_REG_CTRL2 = 0x2B,
    MMA_REG_CTRL4 = 0x2D,
    MMA_DEVICE_ID = 0x2A,
    MMA_STATUS_XYZ_READY = 0x08,
    MMA_CTRL1_ACTIVE = 0x01,
    MMA_CTRL1_50HZ_ACTIVE = 0x21
};
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
    HAL_StatusTypeDef ret = read_reg(MMA_REG_WHO_AM_I, id, 1);
    if (ret != HAL_OK) return ret;
    if (*id != MMA_DEVICE_ID) return HAL_ERROR;
    if ((ret = read_reg(MMA_REG_CTRL1, &ctrl, 1)) != HAL_OK) return ret;
    if ((ret = write_reg(MMA_REG_CTRL1, ctrl & ~MMA_CTRL1_ACTIVE)) != HAL_OK)
        return ret; /* standby */
    if ((ret = write_reg(MMA_REG_XYZ_DATA_CFG, 0x00)) != HAL_OK)
        return ret; /* +/-2g, no HPF */
    if ((ret = write_reg(MMA_REG_CTRL2, 0x00)) != HAL_OK) return ret; /* normal, no sleep */
    if ((ret = write_reg(MMA_REG_CTRL4, 0x00)) != HAL_OK) return ret; /* polling, no IRQ */
    return write_reg(MMA_REG_CTRL1, MMA_CTRL1_50HZ_ACTIVE); /* DR=100 -> 50 Hz, F_READ=0, ACTIVE=1 */
}
HAL_StatusTypeDef MMA_Read(MMA_Raw *raw) {
    uint8_t status, bytes[6];
    HAL_StatusTypeDef ret = read_reg(MMA_REG_STATUS, &status, 1);
    if (ret != HAL_OK) return ret;
    if (!(status & MMA_STATUS_XYZ_READY)) return HAL_BUSY;
    if ((ret = read_reg(MMA_REG_OUT_X_MSB, bytes, 6)) != HAL_OK) return ret;
    raw->x = MMA_Decode12(bytes[0], bytes[1]);
    raw->y = MMA_Decode12(bytes[2], bytes[3]);
    raw->z = MMA_Decode12(bytes[4], bytes[5]);
    return HAL_OK;
}
