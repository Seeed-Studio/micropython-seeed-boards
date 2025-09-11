import network
import time
import sys

if sys.platform != 'esp32':
    raise Exception("This code can only run on ESP32 of Xiao series.")

AP_SSID = 'XIAO'            # WiFi AP SSID
AP_PASSWORD = '132456798'   # WiFi AP password
AP_MAX_CLIENTS = 10         # Maximum number of clients that can connect to the AP

# Start WiFi AP
ap = network.WLAN(network.AP_IF)

# Configure AP settings
ap.config(ssid=AP_SSID, password=AP_PASSWORD, max_clients=AP_MAX_CLIENTS)
ap.active(True)

# Wait for AP to start
time.sleep(2)
if ap.active():
    print(f"AP started: {AP_SSID}")
    print(f"AP IP: {ap.ifconfig()[0]}")
else:
    print("Failed to start AP")
    
    



    