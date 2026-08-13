import sys
import time
from boards.xiao import XiaoPin, XiaoADC, XiaoPWM

adc = 0    #D0
pwm_num = 0 if "stm32c5" in sys.implementation._machine.lower() else 1
adc_obj = None
pwm_obj = None
pwm_ready = False

try:
    # Initialize ADC for potentiometer
    adc_obj = XiaoADC(adc)
    # Initialize PWM for LED control
    pwm_obj = XiaoPWM(pwm_num)
    FREQ = 1000
    PERIOD_NS = 1000000
    pwm_obj.init(freq=FREQ, duty_u16=0)
    pwm_ready = True
    # Potentiometer parameters
    MIN_VOLTAGE = 0.0      
    MAX_VOLTAGE = 3.3     
    DEAD_ZONE = 0.05   
    last_duty = -1 
    while True:
        # Read ADC voltage value
        voltage = adc_obj.read_u16() / 10000
        
        # Ensure voltage is within valid range
        if voltage < MIN_VOLTAGE:
            voltage = MIN_VOLTAGE
        elif voltage > MAX_VOLTAGE:
            voltage = MAX_VOLTAGE
        
        duty_percent = (voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE)
        
        # Apply dead zone to prevent tiny fluctuations
        if abs(duty_percent - last_duty) < DEAD_ZONE / 100:
            time.sleep(0.05)
            continue
        
        # Calculate duty cycle time (nanoseconds)
        duty_ns = int(duty_percent * PERIOD_NS)
        if duty_ns < 20:
            duty_ns = 20
        elif duty_ns > 960000:
            duty_ns = 960000
            
        # Set PWM duty cycle
        pwm_obj.duty_ns(duty_ns)
        
        # Print current status
        print("Voltage: {:.2f}V, Duty Cycle: {:.1f}%".format(voltage, duty_percent * 100))
        
        # Update last duty cycle value
        last_duty = duty_percent
        
        # Short delay
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    if pwm_ready:
        try:
            pwm_obj.deinit()
        except Exception:
            pass
    

  


