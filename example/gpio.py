import time
from boards.xiao import XiaoPin  #If you are using XIAO RA4M1, you must delete this line

button = "sw"
relay = 0       #D0

try:
    # Initialize button and relay
    button = XiaoPin(button, XiaoPin.IN)
    relay = XiaoPin(relay, XiaoPin.OUT)
    relay.value(0)
    while True:
        # Read button state 
        button_state = button.value()
        
        # Control relay based on button state
        if button_state == 0:       
            relay.value(1)         
        else:                      
            relay.value(0)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    relay.off()




