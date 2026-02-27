"""
Configuration manager with singleton pattern for thread-safe config access.
"""
import json
import threading
from pathlib import Path
from typing import Optional
from models.config import StationConfig


class ConfigManager:
    """
    Singleton configuration manager.
    Handles loading, saving, and thread-safe access to configuration.
    """

    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config_path = Path(__file__).parent / "config" / "station_config.json"
            self.config: StationConfig = StationConfig()
            self.access_lock = threading.RLock()
            self.initialized = True

            # Load config if file exists
            if self.config_path.exists():
                self.load()
            else:
                # Create default config
                self.save()

    def load(self) -> StationConfig:
        """
        Load configuration from JSON file.

        Returns:
            StationConfig: Loaded configuration
        """
        try:
            with self.access_lock:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.config = StationConfig(**data)
                print(f"Configuration loaded from {self.config_path}")
                return self.config
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            self.config = StationConfig()
            return self.config

    def save(self) -> bool:
        """
        Save current configuration to JSON file.

        Returns:
            bool: True if save successful
        """
        try:
            with self.access_lock:
                # Ensure config directory exists
                self.config_path.parent.mkdir(parents=True, exist_ok=True)

                # Save config
                with open(self.config_path, 'w') as f:
                    json.dump(
                        self.config.model_dump(),
                        f,
                        indent=2
                    )
                print(f"Configuration saved to {self.config_path}")
                return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_config(self) -> StationConfig:
        """
        Get current configuration.

        Returns:
            StationConfig: Current configuration
        """
        with self.access_lock:
            return self.config

    def update_config(self, **kwargs) -> bool:
        """
        Update configuration fields.

        Args:
            **kwargs: Fields to update

        Returns:
            bool: True if update successful
        """
        try:
            with self.access_lock:
                # Update config fields
                for key, value in kwargs.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

                # Save updated config
                self.save()
                return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def set_reference_point(self, x: float, y: float, z: float) -> bool:
        """
        Set tray corner reference point.

        Args:
            x, y, z: Reference point coordinates

        Returns:
            bool: True if successful
        """
        try:
            with self.access_lock:
                self.config.calibration.reference_point = {"x": x, "y": y, "z": z}
                self.save()
                print(f"Reference point set to: X={x}, Y={y}, Z={z}")
                return True
        except Exception as e:
            print(f"Error setting reference point: {e}")
            return False

    def set_camera_offset(self, x: float, y: float) -> bool:
        """
        Set camera-to-POGO offset.

        Args:
            x, y: Offset coordinates

        Returns:
            bool: True if successful
        """
        try:
            with self.access_lock:
                self.config.calibration.camera_to_pogo_offset = {"x": x, "y": y}
                self.save()
                print(f"Camera offset set to: X={x}, Y={y}")
                return True
        except Exception as e:
            print(f"Error setting camera offset: {e}")
            return False

    def update_ports(self, marlin_port: Optional[str] = None, measurement_port: Optional[str] = None) -> bool:
        """
        Update COM port settings.

        Args:
            marlin_port: Marlin COM port
            measurement_port: Measurement device COM port

        Returns:
            bool: True if successful
        """
        try:
            with self.access_lock:
                if marlin_port:
                    self.config.hardware.marlin.port = marlin_port
                if measurement_port:
                    self.config.hardware.measurement_device.port = measurement_port
                self.save()
                print(f"Ports updated: Marlin={marlin_port}, Measurement={measurement_port}")
                return True
        except Exception as e:
            print(f"Error updating ports: {e}")
            return False

    def update_tray(self, **kwargs) -> bool:
        """
        Update tray layout fields (columns, rows, pitch_x, pitch_y).
        Only provided fields are changed.
        """
        try:
            with self.access_lock:
                for key, value in kwargs.items():
                    if value is not None and hasattr(self.config.tray, key):
                        setattr(self.config.tray, key, value)
                self.save()
                print(f"Tray config updated: {kwargs}")
                return True
        except Exception as e:
            print(f"Error updating tray config: {e}")
            return False

    def set_tray_reference(self, x: float, y: float) -> bool:
        """Copy the current machine reference point into the tray config."""
        try:
            with self.access_lock:
                self.config.tray.reference_point = {"x": x, "y": y}
                self.save()
                print(f"Tray reference set to X={x}, Y={y}")
                return True
        except Exception as e:
            print(f"Error setting tray reference: {e}")
            return False

    def set_first_sipm(self, x: float, y: float) -> bool:
        """Save machine coordinates of the first SiPM (index 0)."""
        try:
            with self.access_lock:
                self.config.tray.first_sipm = {"x": x, "y": y}
                self.save()
                print(f"First SiPM set to X={x}, Y={y}")
                return True
        except Exception as e:
            print(f"Error setting first SiPM: {e}")
            return False

    def get_sipm_position(self, index: int) -> dict:
        """
        Compute machine coordinates for SiPM at the given 0-based index.
        Layout: row-major order, X varies first (columns), then Y (rows).
        """
        with self.access_lock:
            tray = self.config.tray
            total = tray.columns * tray.rows
            if index < 0 or index >= total:
                raise ValueError(
                    f"SiPM index {index} out of range "
                    f"(tray has {tray.columns}×{tray.rows} = {total} SiPMs)"
                )
            col = index % tray.columns
            row = index // tray.columns
            x = tray.first_sipm["x"] + col * tray.pitch_x
            y = tray.first_sipm["y"] + row * tray.pitch_y
            return {"index": index, "row": row, "col": col, "x": x, "y": y}

    def get_marlin_bounds(self):
        """Get Marlin movement bounds."""
        with self.access_lock:
            return self.config.hardware.marlin.bounds

    def get_detection_params(self):
        """Get detection parameters."""
        with self.access_lock:
            return self.config.detection

    def get_probing_params(self):
        """Get probing parameters."""
        with self.access_lock:
            return self.config.probing


# Global config manager instance
config_manager = ConfigManager()
