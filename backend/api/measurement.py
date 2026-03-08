"""
Measurement device API endpoints for diode testing and light control.
"""
from fastapi import APIRouter, HTTPException
from models.hardware import ConnectionRequest, ConnectionResponse
from models.measurement import SetLightRequest, DiodeTestResponse, ProbeRequest, ProbeResponse
from hardware.measurement_device import MeasurementDevice
from hardware.marlin_controller import MarlinController
from services import probing
from config import config_manager


router = APIRouter(prefix="/api/measurement", tags=["measurement"])

# Global measurement device instance
measurement = MeasurementDevice()


@router.post("/connect", response_model=ConnectionResponse)
async def connect(request: ConnectionRequest):
    """Connect to measurement device."""
    try:
        # Get port from config if not provided
        if not request.port:
            request.port = config_manager.get_config().hardware.measurement_device.port

        success = measurement.connect(
            port=request.port,
            baudrate=request.baudrate,
            timeout=request.timeout
        )

        if success:
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
    """Disconnect from measurement device."""
    try:
        measurement.disconnect()
        return {"status": "disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable_psu")
async def enable_psu():
    """Enable PSU for testing."""
    try:
        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        result = measurement.enable_psu()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_light")
async def set_light(request: SetLightRequest):
    """Set LED light mode and color."""
    try:
        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        result = measurement.set_light(
            mode=request.mode,
            r=request.r,
            g=request.g,
            b=request.b
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn_off_leds")
async def turn_off_leds():
    """Turn off all LEDs."""
    try:
        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        result = measurement.turn_off_leds()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test_diode", response_model=DiodeTestResponse)
async def test_diode():
    """Get diode measurement / connection state."""
    try:
        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        result = measurement.get_diode_measurement()

        return DiodeTestResponse(
            status=result["status"],
            connection_state=result.get("connection_state"),
            connection_name=result["connection_name"],
            is_connected=result.get("is_connected", False),
            raw_response=result.get("raw_response"),
            message=result.get("message")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/probe_z", response_model=ProbeResponse)
def probe_z(request: ProbeRequest):
    """
    Run Z-axis probing workflow.
    Moves Z down incrementally, testing connection at each step.
    """
    try:
        from .motion import marlin

        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        cfg = config_manager.get_config()
        probing_cfg = cfg.probing

        start_z = request.start_z
        if start_z is None:
            start_z = marlin.query_position().get("Z", probing_cfg.probe_start_z)

        step = request.rough_step or probing_cfg.probe_step

        prober = probing.ZAxisProber(marlin, measurement)
        result = prober.probe_to_contact(
            start_z=start_z,
            step=step,
            max_z=probing_cfg.max_probe_z,
        )

        return ProbeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/probe_sipm")
def probe_sipm(camera_id: int = 0):
    """
    Full SiPM test workflow: detect pads → apply pogo offset → probe Z until contact.
    """
    try:
        from .motion import marlin
        from .camera import camera

        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        prober = probing.ZAxisProber(marlin, measurement)
        result = prober.probe_sipm(camera, camera_id)

        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Probing failed"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get measurement device status."""
    try:
        status = measurement.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
