from enum import Enum
from threading import Lock

from nio.block.base import Block
from nio.block.mixins.enrich.enrich_signals import EnrichSignals
from nio.properties import (VersionProperty, FloatProperty, IntProperty,
                            SelectProperty)


class SpiModes(Enum):
    mode_0 = 0b00
    mode_3 = 0b11

class Model(Enum):
    MCP3002 = 0
    MCP3004 = 1
    MCP3008 = 2

class SPIDevice:

    """Communicate with a peripheral device over SPI.

    The Serial Peripheral Interface (SPI) is a communication protocol used to
    transfer data between micro-computers like the Raspberry Pi and peripheral
    devices.

    """
    def __init__(self, logger, bus=0, device=0, speed_hz=500000,
                 spi_mode=SpiModes.mode_0):
        import spidev
        self.logger = logger
        self._bus = bus
        self._device = device
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = speed_hz
        self._spi.mode = spi_mode
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


class MCP300x(EnrichSignals, Block):

    version = VersionProperty('0.1.0')
    channel = IntProperty(default=0, title="Channel Number")
    chip_model = SelectProperty(Model, default=Model.MCP3008, title="Chip Model")
    speed = IntProperty(default=500000, title="Clock Rate (Hz)")
    vref = FloatProperty(default=5.0, title="Reference Voltage")
    mode = SelectProperty(SpiModes, title="SPI Mode", default=SpiModes.mode_0)

    def __init__(self):
        super().__init__()
        self._spi = None

    def configure(self, context):
        super().configure(context)
        self._spi = SPIDevice(self.logger, 0, 0, self.speed(), self.mode())

    def stop(self):
        super().stop()
        self._spi.close()

    def process_signals(self, signals):
        output_signals = []
        for signal in signals:
            analog_input_voltage = self._read_from_channel(
                self.channel(signal))
            output_signals.append(self.get_output_signal(
                {"volts": analog_input_voltage}, signal))
        self.notify_signals(output_signals)

    def _read_from_channel(self, channel):
        bytes_to_send = []
        # start bit
        bytes_to_send.append(1)
        # channel number in most significant nibble
        if self.chip_model().value == 0:
            bytes_to_send.append((2 + channel) << 6)
        else:
            bytes_to_send.append((8 + channel) << 4)
        # "don't care" byte (need to write 3 bytes to read 3 bytes)
        bytes_to_send.append(0)
        # Write and read from SPI device
        received_data = self._spi.writeread(bytes_to_send)
        # Merge bits 8 and 9 from the second received byte with 7 through 0
        # from the third received byte to create the 10-bit digital value.
        digital_output_code = ((received_data[1] & 3) << 8) + received_data[2]
        # Scale digital reading to voltage.
        return digital_output_code * self.vref() / 1024
