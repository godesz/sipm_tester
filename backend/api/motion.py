"""
Motion control API endpoints for Marlin controller.
"""
from fastapi import APIRouter, HTTPException
from models.hardware import ConnectionRequest, ConnectionResponse, StatusResponse
from models.position import MoveRequest, MoveResponse, SetBoundsRequest
from hardware.marlin_controller import MarlinController
from config import config_manager


router = APIRouter(prefix="/api/motion", tags=["motion"])

# Global Marlin controller instance
marlin = MarlinController()


@router.post("/connect", response_model=ConnectionResponse)
async def connect(request: ConnectionRequest):
    """Connect to Marlin controller."""
    try:
        # Get port from config if not provided
        if not request.port:
            request.port = config_manager.get_config().hardware.marlin.port

        success = marlin.connect(
            port=request.port,
            baudrate=request.baudrate,
            timeout=request.timeout
        )

        if success:
            # Update bounds from config
            bounds = config_manager.get_marlin_bounds()
            for axis, limits in bounds.items():
                marlin.set_bounds(axis, limits["min"], limits["max"])

            return ConnectionResponse(status="ok", port=request.port)
        else:
            return ConnectionResponse(
                status="error",
                port=request.port,
                message="Failed to connect"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect():
    """Disconnect from Marlin controller."""
    try:
        marlin.disconnect()
        return {"status": "disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position")
async def get_position():
    """Get current position."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        position = marlin.query_position()
        return {"position": position}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move", response_model=MoveResponse)
async def move(request: MoveRequest):
    """Move an axis by relative distance."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        position = marlin.move_axis(
            axis=request.axis,
            distance=request.distance,
            feedrate=request.feedrate
        )

        return MoveResponse(status="ok", position=position)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/home")
async def home():
    """Home all axes."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        position = marlin.home()
        return {"status": "homed", "position": position}
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency_stop")
async def emergency_stop():
    """Activate emergency stop."""
    try:
        marlin.activate_emergency_stop()
        return {"status": "emergency_stop_active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear_emergency_stop")
async def clear_emergency_stop():
    """Clear emergency stop."""
    try:
        marlin.clear_emergency_stop()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_bounds")
async def set_bounds(request: SetBoundsRequest):
    """Set movement bounds for an axis."""
    try:
        marlin.set_bounds(request.axis, request.min, request.max)
        return {"status": "ok", "axis": request.axis, "min": request.min, "max": request.max}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get Marlin controller status."""
    try:
        status = marlin.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
