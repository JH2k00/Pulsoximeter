from ulab import numpy as np
from machine import Pin, I2C
from MAX30102 import MAX30102, MAX3010X_I2C_ADDRESS, MAX30105_PULSEAMP_MEDIUM, MAX30105_PULSEAMP_LOW, I2C_SPEED_FAST, MAX30105_PULSEAMP_HIGH
import ssd1306
from utils import CONST_FIR_COEFFS
import bluetooth
import struct
import time
import machine
import ubinascii
from ble_advertising import advertising_payload
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

# org.bluetooth.service.pulse_oximeter
_PLX_SENSE_UUID = bluetooth.UUID(0x1822)
# org.bluetooth.characteristic.heart_rate_measurement
_PLX_CHAR = (
    bluetooth.UUID(0x2A37),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE,
)
# Service definition
_PLX_SENSE_SERVICE = (
    _PLX_SENSE_UUID,
    (_PLX_CHAR,),
)

# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_PULSE_OXIMETER = const(3136)
# BLE = Bluetooth Low Energy
class BLEPLX:
    def __init__(self, ble, name=""):
        self._hr = 0
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq) # Event Handling
        ((self._handle,),) = self._ble.gatts_register_services((_PLX_SENSE_SERVICE,))
        self._connections = set()
        if len(name) == 0:
            name = 'Pico %s' % ubinascii.hexlify(self._ble.config('mac')[1],':').decode().upper()
        print('Sensor name %s' % name)
        self._payload = advertising_payload(
            name=name, services=[_PLX_SENSE_UUID]
        )
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data

    def update_hr_spo2(self, notify=False, indicate=False):
        # Write the local value, ready for a central to read.
        # temp_deg_c = self._get_temp()
        # print("write temp %.2f degc" % temp_deg_c)
        self._ble.gatts_write(self._handle, struct.pack("<h", int(temp_deg_c * 100)))
        if notify or indicate:
            for conn_handle in self._connections:
                if notify:
                    # Notify connected centrals.
                    self._ble.gatts_notify(conn_handle, self._handle)
                if indicate:
                    # Indicate connected centrals.
                    self._ble.gatts_indicate(conn_handle, self._handle)

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

       
def demo():
    ble = bluetooth.BLE()
    temp = BLEPLX(ble)
    counter = 0
    led = Pin('LED', Pin.OUT)
    while True:
        #if counter % 10 == 0:
       #     temp.update_temperature(notify=True, 
#indicate=False)
        led.toggle()
        time.sleep_ms(1000)
        counter += 1

I2C_0_SDA_PIN = Pin(4, pull=Pin.PULL_UP) # GPIO4 = Pin 6
I2C_0_SCL_PIN = Pin(5, pull=Pin.PULL_UP) # GPIO5 = Pin 7

I2C_1_SDA_PIN = Pin(2, pull=Pin.PULL_UP) # GPIO2 = Pin 4
I2C_1_SCL_PIN = Pin(3, pull=Pin.PULL_UP) # GPIO3 = Pin 5

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