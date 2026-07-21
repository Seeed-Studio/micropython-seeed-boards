# Zephyr Driver Patches

These patches fix issues in the pinned Zephyr 4.4.0 framework that are needed
for XIAO STM32C5 (HAL2) support. Patches are applied in filename order and are
idempotent.

## When to remove a patch

| Patch | Needed until | Upstream status |
|---|---|---|
| 0001-udc-stm32 | Zephyr >= 4.5 | Merged to main (post-4.4.0) |
| 0002-flash-stm32-xspi | Zephyr >= 4.5 (TBD) | Not yet in main |
| 0003-adc-stm32-pcsel | Zephyr >= 4.5 | Fix from platform-seeedboards |

Upstream Zephyr commit references (when available):
- udc_stm32 HAL2: zephyrproject-rtos/zephyr PR #105957
- flash_stm32_xspi HAL2: pending upstream
- adc_stm32 PCSEL: cumin777/platform-seeedboards commit f24a031