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
        self.camera_modes: Dict[int, str] = {}  # Track 'stream' or 'capture' mode
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
        """Close all open cameras and clean up tracking."""
        try:
            with self.lock:
                for cam_id, cam in list(self.cameras.items()):
                    if cam is not None and cam.isOpened():
                        cam.release()
                self.cameras.clear()
                self.camera_locks.clear()
                self.camera_modes.clear()  # Clear mode tracking
                self.connected = False
                print("All cameras released")
                return True
        except Exception as e:
            print(f"Error releasing cameras: {e}")
            return False

    def close_camera(self, camera_id: int) -> bool:
        """
        Safely close a specific camera with proper locking.

        Args:
            camera_id: Camera index to close

        Returns:
            bool: True if closed successfully, False if not open
        """
        if camera_id not in self.cameras:
            return False

        if camera_id in self.camera_locks:
            with self.camera_locks[camera_id]:
                if self.cameras[camera_id] is not None and self.cameras[camera_id].isOpened():
                    self.cameras[camera_id].release()
                    print(f"Camera {camera_id} closed")

        del self.cameras[camera_id]
        if camera_id in self.camera_locks:
            del self.camera_locks[camera_id]
        if camera_id in self.camera_modes:
            del self.camera_modes[camera_id]

        return True

    def switch_camera(self, old_camera_id: int, new_camera_id: int) -> Dict:
        """
        Switch from one camera to another, closing old camera first.

        Args:
            old_camera_id: Currently active camera ID
            new_camera_id: New camera ID to switch to

        Returns:
            Dict with status
        """
        try:
            if old_camera_id != new_camera_id:
                self.close_camera(old_camera_id)
                print(f"Switched from camera {old_camera_id} to {new_camera_id}")

            return {"status": "ok", "current_camera": new_camera_id}
        except Exception as e:
            return {"error": str(e)}

    def list_cameras(self, max_devices: int = 4) -> List[int]:
        """
        List available camera indexes.
        Skips cameras that are already open to avoid conflicts.

        Args:
            max_devices: Maximum number of devices to check (default: 4)

        Returns:
            List of available camera indexes
        """
        available = []
        for i in range(max_devices):
            # If camera is already open and working, it's available
            if i in self.cameras and self.cameras[i].isOpened():
                available.append(i)
                continue

            # Try to open camera to check availability
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap is not None and cap.isOpened():
                    available.append(i)
                    cap.release()
            except Exception:
                pass
        return available

    def open_camera(self, camera_id: int, high_res: bool = False) -> cv2.VideoCapture:
        """
        Open camera with resolution mode checking.
        Automatically closes and reopens if mode switch needed.

        Args:
            camera_id: Camera index
            high_res: If True, use capture resolution. If False, use stream resolution.

        Returns:
            cv2.VideoCapture object

        Raises:
            RuntimeError: If camera cannot be opened
        """
        target_mode = "capture" if high_res else "stream"

        # Check if camera already open
        if camera_id in self.cameras:
            current_mode = self.camera_modes.get(camera_id, None)

            # Already in correct mode - return existing
            if current_mode == target_mode:
                return self.cameras[camera_id]

            # Wrong mode - close and reopen
            print(f"Camera {camera_id} switching from {current_mode} to {target_mode} mode")
            self.close_camera(camera_id)

        # Open camera with DirectShow backend
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

        # Store camera and track its mode
        self.cameras[camera_id] = cap
        self.camera_locks[camera_id] = threading.Lock()
        self.camera_modes[camera_id] = target_mode

        print(f"Camera {camera_id} opened in {target_mode} mode")

        return cap

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
        Generator for MJPEG streaming with thread safety.
        Gracefully handles camera being closed during streaming.

        Args:
            camera_id: Camera index (default: 0)

        Yields:
            MJPEG frame bytes
        """
        try:
            cam = self.open_camera(camera_id, high_res=False)
        except RuntimeError as e:
            print(f"Failed to open camera {camera_id}: {e}")
            return

        while True:
            # Camera might be closed by another operation
            if camera_id not in self.cameras:
                print(f"Camera {camera_id} was closed, stopping stream")
                break

            if camera_id in self.camera_locks:
                with self.camera_locks[camera_id]:
                    # Check again inside lock
                    if camera_id not in self.cameras or not self.cameras[camera_id].isOpened():
                        break
                    success, frame = self.cameras[camera_id].read()
            else:
                break

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
        Capture high-resolution image using unified camera management.

        Args:
            camera_id: Camera index (default: 0)
            high_res: Use high resolution (default: True)

        Returns:
            Dict with status and filename
        """
        try:
            # Use unified camera management (handles mode switching)
            cap = self.open_camera(camera_id, high_res=high_res)

            # Thread-safe capture
            if camera_id in self.camera_locks:
                with self.camera_locks[camera_id]:
                    ret, frame = cap.read()
            else:
                ret, frame = cap.read()

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
        Capture high-resolution frame for detection using unified management.

        Args:
            camera_id: Camera index (default: 0)

        Returns:
            Frame as numpy array, or None if failed
        """
        try:
            # Use unified camera management with high-res mode
            cap = self.open_camera(camera_id, high_res=True)

            # Thread-safe capture
            if camera_id in self.camera_locks:
                with self.camera_locks[camera_id]:
                    ret, frame = cap.read()
            else:
                ret, frame = cap.read()

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
