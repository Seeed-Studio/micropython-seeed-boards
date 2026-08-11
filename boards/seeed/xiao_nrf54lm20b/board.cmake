# Copyright (c) 2025 Seeed Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

if(CONFIG_SOC_NRF54LM20B_CPUAPP)
  board_runner_args(openocd "--cmd-load=nrf54lm20b-load" -c "targets nrf54lm20b.cpu")
  board_runner_args(jlink "--device=cortex-m33" "--speed=4000")
elseif(CONFIG_SOC_NRF54LM20B_CPUFLPR)
  board_runner_args(openocd "--cmd-load=nrf54lm20b-load" -c "targets nrf54lm20b.aux")
  board_runner_args(jlink "--speed=4000")
endif()

include(${ZEPHYR_BASE}/boards/common/openocd.board.cmake)
include(${ZEPHYR_BASE}/boards/common/nrfutil.board.cmake)
include(${ZEPHYR_BASE}/boards/common/jlink.board.cmake)
