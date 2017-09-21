from unittest import skip
from unittest.mock import MagicMock, patch

from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase

from ..mcp300x_block import MCP300x, SPIDevice, SpiModes


class TestMCP300xBlock(NIOBlockTestCase):

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_spi_device(self, mock_spi):
        """SPIDevice is intialized with default bus and device in configure."""
        blk = MCP300x()
        self.configure_block(blk, {})
        self.assertTrue(blk._spi)
        self.assertTrue(isinstance(blk._spi, SPIDevice))
        # SPIDevice is initialized with default bus and device
        mock_spi.assert_called_once_with(
                                  blk.logger, 0, 0, 500000, SpiModes.mode_0)

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_read_from_channel(self, mock_spi):
        """Each signal triggers an spi writeread."""
        blk = MCP300x()
        self.configure_block(blk, {})
        blk._spi.writeread.return_value = [1, 2, 3]
        blk.start()
        blk.process_signals([Signal()])
        blk.stop()
        blk._spi.writeread.assert_called_once_with([1, 8 << 4, 0])
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
                "volts": (((2 & 3) << 8) + 3) * 5.0 / 1024
            })

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_enrich_signals(self, mock_spi):
        """Signals are enriched by new value."""
        blk = MCP300x()
        blk._read_from_channel = MagicMock(return_value=1.23)
        self.configure_block(blk, {
            "enrich": {"exclude_existing": False}
        })
        blk.start()
        blk.process_signals(
            [Signal({"attr1": "val1", "attr2": "val2", "volts": "old"})])
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
                "attr1": "val1",
                "attr2": "val2",
                "volts": 1.23,
            })

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_channel_property(self, mock_spi):
        """Each signal triggers an spi read."""
        blk = MCP300x()
        self.configure_block(blk, {
            "channel": "{{ $channel }}"
        })
        blk.start()
        blk.process_signals([Signal({"channel": 1})])
        blk.stop()
        blk._spi.writeread.assert_called_once_with([1, (8 + 1) << 4, 0])
        self.assert_num_signals_notified(1)

    @skip("Only run on a raspberry pi")
    def test_raspberry_pi(self):
        """Raspberry pi uses spidev library's xfer2 function."""
        blk = MCP300x()
        self.configure_block(blk, {})
        blk._spi._spi = MagicMock()
        blk._spi._spi.xfer2.return_value = b'123'
        blk.start()
        blk.process_signals([Signal()])
        blk.stop()
        blk._spi._spi.xfer2.assert_called_once_with([1, 8 << 4, 0])
        self.assert_num_signals_notified(1)
        # Value should be voltage between 0 and 5
        self.assertTrue(
            0 <= self.last_notified[DEFAULT_TERMINAL][0].volts <= 5)
