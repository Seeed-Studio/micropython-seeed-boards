# Freeze the XIAO STM32C5 helper modules into the firmware image (production firmware).
# Test scripts (xiao_stm32c5_base_test.py / xiao_stm32c5_can_test.py / can_interconnect.py)
# are NOT frozen -- upload them via Thonny / mpremote when testing is needed.
# micropython's frozen _boot.py is intentionally NOT frozen: v1.27.0 auto-runs it
# on boot (ports/zephyr/main.c: pyexec_frozen_module("_boot.py")) and its storage
# init hangs on this board, blocking the REPL. Storage auto-mount disabled until fixed.
freeze("../example", (
    "boards/xiao.py",
    "boards/xiao_stm32c5.py",
))
