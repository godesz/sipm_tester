"""
Pydantic models for measurement and detection-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class SetLightRequest(BaseModel):
    """Request to set LED light."""
    mode: int = Field(..., description="Light mode: 1=left, 2=right, 3=all", ge=1, le=3)
    r: int = Field(..., description="Red value (0-255)", ge=0, le=255)
    g: int = Field(..., description="Green value (0-255)", ge=0, le=255)
    b: int = Field(..., description="Blue value (0-255)", ge=0, le=255)


class DiodeTestResponse(BaseModel):
    """Response from diode test."""
    status: str
    connection_state: Optional[int]
    connection_name: str
    is_connected: bool
    raw_response: Optional[str]
    message: Optional[str] = None


class SiPMDetection(BaseModel):
    """Single SiPM pad detection."""
    x: int = Field(..., description="Center X coordinate in pixels")
    y: int = Field(..., description="Center Y coordinate in pixels")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")
    confidence: float = Field(..., description="Detection confidence (0-1)")


class DetectionResponse(BaseModel):
    """Response from SiPM detection."""
    status: str
    detections: List[SiPMDetection]
    count: int
    message: Optional[str] = None


class ProbeRequest(BaseModel):
    """Request to start Z-axis probing."""
    start_z: Optional[float] = Field(None, description="Starting Z position (current if None)")
    rough_step: float = Field(default=1.0, description="Rough probing step in mm")
    fine_step: float = Field(default=0.1, description="Fine probing step in mm")
    safe_z_min: float = Field(default=40.0, description="Safe minimum Z position in mm")


class ProbeResponse(BaseModel):
    """Response from Z-axis probing."""
    status: str
    final_z: Optional[float]
    connection_state: Optional[str]
    steps_taken: int
    message: Optional[str] = None
