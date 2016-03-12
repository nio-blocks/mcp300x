from threading import Lock
from nio.block.base import Block
from nio.signal.base import Signal
from nio.util.discovery import discoverable
from nio.properties import VersionProperty, IntProperty


class SPIDevice():

    """Communicate with a peripheral device over SPI.

    The Serial Peripheral Interface (SPI) is a communication protocol used to
    transfer data between micro-computers like the Raspberry Pi and peripheral
    devices.

    """
    def __init__(self, logger, bus=0, device=0):
        import spidev
        self.logger = logger
        self._bus = bus
        self._device = device
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi_lock = Lock()

    def read(self, channel):
        """Read value at channel"""
        with self._spi_lock:
            r = self._spi.xfer2([1, (8 + channel) << 4, 0])
            self.logger.debug("Read from channel {}: {}".format(channel, r))
        return ((r[1] & 3) << 8) + r[2]

    def close(self):
        try:
            self._spi.close()
        except:
            self.logger.warning("Failed to close SPI", exc_info=True)


@discoverable
class MCP300x(Block):

    version = VersionProperty('0.1.0')
    channel = IntProperty(default=0)

    def __init__(self):
        super().__init__()
        self._spi = None

    def configure(self, context):
        super().configure(context)
        self._spi = SPIDevice(self.logger, 0, 0)

    def stop(self):
        super().stop()
        self._spi.close()

    def process_signals(self, signals):
        output_signals = []
        for signal in signals:
            value = self._spi.read(self.channel(signal))
            value = value * 5.0 / 1024
            output_signals.append(Signal({"value": value}))
        self.notify_signals(output_signals)
