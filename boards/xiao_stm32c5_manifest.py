# Freeze the XIAO STM32C5 helper modules (production firmware).
# Test scripts are NOT frozen — upload them via Thonny when needed.
freeze("$(PORT_DIR)/modules", "_boot.py")
freeze("../example", (
    "boards/xiao.py",
    "boards/xiao_stm32c5.py",
))
