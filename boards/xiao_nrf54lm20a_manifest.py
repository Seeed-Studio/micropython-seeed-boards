# Freeze the XIAO helper modules from this repository into the firmware image.
# This keeps lib/micropython aligned with upstream while still shipping
# board-specific Python helpers out of the box on XIAO nRF54LM20A builds.

freeze("../example", ("boards/xiao.py", "boards/xiao_nrf54lm20a.py"))
