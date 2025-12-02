#!/usr/bin/env python3
"""Example usage of Genvex Assistant library.

This example demonstrates how to control a Genvex Optima 270 ventilation system.
"""

import logging
from genvexassistant import GenvexClient

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main example function."""
    # Configuration
    port = "/dev/ttyUSB0"  # Update this to match your serial port
    
    print("Genvex Assistant - Example Usage")
    print("=" * 50)
    
    # Create client (context manager handles connect/disconnect)
    with GenvexClient(port=port) as client:
        print(f"\nConnected to Genvex device on {port}")
        
        # Example: Send a command to the device
        # Replace this with actual command data for your device
        command_data = b'\x01\x02\x03\x04'
        
        print(f"\nSending command: {command_data.hex()}")
        
        try:
            # Send command and wait for response
            # The client automatically handles U_NOTIFY packets
            response = client.send_command(command_data)
            
            if response:
                print(f"Received response:")
                print(f"  - Type: {response.packet_type.name} (0x{response.packet_type:02X})")
                print(f"  - Sequence: {response.sequence}")
                print(f"  - Data: {response.data.hex()}")
            else:
                print("No response received")
                
        except Exception as e:
            print(f"Error communicating with device: {e}")
    
    print("\nDisconnected from device")

if __name__ == "__main__":
    main()
