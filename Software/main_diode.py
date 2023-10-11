from machine import Pin, ADC, PWM
from utils import CONST_TONES
import asyncio

gpio_pin = Pin(22, mode=Pin.OUT, value=1)
adc0 = ADC(Pin(26, mode=Pin.IN))

volatile_song_flag = True

buzzer = PWM(Pin(15))
buzzer.freq(500)

U_LSB = (3.3) / (2**16)

song = ["E5","G5","A5","P","E5","G5","B5","A5","P","E5","G5","A5","P","G5","E5"]

async def update_song_flag():
	global volatile_song_flag 
	volatile_song_flag = False

def playtone(frequency, buzzer):
    buzzer.duty_u16(1000)
    buzzer.freq(frequency)
    
async def playsong(song, buzzer):
    while(volatile_song_flag):
		for note in song:
			if (note == "P"):
				buzzer.duty_u16(0)
			else:
				playtone(CONST_TONES[note], buzzer)
			await asyncio.sleep_ms(300)
		buzzer.duty_u16(0)
		task = asyncio.create_task(update_song_flag())
		await update_song_flag()

asyncio.run(playsong(song, buzzer))

while True :
	V = float(adc0.read_u16()) * U_LSB
	V_diode = 3.3 - V 
	print("Diode Forward Voltage is V = %.3f V" %(V_diode))