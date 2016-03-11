from collections import defaultdict
from unittest import skip
from unittest.mock import MagicMock, patch
from nio.block.terminals import DEFAULT_TERMINAL
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..mcp300x_block import MCP300x, SPIDevice


class TestMCP300xBlock(NIOBlockTestCase):

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_spi_device(self, mock_spi):
        """SPIDevice is intialized with default bus and device in configure."""
        blk = MCP300x()
        self.configure_block(blk, {})
        self.assertTrue(blk._spi)
        self.assertTrue(isinstance(blk._spi, SPIDevice))
        # SPIDevice is initialized with default bus and device
        mock_spi.assert_called_once_with(0, 0)

    @patch(SPIDevice.__module__ + ".SPIDevice", spec=SPIDevice)
    def test_read(self, mock_spi):
        """Each signal triggers an spi read."""
        blk = MCP300x()
        self.configure_block(blk, {})
        blk._spi.read.return_value = 3.14
        blk.start()
        blk.process_signals([Signal()])
        blk.stop()
        blk._spi.read.assert_called_once_with(0)
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
                "value": 3.14
            })

    @skip("Only run on a raspbeery pi")
    def test_read(self, mock_spi):
        """Raspberry pi uses spidev library's xfer2 function."""
        blk = MCP300x()
        self.configure_block(blk, {})
        self._spi._spi.xfer2 = MagicMock(return_value=4)
        blk.start()
        blk.process_signals([Signal()])
        blk.stop()
        blk._spi.read.assert_called_once_with(0)
        self.assert_num_signals_notified(1)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(), {
                "value": 3.14
            })
