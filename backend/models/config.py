"""
Pydantic models for configuration schema.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class MarlinConfig(BaseModel):
    """Marlin controller configuration."""
    port: str = Field(default="COM4", description="COM port")
    baudrate: int = Field(default=115200, description="Serial baudrate")
    bounds: Dict[str, Dict[str, float]] = Field(
        default={
            "X": {"min": 0, "max": 300},
            "Y": {"min": 0, "max": 300},
            "Z": {"min": 0, "max": 10}
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


class TrayConfig(BaseModel):
    """
    Describes the physical SiPM tray layout.

    With reference_point, first_sipm, columns, rows, and the two pitches you
    can compute the machine coordinates of any SiPM by index (0-based):
        col = index % columns
        row = index // columns
        x   = first_sipm.x + col * pitch_x
        y   = first_sipm.y + row * pitch_y
    """
    reference_point: Dict[str, float] = Field(
        default={"x": 0.0, "y": 0.0},
        description="Tray corner reference (machine coords, set with SET REF)"
    )
    first_sipm: Dict[str, float] = Field(
        default={"x": 0.0, "y": 0.0},
        description="Machine coordinates of the first SiPM (index 0), set manually"
    )
    columns: int = Field(default=1, description="Number of SiPMs along X axis")
    rows: int = Field(default=1, description="Number of SiPMs along Y axis")
    pitch_x: float = Field(default=0.0, description="Center-to-center distance in X (mm)")
    pitch_y: float = Field(default=0.0, description="Center-to-center distance in Y (mm)")


class DetectionConfig(BaseModel):
    """OpenCV detection parameters for bright pad detection under colored lighting."""
    # Brightness-based detection (primary method for white/bright pads)
    brightness_threshold: int = Field(default=200, description="Min brightness (V channel, 0-255)")
    saturation_max: int = Field(default=100, description="Max saturation for bright pads (S channel, 0-255)")
    # Optional yellow hue range (secondary, for slightly colored pads)
    yellow_hsv_range: Dict[str, List[int]] = Field(
        default={
            "lower": [10, 30, 180],
            "upper": [50, 200, 255]
        },
        description="HSV range for yellowish pad detection"
    )
    use_yellow_detection: bool = Field(default=True, description="Also detect yellowish pads")
    # Area filters
    min_pad_area: int = Field(default=50, description="Minimum pad area in pixels")
    max_pad_area: int = Field(default=5000, description="Maximum pad area in pixels")
    # Pad size filter (post-detection)
    expected_pad_size: int = Field(default=60, description="Expected pad size in pixels (width & height)")
    pad_size_tolerance: float = Field(default=0.4, description="Size tolerance as fraction (0.4 = ±40%, so 36-84 px)")
    max_aspect_ratio: float = Field(default=1.5, description="Max aspect ratio (1.0 = perfect square)")
    # Center crop filter
    # The camera is centered over the SiPM.  Pads of neighboring SiPMs will
    # appear far from the image center.  Set to 0 to disable the filter.
    # With pads at ±50 px (X) and ±95 px (Y) the furthest valid pad is ~107 px
    # from center; a default of 150 px gives comfortable margin.
    max_distance_from_center: int = Field(default=150, description="Max pixel distance from image center (0 = disabled)")
    # Debug
    save_debug_image: bool = Field(default=True, description="Save debug image with detections")


class ProbingConfig(BaseModel):
    """Z-axis probing parameters."""
    rough_step: float = Field(default=1.0, description="Rough probing step in mm")
    fine_step: float = Field(default=0.1, description="Fine probing step in mm")
    safe_z_min: float = Field(default=0.0, description="Safe minimum Z position in mm")
    safe_travel_z: float = Field(default=10.0, description="Z position to retract to before XY travel (small Z = physically high = safe)")
    probe_start_z: float = Field(default=53.0, description="Z position to start probing from (safe height above SiPM surface)")
    probe_step: float = Field(default=0.5, description="Step size for probe_sipm workflow in mm")
    max_probe_z: float = Field(default=80.0, description="Maximum Z depth during probing (stop if reached without contact)")


class ExternalServiceConfig(BaseModel):
    """External measurement service configuration."""
    url: str = Field(default="http://localhost:8003", description="Base URL of the external measurement service")


class StationConfig(BaseModel):
    """Complete station configuration."""
    version: str = Field(default="1.0", description="Config version")
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    calibration: CalibrationData = Field(default_factory=CalibrationData)
    tray: TrayConfig = Field(default_factory=TrayConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    probing: ProbingConfig = Field(default_factory=ProbingConfig)
    external_service: ExternalServiceConfig = Field(default_factory=ExternalServiceConfig)


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


class UpdateTrayRequest(BaseModel):
    """Request to update tray layout parameters."""
    columns: Optional[int] = None
    rows: Optional[int] = None
    pitch_x: Optional[float] = None
    pitch_y: Optional[float] = None
