# Genvex Assistant

Python library to control Genvex Ventilation systems, specifically the Optima 270 (2010 model).

## Features

- Direct communication with Genvex ventilation devices
- Handles U_NOTIFY (Type 0x34) packets that precede actual responses
- Automatic retry/loop mechanism to consume notifications and wait for actual data
- Proper sequence number management for request/response tracking

## Installation

```bash
pip install genvexassistant
```

## Usage

```python
from genvexassistant import GenvexClient

# Create client instance
client = GenvexClient(port="/dev/ttyUSB0")

# Connect to device
client.connect()

# Send commands and handle responses
response = client.send_command(command_data)

# Close connection
client.disconnect()
```

## Protocol Details

The Genvex Optima 270 device often responds with U_NOTIFY packets (Type 0x34) before sending the actual U_CRYPT response. This library handles this behavior automatically by:

1. Consuming U_NOTIFY packets in a loop
2. Waiting for the actual data response
3. Managing sequence numbers across requests

## License

MIT