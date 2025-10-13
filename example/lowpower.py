import time
import sys

if "nrf54l15" in sys.implementation._machine:
    from boards.xiao import XiaoLowPWR
else:
    raise Exception("This code can only run on XIAO nRF54L15.")

# Create an instance of the LowPWR class
lowpwr = XiaoLowPWR()  
# Print the reason for the last reset
lowpwr.print_reset_cause()  
# Configure the wakeup pin to gpio0, with mode set to 0 (falling edge)
lowpwr.configure_wakeup_pin(("gpio0", 0))  
# Put the device into low power mode
print("Entering low power mode...") 
lowpwr.power_off()  



