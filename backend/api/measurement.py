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
async def probe_z(request: ProbeRequest):
    """
    Run Z-axis probing workflow.
    Moves Z down incrementally, testing connection at each step.
    """
    try:
        # Import marlin from motion API
        from .motion import marlin

        if not marlin.is_connected():
            raise HTTPException(status_code=400, detail="Marlin not connected")

        if not measurement.is_connected():
            raise HTTPException(status_code=400, detail="Measurement device not connected")

        # Get probing parameters
        probing_config = config_manager.get_probing_params()

        # Use config values if not provided in request
        rough_step = request.rough_step or probing_config.rough_step
        fine_step = request.fine_step or probing_config.fine_step
        safe_z_min = request.safe_z_min or probing_config.safe_z_min

        # Get start Z position (current if not provided)
        start_z = request.start_z
        if start_z is None:
            current_pos = marlin.query_position()
            start_z = current_pos.get("Z", 0)

        # Run probing
        prober = probing.ZAxisProber(marlin, measurement)
        result = await prober.probe_to_contact(
            start_z=start_z,
            rough_step=rough_step,
            fine_step=fine_step,
            safe_min=safe_z_min
        )

        return ProbeResponse(**result)
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
