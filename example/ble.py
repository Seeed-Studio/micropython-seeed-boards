import bluetooth
from boards.xiao import XiaoPin  #If you are using XIAO RA4M1, you must delete this line

led = "led"
device_name = "xiao"

# Bluetooth event constants
_IRQ_CENTRAL_CONNECT = 1      # Event when central device connects
_IRQ_CENTRAL_DISCONNECT = 2   # Event when central device disconnects
_IRQ_GATTS_WRITE = 3          # Event when central writes to characteristic

# Define UUIDs for our service and characteristics
ONOFF_SERVICE_UUID = bluetooth.UUID("8e7f1a23-4b2c-11ee-be56-0242ac120002")
ONOFF_ACTION_UUID = bluetooth.UUID("8e7f1a24-4b2c-11ee-be56-0242ac120002")
ONOFF_READ_UUID = bluetooth.UUID("8e7f1a25-4b2c-11ee-be56-0242ac120003")

# Build advertising payload:
# 1. Flags (LE General Discoverable Mode)
# 2. Complete device name
adv_payload = bytearray()
adv_payload.extend(bytes([0x02, 0x01, 0x06]))  # Flags (length, type, value)
adv_payload.extend(bytes([len(device_name) + 1, 0x09]))  # Name header
adv_payload.extend(device_name.encode('utf-8'))  # Name value

# State variable for the switch
onoff_flag = 0

# Define our GATT service structure
onoff_service = (
    (ONOFF_SERVICE_UUID, (
        (ONOFF_ACTION_UUID, bluetooth.FLAG_WRITE),  # Writable characteristic
        (ONOFF_READ_UUID, bluetooth.FLAG_READ),     # Readable characteristic
    )),
)

# BLE event callback handler
def ble_irq(event, data):
    global onoff_flag
    if event == _IRQ_CENTRAL_CONNECT:
        led.value(0)
        print("Device connected")
    elif event == _IRQ_CENTRAL_DISCONNECT:
        print("Device disconnected")
        print("Restarting advertising")
        led.value(1)
        ble.gap_advertise(100000, adv_payload)  # Restart advertising
    elif event == _IRQ_GATTS_WRITE:
        # Handle write to our characteristic
        _, attr_handle = data
        value = ble.gatts_read(attr_handle)
        if attr_handle == onoff_action_handle:
            if value == b'\x00':
                onoff_flag = 0
            elif value == b'\x01':
                onoff_flag = 1
            # Update the read characteristic with new state
            ble.gatts_write(onoff_read_handle, bytes([onoff_flag]))

try:
    # Initialize BLE interface
    ble = bluetooth.BLE()
    ble.active(True)  # Activate BLE radio
    # Initialize LED pin
    led = XiaoPin(led, XiaoPin.OUT)
    led.value(1)  # Turn off LED to indicate advertising
    # Register callback and services
    ble.irq(ble_irq)
    ((onoff_action_handle, onoff_read_handle),) = ble.gatts_register_services(onoff_service)
    ble.gatts_write(onoff_read_handle, bytes([onoff_flag]))  # Initialize characteristic value
    # Start advertising (interval=100ms)
    ble.gap_advertise(None)
    ble.gap_advertise(100000, adv_payload)
    print("Start advertising")
    while True:
        pass
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % e)
finally:
    ble.active(False)
