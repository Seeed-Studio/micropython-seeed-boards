# XIAO nRF54LM20B 测试脚本

测试通过应用固件的 USB CDC ACM REPL 执行。先烧录包内的
`firmware/zephyr.signed.bin`，连接应用 CDC（`2886:8013`），再将本目录的
`xiao.py`、`xiao_nrf54lm20b.py` 和 `xiao_nrf54lm20b_full_test.py` 上传到板上。

在普通 `>>>` REPL 中启动测试台：

```python
import xiao_nrf54lm20b_full_test as test
test.main()
```

只有出现 `XIAO nRF54LM20B test>` 后，`help`、`all`、`adc`、`pwm`、`i2c`、
`imu`、`uart`、`battery`、`ble`、`pdm`、`led` 和 `exit` 才是测试命令。
普通 REPL 中输入 `help` 只会得到 Python 内建帮助函数。

没有接入跳线或外设的项目会显示 `SKIP`，不代表固件启动失败。UART 回环需
将 TX P1.8 接 RX P1.9；IMU 使用 P0.08/P0.07。RGB LED 为共阳极、低电平有效。

如果上传文件返回 `OSError: [Errno 19] ENODEV`，先按固件说明初始化一次
LittleFS；格式化会清除文件系统中的文件。
