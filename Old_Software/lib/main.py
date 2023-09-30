# TODO Read hrcalc to see if the girls can program this algorithm on their own.
# TODO Refactor the Code: Make the hearthbeat monitor be a class which runs in a seperate threaed
# TODO Refactor the Code: Make it possible to switch between raw data or calulated data on the displays

# main.py
import os
print("Files on System")
print(os.listdir())
 
from MAX30102 import MAX30102, MAX3010X_I2C_ADDRESS, MAX30105_PULSEAMP_MEDIUM, MAX30105_PULSEAMP_LOW, I2C_SPEED_FAST, MAX30105_PULSEAMP_HIGH
#from ssd1306 import SSD1306_I2C
#import hrcalc   # Algorithm to calculate SpO2 and Heartbeat rate from meassurement data
import logging
#
#import spo2_calc
from ulab import numpy as np
#    
from machine import Pin, I2C
from utime import sleep_ms, ticks_diff, ticks_ms, sleep, time
import framebuf, sys
from CircularBuffer import CircularBuffer
from Calculator import Calculator


# Display Configuration
DISPLAY_START_X = 75
DISPLAY_START_Y = 12
DISPLAY_LINESKIP = 15

# Pin Layout:
#hier waren pins 16 und 17
I2C_SDA_PIN = 16 # GPIO16 = Pin 21
I2C_SCL_PIN = 17 # GPIO17 = Pin 22
#LED_PIN=25

# Initialise Sensor Data Buffer
ir_data = []
red_data = []
bpms = []
bpm = 0

print_results = True

led = Pin(25, Pin.OUT)

fr = []

hr_spO2 = []

samples = 256

def i2c_print(devices):
        if len(devices) == 0:
            print("No i2c device !")
        else:
            print('i2c devices found:',len(devices))

        for device in devices:
            print("Decimal address: ",device," | Hexa address: ",hex(device))

def blink_led(time):
    led.high()
    sleep(1)
    led.low()

# Print the aquired data to the oled display
# TODO Refactor Function 
def print_display(red, ir, start_x=DISPLAY_START_X, start_y=DISPLAY_START_Y, lineskip=DISPLAY_LINESKIP):
    oled_txt_array = ['BPM:', '{}'.format(red) , 'SpO2:', '{}'.format(ir)]
    for i,txt in enumerate(oled_txt_array):
        oled.text(txt, DISPLAY_START_X, DISPLAY_START_Y+(i*DISPLAY_LINESKIP)) # add text at (start_x,start_y)
    oled.show()


class HeartRateMonitor:
    def __init__(self, i2cHexAddress: int, i2c_instance: I2C):
        
        # Connect to MAX30102 over I2C
        self.sensor = MAX30102(i2cHexAddress, i2c_instance)

        # Setup sensor configuration
        self.sensor.setup_sensor(LED_POWER=MAX30105_PULSEAMP_MEDIUM)

        # It is also possible to tune the configuration parameters one by one.
        # Set the sample rate to 1600: 1600 samples/s are collected by the sensor
        self.sensor.setSampleRate(1600)
        # Set the number of samples to be averaged per each reading
        self.sensor.setFIFOAverage(32) #Important for noise reduction. Proved to be the optimal configuration by testing
        self.calc = Calculator()
        self.buffer = CircularBuffer(shape = np.array([samples,4],dtype = np.uint16), columnNames = ['Millis','Red','IR','Samples']) #Samples must be a power of 2 !

    # This method can be executed directly or run in a separate thread
    def run_sensor(self,samples : int):
        t_start = ticks_ms()
        samples_n = 0
        t_led = 0
        blink = False
        curT = 0
        buf = CircularBuffer(shape = np.array([10,4],dtype = np.uint16),columnNames = ['Redfft','IRfft','Redpeaks','IRpeaks'])
        spo2_buf = CircularBuffer(shape = np.array([10,2],dtype = np.uint16),columnNames = ['spo2','valid_spo2'])

        print("Starting data acquisition from RED & IR registers...", '\n')
        freq_bpm = 0
        while(True): #Run for this amount of ms, can be changed.  #abs(ticks_diff(t_start, ticks_ms())) < 12000000
            # The check() method has to be continuously polled, to check if
            # there are new readings into the sensor's FIFO queue. When new
             # readings are available, this function will put them into the storage.
            self.sensor.check()
            # Check if the storage contains available samples
            if(self.sensor.available()):
                # Access the storage FIFO and gather the readings (integers)
                red_reading = self.sensor.popRedFromStorage()
                IR_reading = self.sensor.popIRFromStorage()
                
                print("%.2f,%.2f,%.2f"%(red_reading,IR_reading,freq_bpm))

                # create time stamp from running time
                current_time = ticks_diff(ticks_ms(), t_start)

                # Print the acquired data
                #print(current_time, ', ', red_reading, ', ', IR_reading, ', ', samples_n)
                
                self.buffer.add(np.array([current_time,red_reading,IR_reading,samples_n]).transpose())
                
                if(blink and abs(ticks_diff(t_led, ticks_ms())) >= curT/2): #Blink LED after a Heart period
                    led.toggle()
                    t_led = ticks_ms()

                samples_n += 1
                
                if(samples_n >= samples):
