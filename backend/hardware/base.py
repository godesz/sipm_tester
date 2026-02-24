"""
Base hardware abstraction class for all hardware devices.
"""
from abc import ABC, abstractmethod
import threading
from typing import Any, Dict


class HardwareDevice(ABC):
    """
    Abstract base class for hardware devices.
    Provides common interface for connection management and thread-safe operations.
    """

    def __init__(self):
        self.connected = False
        self.lock = threading.RLock()

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        Connect to the hardware device.

        Args:
            **kwargs: Device-specific connection parameters (port, baudrate, etc.)

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the hardware device.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    def is_connected(self) -> bool:
        """
        Check if the device is currently connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected

    def _ensure_connected(self):
        """
        Ensure the device is connected before operations.

        Raises:
            RuntimeError: If device is not connected
        """
        if not self.is_connected():
            raise RuntimeError(f"{self.__class__.__name__} is not connected")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current device status.

        Returns:
            Dict with status information
        """
        return {
            "device": self.__class__.__name__,
            "connected": self.connected
        }
