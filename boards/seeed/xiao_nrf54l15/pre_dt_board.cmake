# SPDX-License-Identifier: Apache-2.0
# Suppress "unique_unit_address_if_enabled" to handle some overlaps
list(APPEND EXTRA_DTC_FLAGS "-Wno-unique_unit_address_if_enabled")
set(USER_C_MODULES 
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modadc"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modlowpwr"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modpdm"
    "${CMAKE_CURRENT_LIST_DIR}/../../../src/cmodules/modrtc"
)