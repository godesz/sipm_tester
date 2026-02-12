"""
Pydantic models for hardware-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ConnectionRequest(BaseModel):
    """Request to connect to a hardware device."""
    port: str = Field(..., description="COM port (e.g., COM3, COM5)")
    baudrate: int = Field(default=115200, description="Serial baudrate")
    timeout: float = Field(default=1.0, description="Serial timeout in seconds")


class ConnectionResponse(BaseModel):
    """Response after connection attempt."""
    status: str = Field(..., description="Connection status (ok, error)")
    port: Optional[str] = Field(None, description="Connected port")
    message: Optional[str] = Field(None, description="Error message if failed")


class StatusResponse(BaseModel):
    """Hardware device status."""
    device: str
    connected: bool
