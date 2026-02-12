"""
Pydantic models for position and movement-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional


class Position(BaseModel):
    """3D position coordinates."""
    X: float = Field(default=0.0, description="X coordinate in mm")
    Y: float = Field(default=0.0, description="Y coordinate in mm")
    Z: float = Field(default=0.0, description="Z coordinate in mm")


class MoveRequest(BaseModel):
    """Request to move an axis."""
    axis: str = Field(..., description="Axis to move (X, Y, or Z)")
    distance: float = Field(..., description="Distance to move in mm (positive or negative)")
    feedrate: int = Field(default=5000, description="Movement speed in mm/min")


class MoveResponse(BaseModel):
    """Response after movement."""
    status: str
    position: Dict[str, float]
    message: Optional[str] = None


class Bounds(BaseModel):
    """Movement bounds for an axis."""
    min: float = Field(..., description="Minimum position in mm")
    max: float = Field(..., description="Maximum position in mm")


class SetBoundsRequest(BaseModel):
    """Request to set axis bounds."""
    axis: str = Field(..., description="Axis (X, Y, or Z)")
    min: float = Field(..., description="Minimum position in mm")
    max: float = Field(..., description="Maximum position in mm")
