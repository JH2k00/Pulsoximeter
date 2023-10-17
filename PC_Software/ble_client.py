import asyncio
from bleak import BleakScanner, BleakClient
import struct
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation

name = "etv-pulse-oximeter"

# Create figure for plotting
fig, ax = plt.subplots()

line1 = ax.plot([], []) # , lw=2, color='r'

ax.set_xlabel("Samples")
ax.set_ylabel("Red Light Intensity Value")

xs = []

# This function is called periodically from FuncAnimation
def animate(i, xs):
    N = len(xs)
    if(N > 1000):
        xs = xs[-1000:]
        N = 1000

    x_axis = np.arange(N)
    if(N > 2):
        ax.set_xlim((0, N))
        ax.set_ylim((np.min(xs), np.max(xs)))
    line1[0].set_data(x_axis, xs)
    
def decode_heartrate(hr):
    return struct.unpack(">h", hr)[0]

async def main(name):
    device = await BleakScanner.find_device_by_name(name)
    if(device is None):
        print("No Bluetooth device found with the name : %s" %name)
        return
    print(device)
    async with BleakClient(device) as client:
        heart_rate = 0
        while(heart_rate is not None):
            heart_rate = await client.read_gatt_char("00002a37-0000-1000-8000-00805f9b34fb")
            xs.append(decode_heartrate(heart_rate))
            print(decode_heartrate(heart_rate))

asyncio.run(main(name))

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs,), interval=10)
plt.show()