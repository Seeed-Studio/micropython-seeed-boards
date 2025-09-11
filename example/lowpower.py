import time
import sys

if sys.platform != 'zephyr':
    raise Exception("This code can only run on Zephyr of Xiao series.")
else:
    from boards.xiao import XiaoLowPWR

# Create an instance of the LowPWR class
lowpwr = XiaoLowPWR()  
# Print the reason for the last reset
lowpwr.print_reset_cause()  
# Configure the wakeup pin to gpio0, with mode set to 0 (falling edge)
lowpwr.configure_wakeup_pin(("gpio0", 0))  
# Put the device into low power mode
print("Entering low power mode...") 
lowpwr.power_off()  



