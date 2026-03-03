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
            "X": {"min": 0, "max": 500},
            "Y": {"min": 0, "max": 500},
            "Z": {"min": 0, "max": 50}
        }

    def connect(self, port: str = "COM4", baudrate: int = 115200, timeout: float = 0.2) -> bool:
        """
        Connect to Marlin controller via serial port.

        Args:
            port: COM port (default: COM4)
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
                self.ser.reset_input_buffer()  # Flush Marlin startup messages
                self.connected = True
                print(f"Marlin connected on {port}")

                # Query initial position
                self.query_position()

                # Configure replacement Z motor (current + steps/mm).
                # RAM-only — must be applied on every connect until saved with M500.
                self._configure_z_axis()

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
            self.ser.reset_input_buffer()
            self.send_gcode("M114")

            # Read up to 20 lines looking for the position response
            for _ in range(20):
                line = self.read_line()
                if not line:
                    continue
                print(f"<< {line}")
                # Strip encoder counts section (e.g. "Count X:3200 Y:0 Z:0")
                # to avoid overwriting real positions with step counts
                line_pos = line.split("Count")[0]
                match = re.findall(r"([XYZ])\s*:\s*(-?\d+\.?\d*)", line_pos)
                if match:
                    pos = {axis: float(val) for axis, val in match}
                    self.position.update(pos)
                    break

            return self.position

    # Default feedrates per axis (mm/min).
    # Z uses a NEMA11 with 400 steps/mm (2mm lead screw).
    # Z=0 is at the top (endstop); Z increases downward toward the SiPM.
    AXIS_FEEDRATES: Dict[str, int] = {"X": 5000, "Y": 5000, "Z": 500}

    def move_axis(self, axis: str, distance: float, feedrate: int = None) -> Dict[str, float]:
        """
        Move specified axis by relative distance.

        Args:
            axis: Axis to move ("X", "Y", or "Z")
            distance: Distance to move in mm (positive or negative)
            feedrate: Movement speed in mm/min. Defaults to AXIS_FEEDRATES[axis].

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

        if feedrate is None:
            feedrate = self.AXIS_FEEDRATES.get(axis, 5000)

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
            self.send_gcode("G28 X Y")  # Z excluded (motor disconnected)
            time.sleep(5)  # Wait for homing to complete
            pos = self.query_position()

        return pos

    def move_to_absolute(self, x: float = None, y: float = None, z: float = None, feedrate: int = None) -> Dict[str, float]:
        """
        Move to an absolute position (X, Y, Z).

        Args:
            x, y, z: Target coordinates in mm (None = don't move that axis)
            feedrate: Movement speed in mm/min

        Returns:
            Dict with new position
        """
        self._ensure_connected()

        if self.emergency_stop:
            raise RuntimeError("Emergency stop is active! Clear it before moving.")

        cmd_parts = []
        axes_used = []
        for axis, val in [("X", x), ("Y", y), ("Z", z)]:
            if val is None:
                continue
            if val < self.bounds[axis]["min"] or val > self.bounds[axis]["max"]:
                raise ValueError(
                    f"Position would exceed {axis} bounds "
                    f"({self.bounds[axis]['min']:.1f} to {self.bounds[axis]['max']:.1f}mm). "
                    f"Requested: {val:.1f}mm"
                )
            cmd_parts.append(f"{axis}{val:.3f}")
            axes_used.append(axis)

        if not cmd_parts:
            return self.position

        # Use the slowest per-axis feedrate among the axes being moved
        if feedrate is None:
            feedrate = min(self.AXIS_FEEDRATES.get(a, 5000) for a in axes_used)

        with self.lock:
            self.send_gcode("G90")  # Absolute positioning
            self.send_gcode(f"G0 {' '.join(cmd_parts)} F{feedrate}")
            pos = self.query_position()

        return pos

    def _configure_z_axis(self):
        """
        Configure the replacement Z motor (NEMA11, 24V/0.6A, 2mm lead screw).

        Applied on every connect (RAM-only, not persisted in EEPROM):
        - M906 Z200 — motor current, same as A/B NEMA11 axes (confirmed working).
        - M92 Z400  — steps/mm confirmed via manual Putty testing (2mm lead screw).

        Z orientation: Z=0 at top (endstop/trigger), Z increases downward toward SiPM.
        Once confirmed stable, save permanently with M500.
        """
        with self.lock:
            # Query all motor currents and log them
            self.send_gcode("M906")
            print("--- Motor currents (M906) ---")
            for _ in range(15):
                line = self.read_line()
                if not line:
                    continue
                print(f"<< {line}")
                if line.lower().startswith("ok"):
                    break

            # Set Z motor current to 200mA — same as A/B axis NEMA11 motors.
            # Light load (POGO pin contact), same motor hardware as A/B.
            self.send_gcode("M906 Z200")
            for _ in range(5):
                line = self.read_line()
                if not line:
                    continue
                print(f"<< {line}")
                if line.lower().startswith("ok"):
                    break
            print("Z motor current set to 200mA")

            # Set Z steps/mm — confirmed working via manual testing (M92 Z400).
            # 2mm lead screw, NEMA11. Fine-tune later if needed.
            self.send_gcode("M92 Z400")
            for _ in range(5):
                line = self.read_line()
                if not line:
                    continue
                print(f"<< {line}")
                if line.lower().startswith("ok"):
                    break
            print("Z steps/mm set to 400")

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
