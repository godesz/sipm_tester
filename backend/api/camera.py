"""
Camera API endpoints for streaming, capture, and detection.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from hardware.camera import CameraManager
from models.measurement import DetectionResponse, SiPMDetection
from services import detection
from config import config_manager


router = APIRouter(prefix="/api/camera", tags=["camera"])

# Global camera manager instance
camera = CameraManager()


@router.get("/list")
async def list_cameras():
    """List available cameras."""
    try:
        available = camera.list_cameras()
        return {"available_cameras": available}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def stream(camera_id: int = Query(0, description="Camera index")):
    """Stream camera video as MJPEG."""
    try:
        return StreamingResponse(
            camera.gen_frames(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture")
async def capture(camera_id: int = 0):
    """Capture a high-resolution image and save to disk."""
    try:
        result = camera.capture_image(camera_id, high_res=True)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect", response_model=DetectionResponse)
async def detect(camera_id: int = 0):
    """
    Run SiPM detection on current camera frame.
    Returns list of detected pads with coordinates.
    """
    try:
        # Capture high-res frame
        frame = camera.capture_for_detection(camera_id)

        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to capture frame")

        # Get detection parameters from config
        detection_config = config_manager.get_detection_params()

        # Run detection
        detector = detection.SiPMDetector(detection_config)
        detections = detector.detect_pads(frame)

        # Convert to response model
        detection_objects = [
            SiPMDetection(**det) for det in detections
        ]

        return DetectionResponse(
            status="ok",
            detections=detection_objects,
            count=len(detection_objects)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get camera manager status."""
    try:
        status = camera.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch")
async def switch_camera(
    old_camera_id: int = Query(..., description="Current camera ID"),
    new_camera_id: int = Query(..., description="New camera ID")
):
    """
    Switch from one camera to another.
    Properly closes old camera before opening new one.
    """
    try:
        result = camera.switch_camera(old_camera_id, new_camera_id)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
