"""
Motion control API endpoints for Marlin controller.

NOTE: All endpoints use plain `def` (not `async def`) so FastAPI routes them
to a thread pool. This is required because the handlers call blocking serial
I/O and hold threading.RLock. Using `async def` with blocking code would run
everything on the event loop's single thread, causing deadlocks when multiple
requests arrive concurrently (e.g. position polling + set_reference).
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
def connect(request: ConnectionRequest):
    """Connect to Marlin controller."""
    try:
        if not request.port:
            request.port = config_manager.get_config().hardware.marlin.port

        success = marlin.connect(
            port=request.port,
            baudrate=request.baudrate,
            timeout=request.timeout
        )

        if success:
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
def disconnect():
    """Disconnect from Marlin controller."""
    try:
        marlin.disconnect()
        return {"status": "disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position")
def get_position(fresh: bool = False):
    """
    Get current position.

    By default returns the cached position (updated after every move) without
    sending M114 — this avoids flooding the serial port during UI polling.
    Pass ?fresh=true to force an M114 query from the device.
    """
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        position = marlin.query_position() if fresh else marlin.position
        return {"position": position}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move", response_model=MoveResponse)
def move(request: MoveRequest):
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
def home():
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
def emergency_stop():
    """Activate emergency stop."""
    try:
        marlin.activate_emergency_stop()
        return {"status": "emergency_stop_active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear_emergency_stop")
def clear_emergency_stop():
    """Clear emergency stop."""
    try:
        marlin.clear_emergency_stop()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_bounds")
def set_bounds(request: SetBoundsRequest):
    """Set movement bounds for an axis."""
    try:
        marlin.set_bounds(request.axis, request.min, request.max)
        return {"status": "ok", "axis": request.axis, "min": request.min, "max": request.max}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_reference")
def set_reference():
    """Save current position as the tray reference point."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        # Use cached position — no serial I/O needed, avoids lock contention
        pos = marlin.position
        config_manager.set_reference_point(pos["X"], pos["Y"], pos.get("Z", 0.0))
        ref = {"x": pos["X"], "y": pos["Y"], "z": pos.get("Z", 0.0)}
        print(f"Reference point saved: {ref}")
        return {"status": "ok", "reference_point": ref}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_first_sipm")
def set_first_sipm():
    """Save current position as the first SiPM location (index 0) in the tray."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        pos = marlin.position
        config_manager.set_first_sipm(pos["X"], pos["Y"])
        # Keep tray reference_point in sync with the machine reference
        ref = config_manager.get_config().calibration.reference_point
        config_manager.set_tray_reference(ref["x"], ref["y"])
        result = {"x": pos["X"], "y": pos["Y"]}
        print(f"First SiPM saved: {result}")
        return {"status": "ok", "first_sipm": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sipm_position")
def sipm_position(index: int):
    """
    Compute machine coordinates for a SiPM by its 0-based index.
    Does NOT move the machine — use /move or /go_reference for that.
    """
    try:
        pos = config_manager.get_sipm_position(index)
        return {"status": "ok", "sipm": pos}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go_sipm")
def go_sipm(index: int):
    """Move to the machine coordinates of SiPM at the given 0-based index."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        pos = config_manager.get_sipm_position(index)
        new_pos = marlin.move_to_absolute(x=pos["x"], y=pos["y"])
        return {"status": "ok", "index": index, "position": new_pos}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go_sipm_rc")
def go_sipm_rc(col: int, row: int):
    """Move to SiPM at (col, row) — col is 0-based X index, row is 0-based Y index."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        tray = config_manager.get_config().tray
        if col < 0 or col >= tray.columns:
            raise HTTPException(status_code=400, detail=f"Column {col} out of range (0–{tray.columns - 1})")
        if row < 0 or row >= tray.rows:
            raise HTTPException(status_code=400, detail=f"Row {row} out of range (0–{tray.rows - 1})")

        index = col + row * tray.columns
        x = tray.first_sipm["x"] + col * tray.pitch_x
        y = tray.first_sipm["y"] + row * tray.pitch_y
        new_pos = marlin.move_to_absolute(x=x, y=y)
        return {"status": "ok", "col": col, "row": row, "index": index, "position": new_pos}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go_reference")
def go_reference():
    """Move to the saved tray reference point."""
    try:
        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        ref = config_manager.get_config().calibration.reference_point
        if ref["x"] == 0 and ref["y"] == 0:
            raise HTTPException(status_code=400, detail="No reference point set yet")

        position = marlin.move_to_absolute(x=ref["x"], y=ref["y"])
        return {"status": "ok", "position": position}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
def get_status():
    """Get Marlin controller status."""
    try:
        status = marlin.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
