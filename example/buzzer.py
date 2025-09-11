import time
from boards.xiao import XiaoPin, XiaoPWM

buzzer = 3      #D3
button = "sw"

try:
    # Initialize the buzzer and button
    buzzer = XiaoPWM(buzzer) 
    button = XiaoPin(button, XiaoPin.IN)
    # set the frequency and period of the PWM signal
    FREQ = 1000             
    PERIOD_NS = 500000     
    # initialize the PWM with a frequency and a 0% duty cycle
    buzzer.init(freq=FREQ, duty_ns=0)
    while True:
        # check if the button is pressed and turn on the buzzer if it is
        if button.value() == 0:
            buzzer.duty_ns(PERIOD_NS)
        else:
            buzzer.duty_ns(0)  
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    buzzer.deinit()





