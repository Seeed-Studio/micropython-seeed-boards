import sys
import time

from boards.xiao import XiaoADC, XiaoI2C, XiaoPDM, XiaoPWM, XiaoPin


LED_PIN = "led"
BUTTON_PIN = "sw"
ADC_CHANNEL = 0
PWM_CHANNEL = 0
I2C_BUSES = (
    ("i2c0", "imu_sda", "imu_scl"),
    ("i2c1", "imu_sda", "imu_scl"),
)
PDM_DEVICE = "pdm0"
IMU_ADDR = 0x6A
IMU_WHO_AM_I_REG = 0x0F


def print_help():
    print("Commands:")
    print("  help                show this help")
    print("  info                show platform info")
    print("  led [count]         blink onboard LED")
    print("  button [seconds]    poll button state")
    print("  adc [count]         sample ADC channel 0")
    print("  pwm [seconds]       fade PWM channel 0")
    print("  i2c                 scan I2C buses")
    print("  imu                 read IMU WHO_AM_I if present")
    print("  pdm                 capture one PDM frame")
    print("  all                 run a short smoke test")
    print("  exit                stop receiver")


def read_command(prompt="test> "):
    sys.stdout.write(prompt)
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()
    line = sys.stdin.readline()
    if line is None:
        return ""
    return line.strip()


def test_info():
    print("machine:", sys.implementation._machine)
    print("platform:", sys.platform)
    print("version:", ".".join(str(v) for v in sys.implementation.version))


def test_led(count=3, delay=0.2):
    led = XiaoPin(LED_PIN, XiaoPin.OUT)
    print("Blinking LED", count, "times")
    for _ in range(count):
        led.value(0)
        time.sleep(delay)
        led.value(1)
        time.sleep(delay)
    led.value(1)
    print("LED test done")


def test_button(seconds=5):
    button = XiaoPin(BUTTON_PIN, XiaoPin.IN)
    print("Polling button for", seconds, "seconds")
    deadline = time.time() + seconds
    last = None
    while time.time() < deadline:
        value = button.value()
        if value != last:
            print("button:", "pressed" if value == 0 else "released")
            last = value
        time.sleep(0.05)
    print("Button test done")


def test_adc(count=10):
    adc = XiaoADC(ADC_CHANNEL)
    print("Sampling ADC channel", ADC_CHANNEL)
    for idx in range(count):
        value = adc.read_u16()
        print("adc[{0}] = {1}".format(idx, value))
        time.sleep(0.1)
    print("ADC test done")


def test_pwm(seconds=3):
    pwm = XiaoPWM(PWM_CHANNEL)
    pwm.init(freq=1000, duty_ns=20000)
    start = time.time()
    step = 0
    print("Running PWM fade for", seconds, "seconds")
    while time.time() - start < seconds:
        phase = step % 200
        level = phase if phase <= 100 else 200 - phase
        duty_ns = int(20000 + (level / 100.0) * 940000)
        pwm.duty_ns(duty_ns)
        time.sleep(0.02)
        step += 1
    pwm.deinit()
    print("PWM test done")


def _open_i2c(bus_name, sda_name, scl_name):
    return XiaoI2C(bus_name, sda_name, scl_name, 400000)


def test_i2c():
    for bus_name, sda_name, scl_name in I2C_BUSES:
        try:
            bus = _open_i2c(bus_name, sda_name, scl_name)
            devices = bus.scan()
            print("{0}: {1}".format(bus_name, [hex(addr) for addr in devices]))
        except Exception as exc:
            print("{0}: error: {1}".format(bus_name, exc))
    print("I2C test done")


def test_imu():
    for bus_name, sda_name, scl_name in I2C_BUSES:
        try:
            bus = _open_i2c(bus_name, sda_name, scl_name)
            devices = bus.scan()
            if IMU_ADDR not in devices:
                print("{0}: IMU not found".format(bus_name))
                continue
            who = bus.readfrom_mem(IMU_ADDR, IMU_WHO_AM_I_REG, 1)[0]
            print("{0}: IMU WHO_AM_I = 0x{1:02X}".format(bus_name, who))
            print("IMU test done")
            return
        except Exception as exc:
            print("{0}: error: {1}".format(bus_name, exc))
    print("IMU test done")


def test_pdm():
    try:
        pdm = XiaoPDM(PDM_DEVICE)
        pdm.configure(rate=16000, width=16, channels=1)
        pdm.start()
        time.sleep(0.2)
        data = pdm.read()
        pdm.stop()
        print("PDM bytes:", len(data))
    except Exception as exc:
        print("PDM error:", exc)
    print("PDM test done")


def test_all():
    test_info()
    test_led(2)
    test_button(2)
    test_adc(5)
    test_i2c()
    test_imu()


def parse_int(parts, index, default):
    if len(parts) > index:
        try:
            return int(parts[index])
        except Exception:
            pass
    return default


def main():
    print("XIAO test receiver ready")
    print_help()

    while True:
        try:
            line = read_command("test> ")
        except (EOFError, KeyboardInterrupt):
            print("\nreceiver stopped")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        try:
            if cmd == "help":
                print_help()
            elif cmd == "info":
                test_info()
            elif cmd == "led":
                test_led(parse_int(parts, 1, 3))
            elif cmd == "button":
                test_button(parse_int(parts, 1, 5))
            elif cmd == "adc":
                test_adc(parse_int(parts, 1, 10))
            elif cmd == "pwm":
                test_pwm(parse_int(parts, 1, 3))
            elif cmd == "i2c":
                test_i2c()
            elif cmd == "imu":
                test_imu()
            elif cmd == "pdm":
                test_pdm()
            elif cmd == "all":
                test_all()
            elif cmd == "exit":
                print("receiver stopped")
                break
            else:
                print("unknown command:", cmd)
                print_help()
        except Exception as exc:
            print("test failed:", exc)

        print("ready")


main()
