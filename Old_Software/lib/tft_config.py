"""Configuration for 240x240x 1.54" OLED Diplay"""

from micropython import const
from machine import Pin, SPI
import st7789
from config import DISPLAY_SPI_SCK_PIN, DISPLAY_SPI_MOSI_PIN, DISPLAY_RESET_PIN, DISPLAY_CS_PIN, DISPLAY_DC_PIN, \
    DISPLAY_BLK_PIN

TFA = const(40)  # top free area when scrolling
BFA = const(40)  # bottom free area when scrolling


def config(rotation=0, buffer_size=0, options=0):
    return st7789.ST7789(
        SPI(1, baudrate=62500000, sck=Pin(DISPLAY_SPI_SCK_PIN, Pin.OUT), mosi=Pin(DISPLAY_SPI_MOSI_PIN, Pin.OUT),
            miso=None),
        240,
        240,
        reset=Pin(DISPLAY_RESET_PIN, Pin.OUT),
        cs=Pin(DISPLAY_CS_PIN, Pin.OUT),
        dc=Pin(DISPLAY_DC_PIN, Pin.OUT),
        backlight=Pin(DISPLAY_BLK_PIN, Pin.OUT),
        rotation=rotation,
        options=options,
        buffer_size=buffer_size)


if __name__ == '__main__':
    import font

    display = config()
    display.init()
    display.text(font, 'hello world', 0, 0, st7789.RED)
