from boards.xiao import XiaoPin  #If you are using XIAO RA4M1, you must delete this line

button = "sw"
led = "led"

try:
    # Initialize the button and LED
    button = XiaoPin(button, XiaoPin.IN)
    led = XiaoPin(led, XiaoPin.OUT)
    while True:
        # Check if the button is pressed and turn on the LED if it is
        if button.value() == 0:
            led.value(0)    
        else:
            led.value(1)   
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    led.value(1)



        

