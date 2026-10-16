# Freeze the XIAO helper modules into the firmware image for the
# XIAO nRF54LM20A V2.0 (nRF54LM20A on the nRF54LM20B PCB).
#
# The XIAO connector pin map of the V2.0 board is identical to the V1.0
# board (seeed_xiao_connector.dtsi is shared), so the V1 pin tables apply
# unchanged; V2.0 differences (native USB CDC instead of the SAMD11
# bridge, LDO2 back pad, EX_RX/EX_TX back pads on uart20) do not need
# separate aliases.

# _boot.py mounts (and formats on first boot) the /flash filesystem; without
# it the upstream main.c performs no filesystem setup at all.
freeze("$(PORT_DIR)/modules", "_boot.py")
freeze("../example", ("boards/xiao.py", "boards/xiao_nrf54lm20a.py"))
