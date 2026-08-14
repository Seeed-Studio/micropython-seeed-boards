# SPDX-License-Identifier: Apache-2.0

# The XIAO nRF54LM20B board uses MicroPython native C modules for the
# board-facing ADC, PDM, low-power, and RTC APIs exposed by boards/xiao.py.
list(APPEND EXTRA_DTC_FLAGS "-Wno-unique_unit_address_if_enabled")

set(USER_C_MODULES
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modadc"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modlowpwr"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modpdm"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modrtc"
)
