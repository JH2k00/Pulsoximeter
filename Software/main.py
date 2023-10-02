from ulab import numpy as np

from machine import Pin, I2C
from MAX30102 import MAX30102, MAX3010X_I2C_ADDRESS, MAX30105_PULSEAMP_MEDIUM, MAX30105_PULSEAMP_LOW, I2C_SPEED_FAST, MAX30105_PULSEAMP_HIGH
import ssd1306
from utils import CONST_FIR_COEFFS

I2C_0_SDA_PIN = 16 # GPIO16 = Pin 21
I2C_0_SCL_PIN = 17 # GPIO17 = Pin 22

I2C_1_SDA_PIN = 14 # GPIO14 = Pin 19
I2C_1_SCL_PIN = 15 # GPIO15 = Pin 20

fs = 50 # Normal Heart rate is around 30-300 bpm -> f_max = 300 / 60 Hz = 5 Hz -> 50Hz sampling rate is more than enough

def i2c_print(devices):
        if len(devices) == 0:
            print("No i2c device !")
        else:
            print('i2c devices found:',len(devices))

        for device in devices:
            print("Decimal address: ",device," | Hexa address: ",hex(device))

i2c_0 = I2C(0, sda=Pin(I2C_0_SDA_PIN), scl=Pin(I2C_0_SCL_PIN), freq=I2C_SPEED_FAST)
i2c_print(devices=i2c_0.scan())

i2c_1 = I2C(1, sda=Pin(I2C_1_SDA_PIN), scl=Pin(I2C_1_SCL_PIN), freq=I2C_SPEED_FAST)
i2c_print(devices=i2c_1.scan())

display = ssd1306.SSD1306_I2C(128, 32, i2c_1)

display.fill(0) # Clear previous text
display.text('Collecting', 0, 10, 1)
display.text('samples ...', 0, 20 , 1)
display.show()

sensor = MAX30102(MAX3010X_I2C_ADDRESS, i2c_0)
sensor.setup_sensor(LED_POWER=MAX30105_PULSEAMP_MEDIUM)
sensor.clearFIFO()
sensor.setSampleRate(fs)
sensor.setFIFOAverage(1)

red = []
#ir = []

n_readings = 512 # Must be a power of 2
n_overlap = int(0.95*n_readings)

freq_resolution = float(fs) / float(n_readings)
N = n_readings//2 + 1
f = np.array(list(range(N)))*freq_resolution*60 # Frequency vector in bpm
f_min = 30 # Minimal heart rate frequency in bpm
f_max = 200 # Maximal heart rate frequency in bpm

# Smoothing
periodogram_smooth = np.zeros(f.shape())
forgetting_factor = 0.9
first_update = True # Flag for the first update in order to ignore forgetting factor

while(True):
    sensor.check()
    # Check if the storage contains available samples
    if(sensor.available()):
        # Access the storage FIFO and gather the readings (integers)
        red_reading = sensor.popRedFromStorage()
        IR_reading = sensor.popIRFromStorage()
        red.append(red_reading)
        #ir.append(IR_reading)
        n = len(red)
        if(n >= n_readings):
            red_np = np.array(red) - np.mean(red)
            real, imag = np.fft.fft(red_np)
            real = real[:N]
            imag = imag[:N]
            periodogram = (real*real + imag*imag)
            periodogram[f < f_min] = 0 # Set periodogram of frequencies outside the range to 0
            periodogram[f > f_max] = 0 # Set periodogram of frequencies outside the range to 0
            if(first_update):
                periodogram_smooth = periodogram
                first_update = False
            else:
                periodogram_smooth = forgetting_factor * periodogram_smooth + (1-forgetting_factor) * periodogram # Update current periodogram estimate with the smoothing equation
            heart_rate = f[np.argmax(periodogram_smooth)]
            print(heart_rate)
            display.fill(0) # Clear previous text
            display.text('HR : %.3f' %heart_rate, 0, 10, 1)
            display.show()
            red = red[-n_overlap:]
             

        #ir = ir[-n_readings:]
        #print("Red : %.3f , IR : %.3f" %(red_reading, IR_reading))