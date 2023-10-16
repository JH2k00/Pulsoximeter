"""
Created on Wed Nov  2 13:27:21 2022

@author: Jad Haidamous
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import time
import os
import serial

serial_connected = 0
baud_rate = 9600 #Replace with your baud rate
port = "COM3" #Replace with your port
if os.path.exists(port):
    ser = serial.Serial(port, baud_rate)
    serial_connected = 1
    time.sleep(1)

# Create figure for plotting
fig, ax = plt.subplots()

line1 = ax.plot([], []) # , lw=2, color='r'

ax.set_xlabel("Samples")
ax.set_ylabel("Red Light Intensity Value")

xs = []

# This function is called periodically from FuncAnimation
def animate(i, xs):
    global xmin
    global xmax
    if ser.inWaiting() > 0:
        esp_data = ser.readline()
        esp_data = esp_data.decode("utf-8","ignore")
        if(esp_data != "\n" and esp_data != "\r\n"):
            xs.append(float(esp_data)) # TODO Update faster to collect all data but plot every 10th call for example
    
    if(len(xs) > 1000):
        xs = xs[-1000:]

    x_axis = np.arange(len(xs))
    if(len(xs) > 2):
        ax.set_xlim((0, len(xs)))
        ax.set_ylim((np.min(xs), np.max(xs)))
    line1[0].set_data(x_axis, xs)
    

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs,), interval=10)
plt.show()
