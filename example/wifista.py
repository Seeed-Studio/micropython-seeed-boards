import network
import time
import sys

if sys.platform != 'esp32':
    raise Exception("This code can only run on ESP32 of Xiao series.")

WIFI_SSID = 'SEEED-HA_2.4G'         # WiFi SSID
WIFI_PASSWORD = 'Seeedhome2023'     # WiFi password

# Initialize WiFi module
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Connect to WiFi
if wlan.isconnected():
    print("WiFi connected successfully")
    print(f"IP address: {wlan.ifconfig()[0]}")
else:
    print(f"Connecting to {WIFI_SSID}...")
    
    wlan.disconnect()
    time.sleep(1)  
    
    try:
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    except Exception as e:
        print(f"Connection error: {e}")
        raise
    
    # Wait for connection
    timeout = 15
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        print(f"Waiting... {timeout}s left")
    
    # Check connection
    if wlan.isconnected():
        print("WiFi connected successfully")
        print(f"IP address: {wlan.ifconfig()[0]}")
    else:
        print("Failed to connect to WiFi")
        status = wlan.status()
        if status == network.STAT_IDLE:
            print("Status: Idle")
        elif status == network.STAT_CONNECTING:
            print("Status: Still connecting")
        elif status == network.STAT_WRONG_PASSWORD:
            print("Status: Wrong password")
        elif status == network.STAT_NO_AP_FOUND:
            print("Status: AP not found")
        elif status == network.STAT_CONNECT_FAIL:
            print("Status: Connection failed")
        else:
            print(f"Unknown status: {status}")

