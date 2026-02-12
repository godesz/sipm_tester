"""
Marlin firmware controller for LumenPnP machine via G-Code.
Migrated and improved from old_backend.py lines 54-100.
"""
import serial
import time
import re
from typing import Dict, Optional
from .base import HardwareDevice


class MarlinController(HardwareDevice):
    """
    Controls LumenPnP machine with Marlin firmware using G-Code commands.
    Handles X, Y, Z axis movement with safety features.
    """

    def __init__(self):
        super().__init__()
        self.ser: Optional[serial.Serial] = None
        self.position: Dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.emergency_stop: bool = False
        self.bounds: Dict[str, Dict[str, float]] = {
            "X": {"min": 0, "max": 300},
            "Y": {"min": 0, "max": 300},
            "Z": {"min": 40, "max": 50}  # Z: 40mm safe minimum, 50mm max (endstop at top Z0)
        }

    def connect(self, port: str = "COM3", baudrate: int = 115200, timeout: float = 0.2) -> bool:
        """
        Connect to Marlin controller via serial port.

        Args:
            port: COM port (default: COM3)
            baudrate: Communication baudrate (default: 115200)
            timeout: Serial timeout in seconds (default: 0.2)

        Returns:
            bool: True if connection successful
        """
        try:
            with self.lock:
                if self.connected:
                    return True

                self.ser = serial.Serial(port, baudrate, timeout=timeout)
                time.sleep(2)  # Wait for Marlin to initialize
                self.connected = True
                print(f"Marlin connected on {port}")

                # Query initial position
                self.query_position()
                return True
        except Exception as e:
            print(f"Failed to connect to Marlin on {port}: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from Marlin controller.

        Returns:
            bool: True if disconnection successful
        """
        try:
            with self.lock:
                if self.ser and self.ser.is_open:
                    self.ser.close()
                self.connected = False
                print("Marlin disconnected")
                return True
        except Exception as e:
            print(f"Error disconnecting Marlin: {e}")
            return False

    def send_gcode(self, cmd: str):
        """
        Send G-Code command to Marlin.

        Args:
            cmd: G-Code command string
        """
        self._ensure_connected()

        with self.lock:
            cmd = cmd.strip() + "\n"
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
            print(f">> {cmd.strip()}")
            time.sleep(0.05)

    def read_line(self) -> str:
        """
        Read a line from Marlin serial.

        Returns:
            str: Response line (empty if error)
        """
        try:
            return self.ser.readline().decode(errors="ignore").strip()
        except Exception:
            return ""

    def query_position(self) -> Dict[str, float]:
        """
        Query current position from Marlin using M114.

        Returns:
            Dict with X, Y, Z coordinates
        """
        self._ensure_connected()

        with self.lock:
            self.send_gcode("M114")
            line = self.read_line()
            print(f"<< {line}")

            # Parse response: "X:10.00 Y:20.00 Z:5.00 ..."
            match = re.findall(r"([XYZ])\s*:\s*(-?\d+\.?\d*)", line)
            pos = {axis: float(val) for axis, val in match}

            if pos:
                self.position.update(pos)

            return self.position

    def move_axis(self, axis: str, distance: float, feedrate: int = 5000) -> Dict[str, float]:
        """
        Move specified axis by relative distance.

        Args:
            axis: Axis to move ("X", "Y", or "Z")
            distance: Distance to move in mm (positive or negative)
            feedrate: Movement speed in mm/min (default: 5000)

        Returns:
            Dict with new position

        Raises:
            RuntimeError: If emergency stop is active
            ValueError: If movement exceeds bounds
        """
        self._ensure_connected()

        if self.emergency_stop:
            raise RuntimeError("Emergency stop is active! Clear it before moving.")

        axis = axis.upper()
        if axis not in ["X", "Y", "Z"]:
            raise ValueError(f"Invalid axis: {axis}. Must be X, Y, or Z.")

        # Check bounds
        current_pos = self.position.get(axis, 0)
        new_pos = current_pos + distance

        if new_pos < self.bounds[axis]["min"] or new_pos > self.bounds[axis]["max"]:
            raise ValueError(
                f"Movement would exceed {axis} bounds "
                f"({self.bounds[axis]['min']:.1f} to {self.bounds[axis]['max']:.1f}mm). "
                f"Current: {current_pos:.1f}mm, Requested: {new_pos:.1f}mm"
            )

        with self.lock:
            # Set relative positioning
            self.send_gcode("G91")

            # Move
            self.send_gcode(f"G0 {axis}{distance:.3f} F{feedrate}")

            # Set back to absolute positioning
            self.send_gcode("G90")

            # Query new position
            pos = self.query_position()

        return pos

    def home(self) -> Dict[str, float]:
        """
        Home all axes (G28).

        Returns:
            Dict with position after homing
        """
        self._ensure_connected()

        if self.emergency_stop:
            raise RuntimeError("Emergency stop is active! Clear it before homing.")

        with self.lock:
            self.send_gcode("G28")
            time.sleep(2)  # Wait for homing to complete
            pos = self.query_position()

        return pos

    def set_bounds(self, axis: str, min_val: float, max_val: float):
        """
        Set movement bounds for an axis.

        Args:
            axis: Axis to set bounds for ("X", "Y", or "Z")
            min_val: Minimum position in mm
            max_val: Maximum position in mm
        """
        axis = axis.upper()
        if axis not in ["X", "Y", "Z"]:
            raise ValueError(f"Invalid axis: {axis}")

        self.bounds[axis]["min"] = min_val
        self.bounds[axis]["max"] = max_val
        print(f"Set {axis} bounds: {min_val:.1f} to {max_val:.1f}mm")

    def activate_emergency_stop(self):
        """Activate emergency stop flag."""
        self.emergency_stop = True
        print("EMERGENCY STOP ACTIVATED")

    def clear_emergency_stop(self):
        """Clear emergency stop flag."""
        self.emergency_stop = False
        print("Emergency stop cleared")

    def get_status(self) -> Dict:
        """Get controller status."""
        return {
            **super().get_status(),
            "position": self.position,
            "emergency_stop": self.emergency_stop,
            "bounds": self.bounds
        }
