from ulab import numpy as np

from machine import Pin, I2C
from MAX30102 import MAX30102, MAX3010X_I2C_ADDRESS, MAX30105_PULSEAMP_MEDIUM, MAX30105_PULSEAMP_LOW, I2C_SPEED_FAST, MAX30105_PULSEAMP_HIGH

I2C_SDA_PIN = 16 # GPIO16 = Pin 21
I2C_SCL_PIN = 17 # GPIO17 = Pin 22

fs = 200

def i2c_print(devices):
        if len(devices) == 0:
            print("No i2c device !")
        else:
            print('i2c devices found:',len(devices))

        for device in devices:
            print("Decimal address: ",device," | Hexa address: ",hex(device))

i2c_instance = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_SPEED_FAST)
i2c_print(devices=i2c_instance.scan())
sensor = MAX30102(MAX3010X_I2C_ADDRESS, i2c_instance)
sensor.setup_sensor(LED_POWER=MAX30105_PULSEAMP_MEDIUM)
sensor.setSampleRate(fs)
sensor.setFIFOAverage(1)

red = []
#ir = []

n_readings = 2048 # Must be a power of 2
n_overlap = int(0.95*n_readings)

freq_resolution = float(fs) / float(n_readings)
N = n_readings//2 + 1
f = np.array(list(range(N)))*freq_resolution*60 #Vector in bpm
#print(f)

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
            print(f[np.argmax(periodogram)])
            red = red[-n_overlap:]
             

        #ir = ir[-n_readings:]
        #print("Red : %.3f , IR : %.3f" %(red_reading, IR_reading))