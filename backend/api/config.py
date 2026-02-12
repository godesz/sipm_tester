"""
Configuration API endpoints for managing station settings.
"""
from fastapi import APIRouter, HTTPException
from models.config import StationConfig, SetReferencePointRequest, SetCameraOffsetRequest, UpdatePortsRequest
from config import config_manager


router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/", response_model=StationConfig)
async def get_config():
    """Get current configuration."""
    try:
        config = config_manager.get_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reference_point")
async def set_reference_point(request: SetReferencePointRequest):
    """Set tray corner reference point."""
    try:
        success = config_manager.set_reference_point(
            x=request.x,
            y=request.y,
            z=request.z
        )

        if success:
            return {
                "status": "ok",
                "reference_point": {"x": request.x, "y": request.y, "z": request.z}
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set reference point")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera_offset")
async def set_camera_offset(request: SetCameraOffsetRequest):
    """Set camera-to-POGO offset."""
    try:
        success = config_manager.set_camera_offset(
            x=request.x,
            y=request.y
        )

        if success:
            return {
                "status": "ok",
                "camera_offset": {"x": request.x, "y": request.y}
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set camera offset")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ports")
async def update_ports(request: UpdatePortsRequest):
    """Update COM port settings."""
    try:
        success = config_manager.update_ports(
            marlin_port=request.marlin_port,
            measurement_port=request.measurement_port
        )

        if success:
            return {
                "status": "ok",
                "marlin_port": request.marlin_port,
                "measurement_port": request.measurement_port
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update ports")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_config():
    """Reload configuration from file."""
    try:
        config = config_manager.load()
        return {"status": "ok", "message": "Configuration reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_config():
    """Save current configuration to file."""
    try:
        success = config_manager.save()

        if success:
            return {"status": "ok", "message": "Configuration saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
