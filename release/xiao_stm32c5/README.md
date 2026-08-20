# XIAO STM32C5 MicroPython 使用指南

## 包装内容

| 路径 | 说明 |
|---|---|
| `firmware/micropython-xiao-stm32c5.uf2` | 固件镜像(刷这个) |
| `firmware/SHA256SUMS.txt` | 固件与全部脚本的完整性校验 |
| `tests/*.py` | 上板测试脚本(复制到板子文件系统后 import 运行) |

## 刷固件

1. 用可传数据的 USB 线连接板子。
2. **双击 Reset 按键** —— 会出现一个名为 `XIAOC5BOOT` 的 U 盘。
3. 把 `firmware/micropython-xiao-stm32c5.uf2` **直接拖进这个 U 盘**即可。

TinyUF2 处理完文件后板子自动重启进入 MicroPython。全程不需要任何
工具链、ST-Link 或 J-Link;引导程序本身不会被覆盖,万一刷了坏镜像,
重新双击 Reset 进引导模式,再拖一个已知好的 UF2 就能恢复。

## 连接 REPL(USB CDC)

REPL 走板载 USB 口的 CDC-ACM 虚拟串口,和刷固件是同一条线:

- Thonny:*运行 → 选择解释器 → MicroPython (generic)*,端口选刷完
  固件后新出现的串口(Windows `COMx`、Linux `/dev/ttyACM0`、
  macOS `/dev/tty.usbmodem*`),波特率随意(CDC 不看波特率)。
- 也可以用 `mpremote`、`rshell`、`screen /dev/ttyACM0`、PuTTY 等。

时钟同步:固件提供 `time.localtime()` 和 `machine.RTC()`,Thonny
连接时会静默同步时钟(不再有旧版的两条告警)。
`machine.RTC().datetime((y, m, d, wd, hh, mm, ss, 0))` 写入 LSE
硬件 RTC;`time.time()` / `time.localtime()` 从开机时刻起算。

## 运行测试

把需要的脚本复制到板子文件系统(Thonny 里右键文件 → *上传到 /*),
然后在 REPL 里:

```python
import xiao_stm32c5_full_test as t; t.main()   # 全项测试(含 CAN)
import xiao_stm32c5_base_test  as t; t.main()  # 外设测试(不含 CAN)
import xiao_stm32c5_can_test   as t; t.main()  # 9 项 FDCAN 回环测试
import xiao_stm32c5_spi_test   as t; t.main()  # SPI 回环(见下文接线)
```

`can_interconnect.py` 需要第二块板或 CAN 分析仪。板级助手 API
(`from boards.xiao import XiaoPin, XiaoADC, XiaoPWM, XiaoI2C,
XiaoSPI, XiaoUART`)已冻结进固件。

## SPI —— 硬件 SPI3

排针 SPI 是硬件 **SPI3**:D8 (PE2) = SCK、D9 (PB0) = MISO、
D10 (PB15) = MOSI。

```python
from boards.xiao import XiaoSPI
spi = XiaoSPI(0, 500000)   # 硬件 SPI3,模式 0,引脚由设备树固定
rx = bytearray(4)
spi.write_readinto(b"\x9f\x00\x00\x00", rx)   # 例:读 flash JEDEC-ID
```

`machine.SPI("spi3")` 也可直接使用。引脚由板级设备树固定,不支持
运行时改 SPI 引脚;片选(CS)用任意空闲 GPIO 驱动(如 `XiaoPin(1)`)。

`xiao_stm32c5_spi_test.py` 需要**杜邦线短接 D10 (MOSI) ↔ D9 (MISO)**,
在两种波特率下验证全部测试图案。

## 引脚表

| 排针 | GPIO | 功能 |
|---|---|---|
| D0–D3 | PA0–PA3 | ADC1_IN0–IN3 / GPIO |
| D4 / D5 | PB7 / PB6 | I2C1 SDA / SCL |
| D6 / D7 | PA9 / PA10 | USART1 TX / RX(备用串口 —— REPL 在 USB CDC) |
| D8 | PE2 | SPI3 SCK |
| D9 | PB0 | SPI3 MISO |
| D10 | PB15 | SPI3 MOSI |
| D11 / D12 | PB8 / PB9 | FDCAN1 RX / TX |
| D13 / D14 | PB5 / PB13 | FDCAN2 RX / TX |
| D15 | PB14 | CAN 收发器待机控制(高电平 = 待机) |

板载器件:用户 LED PB12(低电平点亮)、LSM6DS3TR-C 六轴 IMU(I2C2,
地址 `0x6A`)、16 MB 外部 NOR flash(MicroPython `/flash` 文件系统)、
电池电压检测 PA4/ADC1_IN4(使能引脚 BAT_EN = PA15)。

## 已知限制

- `time.time()` 从开机起算;墙上时钟保存在
  `machine.RTC().datetime()` 里。
- 在真机通过 `RELEASE_NOTES.md` 的确认清单之前,本包不算正式发布。
