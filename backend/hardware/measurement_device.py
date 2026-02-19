"""
Measurement device controller for diode testing and LED control.
NEW hardware integration not present in old_backend.py.
"""
import serial
import time
import re
from typing import Dict, Optional
from .base import HardwareDevice


class MeasurementDevice(HardwareDevice):
    """
    Controls custom measurement hardware via serial port.
    Handles diode testing through POGO pins and LED light control.
    """

    # Connection states
    CONNECTION_SHORT = 0
    CONNECTION_OK = 1
    CONNECTION_NOT_VALID = 2
    CONNECTION_OPEN = 3
    CONNECTION_I2C_ERROR = 0xFF

    CONNECTION_NAMES = {
        0: "short",
        1: "ok",
        2: "not_valid",
        3: "open",
        0xFF: "i2c_error"
    }

    def __init__(self):
        super().__init__()
        self.ser: Optional[serial.Serial] = None
        self.psu_enabled = False

    def connect(self, port: str = "COM5", baudrate: int = 115200, timeout: float = 5.0) -> bool:
        """
        Connect to measurement device via serial port.

        Args:
            port: COM port (default: COM5)
            baudrate: Communication baudrate (default: 115200)
            timeout: Serial timeout in seconds (default: 5.0)

        Returns:
            bool: True if connection successful
        """
        try:
            with self.lock:
                if self.connected:
                    return True

                self.ser = serial.Serial(port, baudrate, timeout=timeout)
                time.sleep(3.0)  # Wait for device to initialize
                self.connected = True
                print(f"Measurement device connected on {port}")

            # Auto-enable PSU (required before any commands)
            self.enable_psu()
            print("PSU auto-enabled on connect")

            return True
        except Exception as e:
            print(f"Failed to connect to measurement device on {port}: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from measurement device.

        Returns:
            bool: True if disconnection successful
        """
        try:
            with self.lock:
                # Turn off LEDs before disconnecting
                if self.connected:
                    try:
                        self.turn_off_leds()
                    except:
                        pass

                if self.ser and self.ser.is_open:
                    self.ser.close()
                self.connected = False
                self.psu_enabled = False
                print("Measurement device disconnected")
                return True
        except Exception as e:
            print(f"Error disconnecting measurement device: {e}")
            return False

    def _send_command(self, cmd: str) -> str:
        """
        Send command to measurement device and read response.

        Args:
            cmd: Command string

        Returns:
            str: Response from device
        """
        self._ensure_connected()

        with self.lock:
            # Flush any leftover data in input buffer
            self.ser.reset_input_buffer()

            # Send command with \n\r (same as PuTTY Enter key)
            cmd_str = cmd.strip() + "\n\r"
            self.ser.write(cmd_str.encode("utf-8"))
            self.ser.flush()
            print(f">> {cmd.strip()}")

            # Small delay to let the device process
            time.sleep(0.1)

            # Read response - try readline first, fall back to reading available bytes
            response = self.ser.readline().decode(errors="ignore").strip()

            # If readline got nothing, try reading whatever is in the buffer
            if not response and self.ser.in_waiting > 0:
                raw = self.ser.read(self.ser.in_waiting)
                response = raw.decode(errors="ignore").strip()

            print(f"<< {response}")

            return response

    def enable_psu(self) -> Dict:
        """
        Enable PSU for testing.

        Returns:
            Dict with status
        """
        try:
            response = self._send_command("")

            response = self._send_command("enable_A_psu,0")
            self.psu_enabled = True
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_light(self, mode: int, r: int, g: int, b: int) -> Dict:
        """
        Set LED light mode and color.

        Args:
            mode: Light mode (1=left, 2=right, 3=all)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)

        Returns:
            Dict with status
        """
        if mode not in [1, 2, 3]:
            return {"status": "error", "message": "Mode must be 1 (left), 2 (right), or 3 (all)"}

        if not all(0 <= val <= 255 for val in [r, g, b]):
            return {"status": "error", "message": "RGB values must be 0-255"}

        try:
            cmd = f"set_module,0,0,0,k,{mode},{r},{g},{b}"
            response = self._send_command(cmd)
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def turn_off_leds(self) -> Dict:
        """
        Turn off all LEDs.

        Returns:
            Dict with status
        """
        try:
            cmd = "set_module,0,0,0,k,0,0,0,0"
            response = self._send_command(cmd)
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_diode_measurement(self) -> Dict:
        """
        Get diode measurement / connection state.
        First turns off LEDs, then reads the cooler state.

        Returns:
            Dict with connection state and details

        Response format: "get_cooler_state,0,OK*3,1,0,0.000,0.000,0.00,0.00,0.00,0.00*"
        Parse OK*X where X: 0=short, 1=OK (connected), 2=not_valid, 3=open, FF=i2c error
        """
        try:
            # Turn off LEDs first (required before measurement)
            self.turn_off_leds()
            time.sleep(0.1)

            # Get measurement
            response = self._send_command("get_cooler_state,0")

            # Parse response
            parsed = self._parse_cooler_state(response)
            return parsed

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "connection_state": None,
                "connection_name": "error"
            }

    def _parse_cooler_state(self, response: str) -> Dict:
        """
        Parse cooler state response to extract connection state.

        Args:
            response: Response string from get_cooler_state command

        Returns:
            Dict with parsed connection state
        """
        # Look for OK*X pattern
        match = re.search(r"OK\*([0-9A-Fa-f]+)", response)

        if match:
            state_str = match.group(1)

            # Handle hex values (like FF)
            if state_str.upper() == "FF":
                state = self.CONNECTION_I2C_ERROR
            else:
                state = int(state_str)

            state_name = self.CONNECTION_NAMES.get(state, "unknown")

            return {
                "status": "ok",
                "connection_state": state,
                "connection_name": state_name,
                "raw_response": response,
                "is_connected": (state == self.CONNECTION_OK)  # State 1 means connected
            }
        else:
            return {
                "status": "error",
                "message": "Could not parse response",
                "connection_state": None,
                "connection_name": "parse_error",
                "raw_response": response,
                "is_connected": False
            }

    def test_connection(self) -> bool:
        """
        Test if POGO pins are properly connected (state = 1).

        Returns:
            bool: True if connected (state 1), False otherwise
        """
        result = self.get_diode_measurement()
        return result.get("is_connected", False)

    def get_status(self) -> Dict:
        """Get measurement device status."""
        return {
            **super().get_status(),
            "psu_enabled": self.psu_enabled
        }
