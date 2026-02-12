"""
Camera management using OpenCV.
Migrated and improved from old_backend.py lines 106-178.
"""
import cv2
import threading
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import os
import numpy as np
from .base import HardwareDevice


class CameraManager(HardwareDevice):
    """
    Manages USB cameras for streaming and high-resolution capture.
    Supports multiple cameras and resolution modes.
    """

    def __init__(self, capture_dir: str = "captures"):
        super().__init__()
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.camera_locks: Dict[int, threading.Lock] = {}
        self.capture_dir = capture_dir
        self.stream_resolution = (640, 480)  # Lower res for streaming
        self.capture_resolution = (1920, 1080)  # High res for detection

        # Create capture directory if it doesn't exist
        os.makedirs(self.capture_dir, exist_ok=True)

    def connect(self, **kwargs) -> bool:
        """
        Camera manager doesn't need explicit connection.
        Cameras are opened on demand.
        """
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Close all open cameras."""
        try:
            with self.lock:
                for cam_id, cam in list(self.cameras.items()):
                    if cam is not None and cam.isOpened():
                        cam.release()
                self.cameras.clear()
                self.camera_locks.clear()
                self.connected = False
                print("All cameras released")
                return True
        except Exception as e:
            print(f"Error releasing cameras: {e}")
            return False

    def list_cameras(self, max_devices: int = 10) -> List[int]:
        """
        List available camera indexes.

        Args:
            max_devices: Maximum number of devices to check (default: 10)

        Returns:
            List of available camera indexes
        """
        available = []
        for i in range(max_devices):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # CAP_DSHOW avoids warnings on Windows
            if cap is not None and cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def open_camera(self, camera_id: int, high_res: bool = False) -> cv2.VideoCapture:
        """
        Open a camera if not already open.

        Args:
            camera_id: Camera index
            high_res: If True, use high resolution for capture. If False, use streaming resolution.

        Returns:
            cv2.VideoCapture object

        Raises:
            RuntimeError: If camera cannot be opened
        """
        if camera_id not in self.cameras:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                raise RuntimeError(f"Camera {camera_id} not available")

            # Set resolution based on mode
            if high_res:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_resolution[1])
            else:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.stream_resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.stream_resolution[1])

            self.cameras[camera_id] = cap
            self.camera_locks[camera_id] = threading.Lock()
            print(f"Camera {camera_id} opened ({'high-res' if high_res else 'streaming'} mode)")

        return self.cameras[camera_id]

    def get_frame(self, camera_id: int = 0) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.

        Args:
            camera_id: Camera index (default: 0)

        Returns:
            Frame as numpy array, or None if failed
        """
        try:
            cam = self.open_camera(camera_id)

            if camera_id in self.camera_locks:
                with self.camera_locks[camera_id]:
                    success, frame = cam.read()
            else:
                success, frame = cam.read()

            if success:
                return frame
            return None
        except Exception as e:
            print(f"Error getting frame from camera {camera_id}: {e}")
            return None

    def gen_frames(self, camera_id: int = 0):
        """
        Generator for MJPEG streaming.
        Yields frame bytes in multipart format for HTTP streaming.

        Args:
            camera_id: Camera index (default: 0)

        Yields:
            MJPEG frame bytes
        """
        cam = self.open_camera(camera_id, high_res=False)

        while True:
            if camera_id in self.camera_locks:
                with self.camera_locks[camera_id]:
                    success, frame = cam.read()
            else:
                success, frame = cam.read()

            if not success:
                continue

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def capture_image(self, camera_id: int = 0, high_res: bool = True) -> Dict:
        """
        Capture a high-resolution image and save it to disk.

        Args:
            camera_id: Camera index (default: 0)
            high_res: Use high resolution (default: True)

        Returns:
            Dict with status and filename
        """
        try:
            # Open camera in high-res mode temporarily
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

            if high_res:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_resolution[1])
            else:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.stream_resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.stream_resolution[1])

            ret, frame = cap.read()
            cap.release()

            if not ret:
                return {"error": "Camera capture failed"}

            # Generate filename with timestamp
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{self.capture_dir}/cam{camera_id}_{ts}.png"

            # Save image
            cv2.imwrite(filename, frame)

            print(f"Image saved: {filename}")

            return {
                "status": "ok",
                "file": filename,
                "resolution": {
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def capture_for_detection(self, camera_id: int = 0) -> Optional[np.ndarray]:
        """
        Capture a high-resolution frame for SiPM detection.
        Does not save to disk.

        Args:
            camera_id: Camera index (default: 0)

        Returns:
            Frame as numpy array, or None if failed
        """
        try:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_resolution[1])

            ret, frame = cap.read()
            cap.release()

            if ret:
                return frame
            return None
        except Exception as e:
            print(f"Error capturing for detection: {e}")
            return None

    def set_stream_resolution(self, width: int, height: int):
        """Set streaming resolution."""
        self.stream_resolution = (width, height)
        print(f"Stream resolution set to {width}x{height}")

    def set_capture_resolution(self, width: int, height: int):
        """Set capture resolution."""
        self.capture_resolution = (width, height)
        print(f"Capture resolution set to {width}x{height}")

    def get_status(self) -> Dict:
        """Get camera manager status."""
        return {
            **super().get_status(),
            "open_cameras": list(self.cameras.keys()),
            "stream_resolution": self.stream_resolution,
            "capture_resolution": self.capture_resolution,
            "capture_dir": self.capture_dir
        }
