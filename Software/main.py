from ulab import numpy as np
from machine import Pin, I2C, ADC, PWM
from MAX30102 import MAX30102, MAX3010X_I2C_ADDRESS, MAX30105_PULSEAMP_MEDIUM, MAX30105_PULSEAMP_LOW, I2C_SPEED_FAST, MAX30105_PULSEAMP_HIGH
import ssd1306
from utils import CONST_FIR_COEFFS
import struct
import asyncio
from utils import CONST_TONES, CONST_DEFAULT_SONG

from micropython import const

import aioble
import bluetooth

# org.bluetooth.service.pulse_oximeter
_PLX_SENSE_UUID = bluetooth.UUID(0x1822)

# org.bluetooth.characteristic.heart_rate_measurement
_PLX_CHAR_HR_UUID = bluetooth.UUID(0x2A37)

# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_PULSE_OXIMETER = const(0x0C40)

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = const(250000)

# Register GATT server.
plx_service = aioble.Service(_PLX_SENSE_UUID)
plx_characteristic = aioble.Characteristic(
    plx_service, _PLX_CHAR_HR_UUID, read=True, notify=True
)
aioble.register_services(plx_service)

I2C_0_SDA_PIN = Pin(4, pull=Pin.PULL_UP) # GPIO4 = Pin 6
I2C_0_SCL_PIN = Pin(5, pull=Pin.PULL_UP) # GPIO5 = Pin 7

I2C_1_SDA_PIN = Pin(2, pull=Pin.PULL_UP) # GPIO2 = Pin 4
I2C_1_SCL_PIN = Pin(3, pull=Pin.PULL_UP) # GPIO3 = Pin 5

adc1 = ADC(Pin(27, mode=Pin.IN))

gpio_pin = Pin(22, mode=Pin.OUT, value=1)
adc0 = ADC(Pin(26, mode=Pin.IN))

DISPLAY_STATE = 0 # 0 -> HR, 1-> Resistor, 2-> Diode

buzzer = PWM(Pin(15))
buzzer.freq(500)

def button_handler(pin):
    global DISPLAY_STATE
    DISPLAY_STATE = (DISPLAY_STATE + 1) % 3

button_2 = Pin(13, mode=Pin.IN)
button_2.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

I = 0.241751 # 0.241751 mA
U_LSB = (3.3) / (2**16) # U_ref = 3.3V, U_LSB = (U_ref / 2^n) V

LED = Pin('LED', Pin.OUT)
LED.toggle()

fs = 50 # Normal Heart rate is around 30-300 bpm -> f_max = 300 / 60 Hz = 5 Hz -> 50Hz sampling rate is more than enough

def i2c_print(devices):
        if len(devices) == 0:
            print("No i2c device !")
        else:
            print('i2c devices found:',len(devices))

        for device in devices:
            print("Decimal address: ",device," | Hexa address: ",hex(device))

i2c_0 = I2C(0, sda=I2C_0_SDA_PIN, scl=I2C_0_SCL_PIN, freq=I2C_SPEED_FAST)
i2c_print(devices=i2c_0.scan())

i2c_1 = I2C(1, sda=I2C_1_SDA_PIN, scl=I2C_1_SCL_PIN, freq=I2C_SPEED_FAST)
i2c_print(devices=i2c_1.scan())

display = ssd1306.SSD1306_I2C(128, 32, i2c_0)

display.fill(0) # Clear previous text
display.text('Collecting', 0, 10, 1)
display.text('samples ...', 0, 20 , 1)
display.show()

sensor = MAX30102(MAX3010X_I2C_ADDRESS, i2c_1)
sensor.setup_sensor(LED_POWER=MAX30105_PULSEAMP_MEDIUM)
sensor.clearFIFO()
sensor.setSampleRate(fs)
sensor.setFIFOAverage(1)

# Helper to encode the heart rate characteristic encoding (uint16).
def _encode_heart_rate(hr):
    return struct.pack(">h", int(hr))

# This would be periodically polling a hardware sensor.
async def read_heart_rate():
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
    periodogram_smooth = np.zeros(f.shape)
    forgetting_factor = 0.9
    first_update = True # Flag for the first update in order to ignore forgetting factor

    heart_rate = 0

    while True:
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
                if(DISPLAY_STATE == 0):
                    display.fill(0) # Clear previous text
                    display.text('HR : %.3f' %heart_rate, 0, 10, 1)
                    display.show()
                red = red[-n_overlap:]
        plx_characteristic.write(_encode_heart_rate(heart_rate)) # Update Bluetooth
        await asyncio.sleep_ms(int(1000 / (2*fs)))

# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name="etv-pulse-oximeter",
            services=[_PLX_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_PULSE_OXIMETER,
        ) as connection:
            print("Connection from", connection.device)
            await connection.disconnected()

async def measure_diode():
    while True:
        V = float(adc0.read_u16()) * U_LSB
        V_diode = 3.3 - V 
        if(DISPLAY_STATE == 2):
            display.fill(0) # Clear previous text
            display.text('V_d = %.3f V' %V_diode, 0, 10, 1)
            display.show()
        await asyncio.sleep_ms(500)
    #print("Diode Forward Voltage is V = %.3f V" %(V_diode))

async def measure_resistor():
    while True:
        V = float(adc1.read_u16()) * U_LSB
        R = V / I; # R in kOhm
        if(DISPLAY_STATE == 1):
            display.fill(0)# Clear previous text
            if(R < 1):
                display.text('R = %.3f Ohm' %(R*1000), 0, 10, 1)
            else:
                display.text('R = %.3f kOhm' %R, 0, 10, 1)
            display.show()
        await asyncio.sleep_ms(500)

# Run both tasks.
async def main():
    t1 = asyncio.create_task(read_heart_rate())
    t2 = asyncio.create_task(peripheral_task())
    t3 = asyncio.create_task(measure_resistor())
    t4 = asyncio.create_task(measure_diode())
    await asyncio.gather(t1, t2, t3, t4, return_exceptions=True)

asyncio.run(main())