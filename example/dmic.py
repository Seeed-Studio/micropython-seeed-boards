import time
import sys

if "nrf54l15" in sys.implementation._machine:
    from boards.xiao import XiaoPDM
    pdm_ch = "pdm0"  
else:
    raise Exception("This code can only run on XIAO nRF54L15 Sence.")

# Single channel capture
print("PCM output rate: 16000, channels: 1")
pdm = XiaoPDM(pdm_ch)
pdm.configure(rate=16000, width=16, channels=1, block_size=320)

for i in range(8):
    pdm.start()
    data = pdm.read()
    print("%d - got buffer of %d bytes" % (i+1, len(data)))
    pdm.stop()

time.sleep(1)

# Stereo channel capture
print("PCM output rate: 16000, channels: 2")
pdm = XiaoPDM(pdm_ch)
pdm.configure(rate=16000, width=16, channels=2, block_size=640)

for i in range(8):
    pdm.start()
    data = pdm.read()
    print("%d - got buffer of %d bytes" % (i+1, len(data)))
    pdm.stop()


