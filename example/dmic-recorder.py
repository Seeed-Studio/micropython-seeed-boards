import time
import sys

if "nrf54l15" in sys.implementation._machine:
    import ubinascii
    from boards.xiao import XiaoPin, XiaoPDM
    led = "led"  
    button = "sw"  
    en = "mic_en"
    pdm = "pdm0"
else:
    raise Exception("This code can only run on XIAO nRF54L15 Sence.")

def record_audio():
    # Configure PDM
    pdm.configure(
        rate=SAMPLE_RATE,
        width=SAMPLE_WIDTH,
        channels=CHANNELS,
        block_size=CHUNK_SIZE
    )
    
    # Print configuration using compatible format
    print("\n=== Starting Audio Recording ===")
    print("Configuration: %dHz, %d-bit, %s" % (SAMPLE_RATE, SAMPLE_WIDTH, 'Mono' if CHANNELS == 1 else 'Stereo'))
    print("Chunk size: %d bytes (%dms)" % (CHUNK_SIZE, CHUNK_DURATION_MS))
    print("Total recording time: %d seconds" % RECORD_TIME_S)
    print("Total chunks to capture: %d" % TOTAL_CHUNKS)
    
    # Start recording
    start_time = time.ticks_ms()
    
    # Record all chunks
    for i in range(TOTAL_CHUNKS):
        # Start PDM capture
        pdm.start()
        
        # Read one chunk of audio data
        data = pdm.read()
        
        # Calculate progress
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
        progress = min(100, (elapsed_ms / (RECORD_TIME_S * 1000)) * 100)
        
        # Print chunk summary using your specified format for the main line
        print("%d - got buffer of %d bytes" % (i+1, len(data)))  
        
        # Additional debug information with compatible formatting
        print("  Progress: %.1f%%" % progress)
        
        # Print entire data buffer as hex representation
        # if len(data) > 0:
        #     hex_data = ubinascii.hexlify(data).decode()
        #     print("  Hex data: %s" % hex_data)
        
        # Stop PDM capture
        pdm.stop()
    
    # Print completion message with compatible formatting
    total_bytes = TOTAL_CHUNKS * CHUNK_SIZE
    print("\n=== Recording Complete ===")
    print("Total data captured: %d bytes" % total_bytes)
    print("Equivalent to %.2f seconds of audio" % (total_bytes / (SAMPLE_RATE * BYTES_PER_SAMPLE)))

try:
    # Initialize hardware resources
    led = XiaoPin(led, XiaoPin.OUT) 
    button = XiaoPin(button, XiaoPin.IN) 
    en = XiaoPin(en, XiaoPin.OUT)  
    pdm = XiaoPDM(pdm)  
    # Audio configuration parameters
    SAMPLE_RATE = 16000  # 16kHz sampling rate
    SAMPLE_WIDTH = 16    # 16-bit sample width
    CHANNELS = 1         # Mono recording
    BYTES_PER_SAMPLE = 2 # 16-bit = 2 bytes
    CHUNK_DURATION_MS = 100  # Duration of each audio chunk in ms
    CHUNK_SIZE = (SAMPLE_RATE * BYTES_PER_SAMPLE * CHUNK_DURATION_MS) // 1000  # Bytes per chunk
    RECORD_TIME_S = 10   # Total recording time in seconds
    TOTAL_CHUNKS = (RECORD_TIME_S * 1000) // CHUNK_DURATION_MS  # Total chunks to record
    # Initialize LED state and enable PDM
    led.value(1)
    en.value(1)
    while True:
        # Check if button is pressed (active low)
        if button.value() == 0:
            led.value(0)
            record_audio()
            led.value(1)
            print("\nPress button to start another recording...")
            while button.value() == 1:
                time.sleep(0.1)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    led.value(1)
    en.value(0)

    
    


