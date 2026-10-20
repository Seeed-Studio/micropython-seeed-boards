# XIAO nRF54LM20A (V2.0) test script

The tests run over the application firmware's USB CDC ACM REPL. First flash
`firmware/zephyr.signed.bin` from this package, connect to the application
CDC (`2886:8068`), then run `xiao_nrf54lm20a_v2_full_test.py` from this
directory.

`boards.xiao` and `boards.xiao_nrf54lm20a` are frozen into the firmware;
there is no need (and it will not work) to upload those helper sources to
the filesystem. With Thonny, simply open and run
`xiao_nrf54lm20a_v2_full_test.py`. With mpremote or similar tools, upload
only the test script to the filesystem.

Start the test console from the normal `>>>` REPL:

```python
import xiao_nrf54lm20a_v2_full_test as test
test.main()
```

The test commands (`help`, `all`, `adc`, `pwm`, `i2c`, `imu`, `uart`,
`battery`, `ble`, `pdm`, `led`, `exit`) are only available after the
`XIAO nRF54LM20A V2 test>` prompt appears. Typing `help` at the plain REPL
only gives the built-in Python help function.

Tests report SKIP when no jumper or peripheral is attached — a SKIP does
not mean the firmware failed to start. The UART test needs TX P1.8 wired
to RX P1.9 for loopback; the IMU uses P0.08/P0.07. The RGB LED is
common-anode, active-low. Battery voltage is read from the nPM1300 fuel
gauge (the `battery` command); do not interpret any ADC channel as VBAT.

If uploading a file returns `OSError: [Errno 19] ENODEV`, initialize the
LittleFS filesystem once as described in the firmware notes; formatting
erases the files on the filesystem.
