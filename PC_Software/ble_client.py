import asyncio
from bleak import BleakScanner, BleakClient
import struct

name = "etv-pulse-oximeter"

def decode_heartrate(hr):
    return struct.unpack(">h", hr)[0]

async def main(name):
    device = await BleakScanner.find_device_by_name(name)
    if(device is None):
        print("No Bluetooth device found with the name : %s" %name)
        return
    print(device)
    async with BleakClient(device) as client:
        heart_rate = 0
        while(heart_rate is not None):
            heart_rate = await client.read_gatt_char("00002a37-0000-1000-8000-00805f9b34fb")
            print(decode_heartrate(heart_rate))

asyncio.run(main(name))