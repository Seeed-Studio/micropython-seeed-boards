import time 
from boards.xiao import XiaoRTC  #If you are using XIAO RA4M1, you must delete this line

rtc = XiaoRTC()

try:
    # Set the date and time to 2025-08-31 15:55:00
    rtc.set_datetime((2025, 8, 31, 15, 55, 0))
    while True:
        # Get the current date and time
        year, month, day, hour, minute, second = rtc.get_datetime()
        print("%04d-%02d-%02d %02d:%02d:%02d" % (year, month, day, hour, minute, second))
        time.sleep(1)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    print("\nCleaning up...")
    
    



