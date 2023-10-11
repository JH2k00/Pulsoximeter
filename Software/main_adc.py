from machine import Pin, ADC
adc1 = ADC(Pin(27, mode=Pin.IN))

I = 0.241751 # 0.241751 mA
U_LSB = (3.3) / (2**16) # U_ref = 3.3V, U_LSB = (U_ref / 2^n) V

while True:
    V = float(adc1.read_u16()) * U_LSB
    R = V / I; # R in kOhm
    print("V = %.6f V, R = %.6f kOhm" %(V,R))