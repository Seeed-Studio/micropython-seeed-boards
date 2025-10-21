import time  
from boards.xiao import XiaoPin, XiaoADC  #If you are using XIAO RA4M1, you must delete this line

adc = "vbat"
en = "vbat_en"        

try:
    # Enable vbat
    en = XiaoPin(en, XiaoPin.OUT)  
    en.value(1) 
    # Create an ADC object on the ADC pin
    adc = XiaoADC(adc)  
    while True:
        # Read the battery voltage in microvolts and convert to volts
        vbat = adc.read_uv() / 1000000  
        print("Battery Voltage: {:.4f} V".format(vbat)) 
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    en.value(0)
    


