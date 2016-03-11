from nio.block.base import Block
from nio.signal.base import Signal
from nio.util.discovery import discoverable
from nio.properties import VersionProperty


class SPIDevice():

    """Communicate with a peripheral device over SPI.

    The Serial Peripheral Interface (SPI) is a communication protocol used to
    transfer data between micro-computers like the Raspberry Pi and peripheral
    devices.

    """
    def __init__(self, bus=0, device=0):
        self._bus = bus
        self._device = device

    def read(self, channel):
        """Read value at channel"""
        raise NotImplemented()


@discoverable
class MCP300x(Block):

    version = VersionProperty('0.1.0')

    def __init__(self):
        super().__init__()
        self._spi = None

    def configure(self, context):
        super().configure(context)
        self._spi = SPIDevice(0, 0)

    def process_signals(self, signals):
        output_signals = []
        for signal in signals:
            value = self._spi.read(0)
            output_signals.append(Signal({"value": value}))
        self.notify_signals(output_signals)
