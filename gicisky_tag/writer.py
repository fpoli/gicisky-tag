import math
import asyncio
import logging
from bleak import BleakClient
from gicisky_tag.log import logger


class ScreenWriter:
    REQUEST_CHARACTERISTIC = "0000fef1-0000-1000-8000-00805f9b34fb"
    IMAGE_CHARACTERISTIC = "0000fef2-0000-1000-8000-00805f9b34fb"

    def __init__(self, device, image):
        self.device = device
        self.image = image
        self.block_size = None
        self.pending_notify = None
        self.transfer_queue = None
        logger.debug(f"Image data: {len(image)} bytes")
        assert len(image) > 0

    async def start_notify(self):
        async def handler(sender, data):
            await self.notify_handler(sender, data)
        await self.device.start_notify(ScreenWriter.REQUEST_CHARACTERISTIC, handler)

    async def stop_notify(self):
        logger.debug(f"Stop notify")
        await self.device.stop_notify(ScreenWriter.REQUEST_CHARACTERISTIC)

    async def _send_request(self, data):
        logger.log(logging.NOTSET, f"Sending request message: {[data[i] for i in range(len(data))]}")
        self.pending_notify = asyncio.Event()
        pending_task = self.pending_notify
        await self.device.write_gatt_char(
            ScreenWriter.REQUEST_CHARACTERISTIC,
            data,
            response=True,
        )
        return pending_task

    async def _send_write(self, data):
        logger.log(logging.NOTSET, f"Sending image message: {[data[i] for i in range(len(data))]}")
        assert len(data) <= self.block_size
        await self.device.write_gatt_char(
            ScreenWriter.IMAGE_CHARACTERISTIC,
            data,
            response=True,
        )

    async def raw_request(self, message):
        panding_task = await self._send_request(bytearray(message))
        await panding_task.wait()

    async def request_block_size(self):
        logger.log(logging.NOTSET, "Request: block size")
        await self.raw_request([0x01])

    async def request_write_screen(self):
        assert self.block_size is not None and self.block_size > 0
        size = len(self.image)
        logger.debug(f"Request: write screen (size: {size})")
        await self.raw_request([0x02, *size.to_bytes(4, "little")])

    async def request_start_transfer(self):
        self.transfer_queue = asyncio.Queue()

        async def transfer_task(queue):
            while True:
                block = await queue.get()
                if block is None:
                    return
                await self.send_image_block(block)

        task = asyncio.create_task(transfer_task(self.transfer_queue))
        logger.debug("Request: start transfer")
        await self.raw_request([0x03])
        await asyncio.wait([task])

    async def request_write_cancel(self):
        logger.debug("Request: write cancel")
        await self.raw_request([0x04])

    async def request_write_settings(self, settings):
        await self.raw_request([0x40, *settings])

    async def request_set_address(self, address):
        await self.raw_request([0x19, *address[0:6:-1]])

    async def notify_handler(self, _characteristic, data):
        logger.log(logging.NOTSET, f"Received notify: {[data[i] for i in range(len(data))]}")
        if data[0] == 0x01:
            assert len(data) == 3
            logger.debug(f"Success: block size request")
            self.block_size = int.from_bytes(data[1:], "little")
            logger.debug(f"Received block size: {self.block_size}")
            self.pending_notify.set()
        elif data[0] == 0x02:
            if data[1] == 0x00:
                logger.debug("Success: write screen request")
                self.pending_notify.set()
            else:
                raise Exception(f"Error: write screen {data[1]}")
        elif data[0] == 0x04:
            if data[1] == 0x00:
                logger.debug("Success: update cancel request")
                self.pending_notify.set()
            else:
                raise Exception(f"Error: update cancel {data[1]}")
        elif data[0] == 0x05:
            if data[1] == 0x00:
                logger.debug(f"Success: image transfer request")
                await self.transfer_queue.put(int.from_bytes(data[2:6], "little"))
            elif data[1] == 0x08:
                logger.debug(f"Success: image transfer request")
                logger.debug(f"Screen write complete")
                await self.transfer_queue.put(None)
                self.pending_notify.set()
            else:
                raise Exception(f"Error: image transfer ({data[1]})")
        elif data[0] == 0x19:
            logger.debug(f"Success: set new address request")
            self.pending_notify.set()
        elif data[0] == 0x40:
            logger.debug(f"Success: set remote device setting request")
            self.pending_notify.set()
        elif data[0] == 0x50:
            logger.debug(f"Success: exit remote device setting request")
            self.pending_notify.set()
        else:
            logger.error(f"Unknown state: {data}")

    async def send_image_block(self, part):
        img_block_size = self.block_size - 4
        num_parts = math.ceil(len(self.image) / img_block_size)
        assert part < num_parts, f"Part {part} is too high, there are only {num_parts} parts."
        logger.info(f"Sending image part {part + 1}/{num_parts}")
        image_block = self.image[part * img_block_size : part * img_block_size + img_block_size]
        assert 0 < len(image_block) <= img_block_size
        message = bytearray([
            *part.to_bytes(4, "little"),
            *image_block
        ])
        await self._send_write(message)


async def send_data_to_screen(address, image_data):
    logger.info(f"Connecting to {address}...")
    async with BleakClient(address) as device:
        # BlueZ doesn't have a proper way to get the MTU, so we have this hack.
        # If this doesn't work for you, you can set the device._mtu_size attribute
        # to override the value instead.
        if device._backend.__class__.__name__ == "BleakClientBlueZDBus":
            await device._backend._acquire_mtu()
        logger.debug(f"MTU: {device.mtu_size}")

        screen = ScreenWriter(device, image_data)
        logger.info(f"Sending image data...")
        await screen.start_notify()
        await screen.request_block_size()
        await screen.request_write_screen()
        await screen.request_start_transfer()
        await screen.stop_notify()
