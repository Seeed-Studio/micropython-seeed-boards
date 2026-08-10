# Freeze the XIAO STM32C5 helper modules into the firmware image (production firmware).
# Test scripts (xiao_stm32c5_base_test.py / xiao_stm32c5_can_test.py / can_interconnect.py)
# are NOT frozen -- upload them via Thonny / mpremote when testing is needed.
freeze("$(PORT_DIR)/modules", "_boot.py")
freeze("../example", (
    "boards/xiao.py",
    "boards/xiao_stm32c5.py",
))
