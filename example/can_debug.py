# CAN debug test script
import sys

print("=== CAN Debug Test ===")

# Step 1: Try device_get_binding("fdcan2")
print("\n--- Step 1: zephyr_device_find ---")
from CAN import CAN
try:
    can = CAN("fdcan2", loopback=True)
    print("zephyr_device_find: OK")
    print("CAN device found and started")

    # Try send/recv
    payload = bytes((0xC5, 0x01, 0x02, 0x03))
    can.send(0x123, payload)
    print("send: OK")

    frame = can.recv(500)
    if frame is None:
        print("recv: timeout (no loopback)")
    else:
        print("recv: OK, id=0x%03X data=%s" % (frame[0], frame[1]))

    can.deinit()
    print("deinit: OK")
except Exception as e:
    sys.print_exception(e)

# Step 2: Try with "can@4000a800" (old name)
print("\n--- Step 2: try old name ---")
try:
    can = CAN("can@4000a800", loopback=True)
    print("can@4000a800: OK")
    can.deinit()
except Exception as e:
    sys.print_exception(e)

# Step 3: Try with "can0" (DT alias)
print("\n--- Step 3: try DT alias ---")
try:
    can = CAN("can0", loopback=True)
    print("can0: OK")
    can.deinit()
except Exception as e:
    sys.print_exception(e)

print("\n=== Done ===")