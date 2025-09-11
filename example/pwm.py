import time
from boards.xiao import XiaoPWM

led = 1   #D1

try:
    # set the frequency and period of the PWM signal
    FREQ = 1000             
    PERIOD_NS = 1000000     
    # set the number of steps to fade the LED and the delay between steps
    FADE_STEPS = 255        
    STEP_DELAY = 0.01       
    STEP_SIZE = 3           
    # initialize the PWM with a frequency and a 0% duty cycle
    led = XiaoPWM(led) 
    led.init(freq=FREQ, duty_ns=0)
    while True:
        # fade the LED in and out
        for fade in range(0, FADE_STEPS + 1, STEP_SIZE):
            duty_time = int((fade * PERIOD_NS) / FADE_STEPS)
            led.duty_ns(duty_time)
            time.sleep(STEP_DELAY)
        # fade the LED in and out again
        for fade in range(FADE_STEPS, -1, -STEP_SIZE):
            duty_time = int((fade * PERIOD_NS) / FADE_STEPS)
            led.duty_ns(duty_time)
            time.sleep(STEP_DELAY)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    led.deinit()




