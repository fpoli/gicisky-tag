import math
import asyncio
import logging
from bleak import BleakClient
from gicisky_tag.log import logger


class ScreenWriter:
    """
    Class to write an image to a screen device.

    Attrbutes:
    - device: The `BleakClient` instance to which the image will be sent.
    - image: The encoded image data, as a `bytes` object.
    - block_size: The block size for the image transfer, as an `int` or `None` if not yet known.
    - transfer_queue:
        An `asyncio.queues.Queue()` that will contain the data of the next image block to send, or `None` if the
        transfer is complete.
    - notify_handler_results:
        An `asyncio.queues.Queue()` that will contain `None` as soon as a notification is handled correctly, or an
        exception if the handling failed.
    """

    REQUEST_CHARACTERISTIC = "0000fef1-0000-1000-8000-00805f9b34fb"
    IMAGE_CHARACTERISTIC = "0000fef2-0000-1000-8000-00805f9b34fb"

    def __init__(self, device, image):
        logger.debug(f"Image data: {len(image)} bytes")
        assert len(image) > 0
        self.device = device
        self.image = image
        self.block_size = None
        self.transfer_queue = asyncio.queues.Queue()
        self.notify_handler_results = asyncio.queues.Queue()

    async def start_notify(self):
        async def notify_handler_task(sender, data):
            try:
                await self.notify_handler(sender, data)
            # Here we catch all exceptions to avoid "Task exception was never retrieved" errors
            except Exception as e:
                logger.error(f"Error in the notify handler: {e}")
                await self.notify_handler_results.put(e)
            else:
                # Signal that the notification was handled correctly
                await self.notify_handler_results.put(None)

        await self.device.start_notify(
            ScreenWriter.REQUEST_CHARACTERISTIC, notify_handler_task
        )

    async def stop_notify(self):
        logger.debug(f"Stop notify")
        await self.device.stop_notify(ScreenWriter.REQUEST_CHARACTERISTIC)

    async def _send_request(self, data):
        logger.log(
            logging.NOTSET,
            f"Sending request message: {[data[i] for i in range(len(data))]}",
        )
        if not isinstance(data, bytes):
            data = bytes(data)
        await self.device.write_gatt_char(
            ScreenWriter.REQUEST_CHARACTERISTIC,
            data,
            response=True,
        )
        # Wait until we handled the response of the request
        result = await self.notify_handler_results.get()
        # Propagate an exception if we failed to handle the response
        if result is not None:
            raise result

    async def _send_write(self, data):
        logger.log(
            logging.NOTSET,
            f"Sending image message: {[data[i] for i in range(len(data))]}",
        )
        assert len(data) <= self.block_size
        await self.device.write_gatt_char(
            ScreenWriter.IMAGE_CHARACTERISTIC,
            data,
            response=True,
        )

    async def request_block_size(self):
        logger.log(logging.NOTSET, "Request: block size")
        await self._send_request([0x01])

    async def request_write_screen(self):
        assert self.block_size is not None and self.block_size > 0
        size = len(self.image)
        logger.debug(f"Request: write screen (size: {size})")
        await self._send_request([0x02, *size.to_bytes(4, "little")])

    async def request_start_transfer(self):
        logger.debug("Request: start transfer")
        await self._send_request([0x03])

    async def handle_transfer(self):
        logger.debug("Handle transfer")
        while True:
            block = await self.transfer_queue.get()
            if block is None:
                return
            await self.send_image_block(block)

    async def request_write_cancel(self):
        logger.debug("Request: write cancel")
        await self._send_request([0x04])

    async def request_write_settings(self, settings):
        await self._send_request([0x40, *settings])

    async def request_set_address(self, address):
        await self._send_request([0x19, *address[0:6:-1]])

    async def notify_handler(self, _characteristic, data):
        logger.log(
            logging.NOTSET, f"Received notify: {[data[i] for i in range(len(data))]}"
        )
        if data[0] == 0x01:
            assert len(data) == 3
            logger.debug(f"Success: block size request")
            self.block_size = int.from_bytes(data[1:], "little")
            logger.debug(f"Received block size: {self.block_size}")
        elif data[0] == 0x02:
            if data[1] == 0x00:
                logger.debug("Success: write screen request")
            else:
                raise Exception(f"Error: write screen {data[1]}")
        elif data[0] == 0x04:
            if data[1] == 0x00:
                logger.debug("Success: update cancel request")
            else:
                raise Exception(f"Error: update cancel {data[1]}")
        elif data[0] == 0x05:
            if data[1] == 0x00:
                logger.debug(f"Success: image transfer request")
                # Push a new block to be sent by `handle_transfer`
                await self.transfer_queue.put(int.from_bytes(data[2:6], "little"))
            elif data[1] == 0x08:
                logger.debug(f"Success: image transfer request")
                logger.debug(f"Screen write complete")
                # Signal to `handle_transfer` that the transfer is complete
                await self.transfer_queue.put(None)
            else:
                raise Exception(f"Error: image transfer ({data[1]})")
        elif data[0] == 0x19:
            logger.debug(f"Success: set new address request")
        elif data[0] == 0x40:
            logger.debug(f"Success: set remote device setting request")
        elif data[0] == 0x50:
            logger.debug(f"Success: exit remote device setting request")
        else:
            logger.error(f"Unknown state: {data}")

    async def send_image_block(self, part):
        img_block_size = self.block_size - 4
        num_parts = math.ceil(len(self.image) / img_block_size)
        assert (
            part < num_parts
        ), f"Part {part} is too high, there are only {num_parts} parts."
        logger.info(f"Sending image part {part + 1}/{num_parts}")
        image_block = self.image[
            part * img_block_size : part * img_block_size + img_block_size
        ]
        assert 0 < len(image_block) <= img_block_size
        message = bytearray([*part.to_bytes(4, "little"), *image_block])
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
        await screen.handle_transfer()
        await screen.stop_notify()
