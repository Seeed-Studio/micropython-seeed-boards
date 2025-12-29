import time
from boards.xiao import XiaoPin, XiaoSPI  

# GDEY0213F51 2.13" 4-color ePaper Display Driver
# Screen Resolution: 128x250 pixels (2-bit per pixel for 4 colors)

# Pin configuration (same as epaper.py)
RST = 0                     # D0
CS = 1                      # D1
DC = 3                      # D3
BUSY = 5                    # D5
sck = 9                     # D9
mosi = 10                   # D10
miso = 8                    # D8
spi = "spi0"

# Screen parameters
SOURCE_BITS = 128
GATE_BITS = 250
ALLSCREEN_BYTES = SOURCE_BITS * GATE_BITS // 4  # 2-bit per pixel = 4 pixels per byte

# Color definitions (2-bit)
BLACK = 0x00   # 00
WHITE = 0x01   # 01
YELLOW = 0x02  # 10
RED = 0x03     # 11

# Hardware configuration
RST = XiaoPin(RST, XiaoPin.OUT)
CS = XiaoPin(CS, XiaoPin.OUT)
DC = XiaoPin(DC, XiaoPin.OUT)
BUSY = XiaoPin(BUSY, XiaoPin.IN, XiaoPin.PULL_UP)
spi = XiaoSPI(spi, 10000000, sck, mosi, miso)

# Reset the display
def reset():
    RST.value(0)
    time.sleep_ms(40)  # At least 40ms delay
    RST.value(1)
    time.sleep_ms(50)  # At least 50ms delay

# Send command
def send_command(command):
    DC.value(0)
    CS.value(0)
    spi.write(bytearray([command]))
    CS.value(1)

# Send data
def send_data(data):
    DC.value(1)
    CS.value(0)
    if isinstance(data, int):
        spi.write(bytearray([data]))
    else:
        spi.write(data)
    CS.value(1)

# Wait until the display is idle (BUSY=1 means idle)
def wait_until_idle():
    # while BUSY.value() == 0:  # Wait while BUSY is LOW
    time.sleep_ms(1)

# Simple 8x8 font for ASCII characters (32-127)
FONT_8X8 = {
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F, 0x00, 0x00, 0x00],
    'e': [0x38, 0x54, 0x54, 0x54, 0x18, 0x00, 0x00, 0x00],
    'l': [0x00, 0x41, 0x7F, 0x40, 0x00, 0x00, 0x00, 0x00],
    'o': [0x38, 0x44, 0x44, 0x44, 0x38, 0x00, 0x00, 0x00],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    'W': [0x7F, 0x20, 0x18, 0x20, 0x7F, 0x00, 0x00, 0x00],
    'r': [0x7C, 0x08, 0x04, 0x04, 0x08, 0x00, 0x00, 0x00],
    'd': [0x38, 0x44, 0x44, 0x48, 0x7F, 0x00, 0x00, 0x00],
}

# Set a pixel in the frame buffer with the given color (2-bit)
def set_pixel_in_buffer(buffer, x, y, color):
    if x < 0 or x >= SOURCE_BITS or y < 0 or y >= GATE_BITS:
        return
    
    byte_index = (y * SOURCE_BITS + x) // 4
    pixel_pos = (y * SOURCE_BITS + x) % 4
    shift = (3 - pixel_pos) * 2
    
    # Clear the 2 bits for this pixel
    buffer[byte_index] &= ~(0x03 << shift)
    # Set the new color
    buffer[byte_index] |= (color & 0x03) << shift

# Draw a character at position (x, y) with the given color
def draw_char(buffer, x, y, char, color):
    if char not in FONT_8X8:
        return x + 8
    
    font_data = FONT_8X8[char]
    for row in range(8):
        byte_data = font_data[row]
        for col in range(8):
            if byte_data & (0x80 >> col):
                set_pixel_in_buffer(buffer, x + (7 - col), (GATE_BITS - 1) - (y + row), color)
    
    return x + 8  # Return next x position

# Draw text string at position (x, y) with the given color
def draw_text(buffer, x, y, text, color):
    current_y = y 
    for char in text:
        draw_char(buffer, x, current_y, char, color)
        current_y += 8 
    return current_y

# Initialize the display (based on Arduino EPD_init)
def init_display():
    time.sleep_ms(20)  # At least 20ms delay
    reset()
    
    wait_until_idle()
    
    send_command(0x4D)
    send_data(0x78)
    
    send_command(0x00)  # PSR
    send_data(0x0F)
    send_data(0x29)
    
    send_command(0x01)  # PWRR
    send_data(0x07)
    send_data(0x00)
    
    send_command(0x03)  # POFS
    send_data(0x10)
    send_data(0x54)
    send_data(0x44)
    
    send_command(0x06)  # BTST_P
    send_data(0x05)
    send_data(0x00)
    send_data(0x3F)
    send_data(0x0A)
    send_data(0x25)
    send_data(0x12)
    send_data(0x1A)
    
    send_command(0x50)  # CDI
    send_data(0x37)
    
    send_command(0x60)  # TCON
    send_data(0x02)
    send_data(0x02)
    
    send_command(0x61)  # TRES (Resolution)
    send_data(SOURCE_BITS >> 8)    # Source_BITS_H
    send_data(SOURCE_BITS & 0xFF)  # Source_BITS_L
    send_data(GATE_BITS >> 8)      # Gate_BITS_H
    send_data(GATE_BITS & 0xFF)    # Gate_BITS_L
    
    send_command(0xE7)
    send_data(0x1C)
    
    send_command(0xE3)
    send_data(0x22)
    
    send_command(0xB4)
    send_data(0xD0)
    
    send_command(0xB5)
    send_data(0x03)
    
    send_command(0xE9)
    send_data(0x01)
    
    send_command(0x30)
    send_data(0x08)
    
    send_command(0x04)  # Power on
    wait_until_idle()

# Refresh display
def refresh():
    send_command(0x12)  # Display Update Control
    send_data(0x00)
    wait_until_idle()

# Clear screen to white
def clear_screen_white():
    send_command(0x10)  # Write to RAM
    
    # For 4-color display, white = 0x01 (01 in binary)
    # 4 pixels per byte: 0x55 = 01010101 = white, white, white, white
    white_byte = 0x55
    
    for i in range(ALLSCREEN_BYTES):
        send_data(white_byte)
    
    # Refresh the display
    refresh()

# Display buffer
def display_buffer(buffer):
    send_command(0x10)  # Write to RAM
    
    for byte_data in buffer:
        send_data(byte_data)
    
    # Refresh the display
    refresh()

# Create a frame buffer initialized with white color
def create_frame_buffer():
    buffer = bytearray(ALLSCREEN_BYTES)
    for i in range(ALLSCREEN_BYTES):
        buffer[i] = 0x55  # All white pixels
    return buffer

def sleep():
    send_command(0x02)  # Power off
    send_data(0x00)
    wait_until_idle()
    
    send_command(0x07)  # Deep sleep
    send_data(0xA5)

# Main execution
try:
    print("Initializing 2.13\" 4-color ePaper display...")
    init_display()
    
    print("Creating frame buffer...")
    buffer = create_frame_buffer()
    
    print("Drawing Hello World (Corrected)...")
    draw_text(buffer, 10, 10, "Hello World", BLACK)    
    draw_text(buffer, 30, 10, "Hello World", YELLOW)   
    draw_text(buffer, 50, 10, "Hello World", RED)      
    
    print("Displaying image...")
    display_buffer(buffer)
    
    print("Display complete!")
    
    print("Putting display to sleep...")
    sleep()
    
    print("Done!")
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("Error occurred: %s" % str(e))


