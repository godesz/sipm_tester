"""
Z-axis probing service for POGO pin contact detection.

Z axis orientation (after motor coil swap):
  Z+ (positive step) = physical DOWN toward the SiPM
  Z- (negative step) = physical UP away from the SiPM
  Z=0 at top (endstop); Z increases downward.

probe_sipm workflow:
  1. Run camera detection to confirm pads are visible
  2. Move XY: apply camera-to-pogo offset so POGO pins are over the SiPM
  3. Move Z to probe_start_z (safe height just above SiPM surface)
  4. Step Z down (+step = physical down) until diode contact detected
"""
import time
from typing import Dict, List, Optional
from hardware.marlin_controller import MarlinController
from hardware.measurement_device import MeasurementDevice


class ZAxisProber:
    """Handles Z-axis probing and the full SiPM test workflow."""

    def __init__(self, marlin: MarlinController, measurement: MeasurementDevice):
        self.marlin = marlin
        self.measurement = measurement

    def probe_to_contact(
        self,
        start_z: float = 53.0,
        step: float = 0.5,
        max_z: float = 80.0,
    ) -> Dict:
        """
        Move Z downward from start_z in step increments until diode contact.

        Z+ = physical DOWN on this machine (toward SiPM).

        Args:
            start_z: Z position to start from (safe height above SiPM surface)
            step:    Step size in mm (positive = physically down)
            max_z:   Abort if this Z is reached without contact

        Returns:
            Dict with status, final_z, connection_state, steps_taken, message
        """
        steps_taken = 0

        print(f"Probing: moving to start Z={start_z:.2f}mm")
        self.marlin.move_to_absolute(z=start_z)
        time.sleep(0.5)  # Settle before probing

        current_z = self.marlin.position.get("Z", start_z)

        print(f"Probing: stepping down {step}mm at a time (max Z={max_z:.1f}mm)")

        try:
            while current_z < max_z:
                # Move DOWN (positive step = physical down)
                self.marlin.move_axis("Z", step)
                current_z += step
                steps_taken += 1
                time.sleep(0.15)  # Wait for movement and settle

                result = self.measurement.get_diode_measurement()
                print(f"  Z={current_z:.2f}mm  →  {result['connection_name']}")

                if result.get("is_connected", False):
                    print(f"Contact detected at Z={current_z:.2f}mm")
                    return {
                        "status": "connected",
                        "final_z": current_z,
                        "connection_state": result["connection_name"],
                        "steps_taken": steps_taken,
                        "message": f"Contact at Z={current_z:.2f}mm after {steps_taken} steps",
                    }

            return {
                "status": "failed",
                "final_z": current_z,
                "connection_state": "open",
                "steps_taken": steps_taken,
                "message": f"No contact found (max depth Z={max_z:.1f}mm reached)",
            }

        except Exception as e:
            return {
                "status": "error",
                "final_z": current_z,
                "connection_state": "error",
                "steps_taken": steps_taken,
                "message": f"Probing error: {str(e)}",
            }

    def probe_sipm(self, camera, camera_id: int = 0) -> Dict:
        """
        Full SiPM test workflow from the current XY position:
          1. Detect pads via camera (confirms camera is over SiPM)
          2. Apply camera-to-pogo offset — moves POGO pins over the SiPM
          3. Probe Z until diode contact

        Args:
            camera:     CameraManager instance
            camera_id:  Camera index to use

        Returns:
            Dict with status, detections, pogo_x/y, final_z, message
        """
        from config import config_manager
        from services.detection import SiPMDetector

        cfg = config_manager.get_config()
        probing_cfg = cfg.probing
        offset = cfg.calibration.camera_to_pogo_offset

        # --- Step 1: Detect pads ---
        print("probe_sipm: capturing frame for detection...")
        frame = camera.capture_for_detection(camera_id)

        # Release camera immediately so the live stream can recover
        camera.close_camera(camera_id)

        if frame is None:
            return {"status": "error", "message": "Camera capture failed"}

        detector = SiPMDetector(cfg.detection)
        detections = detector.detect_pads(frame)

        if len(detections) == 0:
            return {
                "status": "error",
                "message": "No SiPM pads detected. Check camera position and lighting.",
                "detections": 0,
            }

        print(f"probe_sipm: {len(detections)} pad(s) detected")

        # --- Step 2: Move POGO pins over SiPM ---
        pos = self.marlin.position
        pogo_x = pos["X"] + offset["x"]
        pogo_y = pos["Y"] + offset["y"]

        print(f"probe_sipm: moving to pogo position X={pogo_x:.2f} Y={pogo_y:.2f}")
        self.marlin.move_to_absolute(x=pogo_x, y=pogo_y)
        time.sleep(0.3)

        # --- Step 3: Probe Z ---
        probe_result = self.probe_to_contact(
            start_z=probing_cfg.probe_start_z,
            step=probing_cfg.probe_step,
            max_z=probing_cfg.max_probe_z,
        )

        # --- Step 4: Restore LEDs (measurement turns them off) ---
        self.measurement.restore_light()

        return {
            **probe_result,
            "detections": len(detections),
            "pogo_x": pogo_x,
            "pogo_y": pogo_y,
        }
