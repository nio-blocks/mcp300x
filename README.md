MCP300x
=======
Read from the Microchip MCP300X family of 10-bit analog-to-digital converters.

Properties
----------
- **channel**: Microchip channel to read from
- **chip_model**: Chip model corresponding to total number of channels on chip.
- **enrich**: If true, include the original incoming signal in the output signal.
- **mode**: Mode used by device to read data.
- **speed**: SPI protocol max speed.
- **vref**: Reference value for scaling digital reading to voltage.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Signal with a 'volts' attribute read from the microchip.
```
    {"volts": 3.14}
```

Commands
--------

Dependencies
------------
spidev
