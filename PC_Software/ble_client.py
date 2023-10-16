import asyncio
from bleak import BleakScanner

async def main():
    devices = await BleakScanner.discover(timeout=20)
    for d in devices:
        print(d)

asyncio.run(main())