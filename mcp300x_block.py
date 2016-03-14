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

    def writeread(self, data):
        """Write data to spi bus and concurrently read from it

        Args:
            data (list of bytes): the data two write to the bus

        Return:
            list: the data read from the bus

        """
        with self._spi_lock:
            bytes_read = self._spi.xfer2(data)
            self.logger.debug(
                "Read bytes from SPI bus/device ({}, {}): {}".format(
                    self._bus, self._device, bytes_read))
        return bytes_read

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
            digital_output_code = self._read_from_channel(self.channel(signal))
            reference_voltage_input = 5.0
            analog_input_voltage = \
                digital_output_code * reference_voltage_input / 1024
            output_signals.append(Signal({"value": analog_input_voltage}))
        self.notify_signals(output_signals)

    def _read_from_channel(self, channel):
        bytes_to_send = []
        # start bit
        bytes_to_send.append(1)
        # channel number in most significant nibble
        # Note: the 8 sets the mode to "single" instead of "differential" 
        bytes_to_send.append((8 + channel) << 4)
        # "don't care" byte (need to write 3 bytes to read 3 bytes)
        bytes_to_send.append(0)
        # Write and read fro SPI device
        received_data = self._spi.writeread(bytes_to_send)
        # Merge bits 8 and 9 from the second received byte with 7 through 0
        # from the third received byte to create the 10-bit digital value.
        return ((received_data[1] & 3) << 8) + received_data[2]
