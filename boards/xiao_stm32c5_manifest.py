# Freeze the XIAO STM32C5 helper modules and test script.
freeze("../example", (
    "boards/xiao.py",
    "boards/xiao_stm32c5.py",
    "xiao_stm32c5_full_test.py",
    "can_debug.py",
    "can_interconnect.py",
))

