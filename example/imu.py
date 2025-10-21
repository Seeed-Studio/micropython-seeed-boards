import time
import sys
import ubinascii

sda = "imu_sda"        
scl = "imu_scl"        
i2c = "i2c1"
en = "imu_en"
frq = 400000

if "nrf54l15" in sys.implementation._machine:
    from boards.xiao import XiaoPin, XiaoI2C
    i2c = XiaoI2C(i2c, sda, scl, frq)
elif "mg24" in sys.implementation._machine: 
    from boards.xiao import XiaoPin
    from boards.xiao_mg24 import xiao_mg24 as xiao
    from machine import SoftI2C, Pin
    i2c = SoftI2C(Pin(xiao.pin(scl)), Pin(xiao.pin(sda)))
else:
    raise Exception("This code can only run on XIAO nRF54L15 Sense and XIAO MG24 Sense.")

# --- LSM6DSO I2C address and register definitions ---
LSM6DSO_I2C_ADDR = 0x6A         # LSM6DSO I2C device address
LSM6DSO_REG_WHO_AM_I = 0x0F     # Identification register
LSM6DSO_VAL_WHO_AM_I = 0x6A     # Expected WHO_AM_I value
LSM6DSO_REG_CTRL1_XL = 0x10     # Accelerometer control register
LSM6DSO_REG_CTRL2_G = 0x11      # Gyroscope control register

# Accelerometer/gyroscope data output registers (low byte first)
LSM6DSO_REG_OUTX_L_XL = 0x28    # Accelerometer X axis low byte
LSM6DSO_REG_OUTX_L_G = 0x22     # Gyroscope X axis low byte

# Write a single byte to an LSM6DSO register via I2C
def lsm6dso_reg_write_byte(reg_addr, value):
    try:
        i2c.writeto_mem(LSM6DSO_I2C_ADDR, reg_addr, bytes([value]))
        return True
    except:
        return False

# Read a single byte from an LSM6DSO register via I2C
def lsm6dso_reg_read_byte(reg_addr):
    try:
        return i2c.readfrom_mem(LSM6DSO_I2C_ADDR, reg_addr, 1)[0]
    except:
        return None

# Read multiple consecutive bytes from LSM6DSO register via I2C
def lsm6dso_reg_read_bytes(reg_addr, length):
    try:
        return i2c.readfrom_mem(LSM6DSO_I2C_ADDR, reg_addr, length)
    except:
        return None

try:
    # Enable the LSM6DSO 
    en = XiaoPin(en, XiaoPin.OUT)  
    en.value(1) 
    # Initialize I2C bus and check if LSM6DSO is present
    i2c_addr = i2c.scan()
    if LSM6DSO_I2C_ADDR not in i2c_addr:
        raise Exception("LSM6DSO not found on I2C bus")
    else:
        print("LSM6DSO found on I2C bus: 0x{:02X}".format(LSM6DSO_I2C_ADDR))
    # Vify device ID
    who_am_i = lsm6dso_reg_read_byte(LSM6DSO_REG_WHO_AM_I)
    if who_am_i != LSM6DSO_VAL_WHO_AM_I:
        raise Exception("LSM6DSO WHO_AM_I mismatch: expected 0x{:02X}, got 0x{:02X}".format(LSM6DSO_VAL_WHO_AM_I, who_am_i))
    else:
        print("LSM6DSO WHO_AM_I check passed. ID: 0x{:02X}".format(LSM6DSO_VAL_WHO_AM_I))
    # Set accelerometer ODR (12.5 Hz) and 2g range (0x20)
    if not lsm6dso_reg_write_byte(LSM6DSO_REG_CTRL1_XL, 0x20):
        raise Exception("Failed to set CTRL1_XL register")
    # Set gyroscope ODR (12.5 Hz) and 250dps range (0x20)
    if not lsm6dso_reg_write_byte(LSM6DSO_REG_CTRL2_G, 0x20):
        raise Exception("Failed to set CTRL2_G register")
    print("LSM6DSO initialized successfully.")
    while True:
        # Read accelerometer and gyroscope data
        accel_data = lsm6dso_reg_read_bytes(LSM6DSO_REG_OUTX_L_XL, 6)
        if accel_data is None:
            print("Failed to read accelerometer data")
            continue
        gyro_data = lsm6dso_reg_read_bytes(LSM6DSO_REG_OUTX_L_G, 6)
        if gyro_data is None:
            print("Failed to read gyroscope data")
            continue
        # Convert raw data to signed integers
        accel_x = (accel_data[1] << 8) | accel_data[0]
        accel_y = (accel_data[3] << 8) | accel_data[2]
        accel_z = (accel_data[5] << 8) | accel_data[4]
        if accel_x > 32767: accel_x -= 65536
        if accel_y > 32767: accel_y -= 65536
        if accel_z > 32767: accel_z -= 65536
        # Convert raw data to signed integers
        gyro_x = (gyro_data[1] << 8) | gyro_data[0]
        gyro_y = (gyro_data[3] << 8) | gyro_data[2]
        gyro_z = (gyro_data[5] << 8) | gyro_data[4]
        if gyro_x > 32767: gyro_x -= 65536
        if gyro_y > 32767: gyro_y -= 65536
        if gyro_z > 32767: gyro_z -= 65536
        # Print data
        print("\nAccelerometer (mg): X={:>6} Y={:>6} Z={:>6}".format(accel_x, accel_y, accel_z))
        print("Gyroscope (mdps):   X={:>6} Y={:>6} Z={:>6}".format(gyro_x, gyro_y, gyro_z))
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    i2c.stop()
