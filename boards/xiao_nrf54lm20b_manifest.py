# Freeze the XIAO helper modules into the firmware image.
freeze("$(PORT_DIR)/modules", "_boot.py")
freeze("../example", ("boards/xiao.py", "boards/xiao_nrf54lm20b.py"))
