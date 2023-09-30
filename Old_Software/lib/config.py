"""
Configures the Pin Layout
"""
from os import uname
from micropython import const

# FIXME Config should be able to run on esp and pico

# Samples must be a power of 2 !
SAMPLE_NUM = const(400) #Changed it to 400 -Jad

# Display Configuration
DISPLAY_START_X = const(75)
DISPLAY_START_Y = const(12)
DISPLAY_LINESKIP = const(15)
DISPLAY_PPG_Y_OFFSET = const(240)  # Start the PPG curve on the given pixel
DISPLAY_PPG_Y_SCALE = const(120)  # The scale of the ppg curve in pixels

# TODO Make a dynamic threhold depending on the LED_POWER
FINGER_DETECTED_THRESHOLD = const(10000)  # TODO TEST THRESHOLD
"""
FIR_FILTER_COEFFS = [0.01104616, 0.04979226, 0.01546462, -0.06468204, -0.07041689, 0.07468839, 0.28857376, 0.39106748,
                     0.28857376, 0.07468839, -0.07041689, -0.06468204, 0.01546462, 0.04979226, 0.01104616]
"""
FIR_FILTER_COEFFS = [0.027742531373917703, -0.004332056402688453, -0.03677643938284043, -0.016087865849492934,
                     0.03848339132316854, 0.04548037156374464, -0.026813109749154934, -0.08931420992975533,
                     -0.016461814330216217, 0.19419771961742396, 0.3838814817658934, 0.3838814817658934,
                     0.19419771961742396, -0.016461814330216217, -0.08931420992975533, -0.026813109749154934,
                     0.04548037156374464, 0.03848339132316854, -0.016087865849492934, -0.03677643938284043,
                     -0.004332056402688453, 0.027742531373917703]
LED_BLINK_TIME = const(50)  # Beat Detection blink duration in ms
BEATS_BUFFER_LEN = const(4)  # Save the last N detected beats to average them out a little
PPG_BPM_AVG = const(4)  # Average the calulation of N beats together

# Configuration for RP2040
if uname()[0] == 'rp2':
    print("Running Code on a raspberry Pi pico:")
    # Display Pins
    DISPLAY_SPI_SCK_PIN = const(14)
    DISPLAY_SPI_MOSI_PIN = const(15)
    DISPLAY_SPI_MISO_PIN = const(25)  # Not Used but cant be left to None in Soft SPI
    DISPLAY_RESET_PIN = const(10)
    DISPLAY_DC_PIN = const(11)
    DISPLAY_CS_PIN = const(12)
    DISPLAY_BLK_PIN = const(13)

    # MAX30102
    MAX30102_I2C_SDA_PIN = const(16)
    MAX30102_I2C_SCL_PIN = const(17)

    # LED Builtin
    LED_BUILTIN_PIN = const(25)

# Configuration for ESP32
"""
elif uname()[0] == 'esp32':
    print("Running Code on an ESP32:")
    # Display Pins
    DISPLAY_SPI_SCK_PIN = const(5)
    DISPLAY_SPI_MOSI_PIN = const(18)
    DISPLAY_SPI_MISO_PIN = None
    DISPLAY_RESET_PIN = const(14)
    DISPLAY_DC_PIN = const(32)
    DISPLAY_CS_PIN = const(15)
    DISPLAY_BLK_PIN = const(33)

    # MAX30102
    MAX30102_I2C_SDA_PIN = const(23)
    MAX30102_I2C_SCL_PIN = const(22)

    # LED Builtin
    LED_BUILTIN_PIN = const(13)
"""

HEART = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 1, 1, 0],
    [1, 1, 1, 1, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0],
]

CIRCLE = [
    [0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 1, 1, 1, 0],
    [1, 1, 1, 1, 1],
    [0, 1, 1, 1, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0],
]
