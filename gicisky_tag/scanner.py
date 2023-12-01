import asyncio
from bleak import BleakScanner
from gicisky_tag.log import logger


async def find_address():
    address = None

    def scan_callback(device, data):
        nonlocal address
        if str(device).upper().startswith("FF:FF") and 20563 in data.manufacturer_data:
            address = str(device)[0:17]
            logger.debug(f"Device {device}: {data}")
            manufacturer_data = data.manufacturer_data[20563]
            power_data = float(manufacturer_data[1]) / 10
            logger.info(f"Found device {address}. Battery: {power_data:.1f} V")

    scanner = BleakScanner(scan_callback)
    while address is None:
        await scanner.start()
        await asyncio.sleep(1.0)
        await scanner.stop()

    return address