#                     spo2, valid_spo2 = self.calc.spo2_calc(self.buffer)
#                     if(not valid_spo2) :
#                         print(self.buffer.getColumn(1).reshape((32,8)))
#                     spo2_buf.add(np.array([spo2,int(valid_spo2)]).transpose())
#                     freq = self.calc.fr_calc(self.buffer)
                    freq_spo2 = self.calc.hr_spo2_calc(self.buffer)
                    freq = freq_spo2[0:4] #frequencies in bpm (fftRed,fftIR,peaksRed,peaksIR)
                    spo2_buf.add(freq_spo2[4:5].transpose()) #Spo2,validspo2 in int form
                    #curFr = (freq[0]+freq[1]) / 120 #Mean out of the fft frequencies and conversion in Hz
                    curFr = (freq[2]+freq[3])/120
                    curT = 10**3 / curFr # Period in ms
                    buf.add(freq)
                    freq_bpm = (freq[2]+freq[3])/2
                    #print(freq)
                    #print(freq_spo2[4:6].transpose())
                    if(not blink): #Start LED with current time
                        t_led = ticks_ms()
                        led.toggle()
                    blink = True;
                    samples_n = samples_n - 15 #Collect 15 new samples and calculate again (--> wait approx 1 sec)
    

    def shut_down(self):
        self.sensor.shutDown()


def main(samples):
    try:
        hrm = HeartRateMonitor(i2cHexAddress=MAX3010X_I2C_ADDRESS, i2c_instance=i2c_instance)
        hrm.run_sensor(samples)
    except KeyboardInterrupt:
        led.off()
        hrm.shut_down()
        print("Keyboard Interrupt occurs. Finish execution")
 

if __name__ == '__main__':
    
    i2c_instance = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_SPEED_FAST)
    
    # Configure MAX30102 
    logging.basicConfig(level=logging.INFO)
    
    # Scan I2C Devices
    i2c_print(devices=i2c_instance.scan())

    # Initiallize oled
    #oled = SSD1306_I2C(height=64, width=128, i2c=i2c_instance, addr=0x3c)
    #print("Oled display instance = ", oled)

    # The default sensor configuration is:
    # Led mode: 2 (RED + IR)
    # ADC range: 16384
    # Sample rate: 400 Hz
    # Led power: maximum (50.0mA - Presence detection of ~12 inch)
    # Averaged samples: 8
    # pulse width: 411

    # The readTemperature() method allows to extract the die temperature in °C    
    #print("Reading temperature in °C.", '\n')
    #print(sensor.readTemperature())
    
    # Display Data on OLED
    #buffer,img_res = imgfile.get_img() # get the image byte array

    # frame buff types: GS2_HMSB, GS4_HMSB, GS8, MONO_HLSB, MONO_VLSB, MONO_HMSB, MVLSB, RGB565
    #fb = framebuf.FrameBuffer(buffer, img_res[0], img_res[1], framebuf.MONO_HMSB) # MONO_HLSB, MONO_VLSB, MONO_HMSB
    
    main(samples)
    print(fr)