import time
from boards.xiao import XiaoPin, XiaoADC, XiaoPWM  #If you are using XIAO RA4M1, you must delete this line

adc = 0    #D0
pwm = 1    #D1

try:
    # Initialize ADC for potentiometer
    adc = XiaoADC(adc)            
    # Initialize PWM for LED control
    pwm = XiaoPWM(pwm)     
    FREQ = 1000                     
    PERIOD_NS = 1000000             
    pwm.init(freq=FREQ, duty_ns=0)  
    # Potentiometer parameters
    MIN_VOLTAGE = 0.0      
    MAX_VOLTAGE = 3.3     
    DEAD_ZONE = 0.05   
    last_duty = -1 
    while True:
        # Read ADC voltage value
        voltage = adc.read_uv() / 1000000  
        
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
        
        # Set PWM duty cycle
        pwm.duty_ns(duty_ns)
        
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
    pwm.deinit()
    

  


