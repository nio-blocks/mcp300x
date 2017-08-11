MCP300x
=======

Read from the Microchip MCP300X family of 10-bit analog-to-digital converters.

Properties
----------
- **channel**: channel to read from
- **total_channels**: total number of channels available on the chip
- **enrich**: add information to incoming signals

Dependencies
------------
spidev

Commands
--------
None

Input
-----
Any list of signals.

Output
------
Adds "volts" to each signal.

```
    {"volts": 3.14}
```
