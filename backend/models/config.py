"""
Pydantic models for configuration schema.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class MarlinConfig(BaseModel):
    """Marlin controller configuration."""
    port: str = Field(default="COM3", description="COM port")
    baudrate: int = Field(default=115200, description="Serial baudrate")
    bounds: Dict[str, Dict[str, float]] = Field(
        default={
            "X": {"min": 0, "max": 300},
            "Y": {"min": 0, "max": 300},
            "Z": {"min": 40, "max": 50}
        },
        description="Movement bounds for each axis"
    )


class CameraConfig(BaseModel):
    """Camera configuration."""
    default_id: int = Field(default=0, description="Default camera index")
    stream_resolution: List[int] = Field(
        default=[640, 480],
        description="Streaming resolution [width, height]"
    )
    capture_resolution: List[int] = Field(
        default=[1920, 1080],
        description="Capture resolution [width, height]"
    )


class MeasurementDeviceConfig(BaseModel):
    """Measurement device configuration."""
    port: str = Field(default="COM5", description="COM port")
    baudrate: int = Field(default=115200, description="Serial baudrate")


class HardwareConfig(BaseModel):
    """All hardware configurations."""
    marlin: MarlinConfig = Field(default_factory=MarlinConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    measurement_device: MeasurementDeviceConfig = Field(default_factory=MeasurementDeviceConfig)


class CalibrationData(BaseModel):
    """Calibration data (reference point and offset)."""
    reference_point: Dict[str, float] = Field(
        default={"x": 0, "y": 0, "z": 0},
        description="Tray corner reference point"
    )
    camera_to_pogo_offset: Dict[str, float] = Field(
        default={"x": 0, "y": 0},
        description="Offset from camera center to POGO pins"
    )


class DetectionConfig(BaseModel):
    """OpenCV detection parameters."""
    yellow_hsv_range: Dict[str, List[int]] = Field(
        default={
            "lower": [20, 100, 100],
            "upper": [40, 255, 255]
        },
        description="HSV range for yellow color detection"
    )
    min_pad_area: int = Field(default=100, description="Minimum pad area in pixels")
    max_pad_area: int = Field(default=10000, description="Maximum pad area in pixels")


class ProbingConfig(BaseModel):
    """Z-axis probing parameters."""
    rough_step: float = Field(default=1.0, description="Rough probing step in mm")
    fine_step: float = Field(default=0.1, description="Fine probing step in mm")
    safe_z_min: float = Field(default=40.0, description="Safe minimum Z position in mm")


class StationConfig(BaseModel):
    """Complete station configuration."""
    version: str = Field(default="1.0", description="Config version")
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    calibration: CalibrationData = Field(default_factory=CalibrationData)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    probing: ProbingConfig = Field(default_factory=ProbingConfig)


class SetReferencePointRequest(BaseModel):
    """Request to set reference point."""
    x: float
    y: float
    z: float


class SetCameraOffsetRequest(BaseModel):
    """Request to set camera-to-POGO offset."""
    x: float
    y: float


class UpdatePortsRequest(BaseModel):
    """Request to update COM port settings."""
    marlin_port: Optional[str] = None
    measurement_port: Optional[str] = None
