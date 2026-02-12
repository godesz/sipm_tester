"""
Z-axis probing service for POGO pin contact detection.
Implements incremental probing workflow with rough and fine steps.
"""
import time
from typing import Dict
from hardware.marlin_controller import MarlinController
from hardware.measurement_device import MeasurementDevice


class ZAxisProber:
    """
    Handles Z-axis probing workflow.
    Moves Z down incrementally, testing connection at each step.
    """

    def __init__(self, marlin: MarlinController, measurement: MeasurementDevice):
        """
        Initialize prober with hardware instances.

        Args:
            marlin: Marlin controller for Z movement
            measurement: Measurement device for connection testing
        """
        self.marlin = marlin
        self.measurement = measurement

    async def probe_to_contact(
        self,
        start_z: float,
        rough_step: float = 1.0,
        fine_step: float = 0.1,
        safe_min: float = 40.0
    ) -> Dict:
        """
        Probe Z axis until contact is detected.

        Workflow:
        1. Phase 1: Rough probing - move down in rough_step increments
        2. When contact detected, back up
        3. Phase 2: Fine probing - move down in fine_step increments for precise contact
        4. Stop if safe_min is reached

        Args:
            start_z: Starting Z position (should be above surface)
            rough_step: Step size for rough probing in mm (default: 1.0)
            fine_step: Step size for fine probing in mm (default: 0.1)
            safe_min: Safe minimum Z position in mm (default: 40.0)

        Returns:
            Dict with status, final_z, connection_state, steps_taken, message
        """
        current_z = start_z
        steps_taken = 0

        print(f"Starting Z-axis probing from Z={start_z:.2f}mm")

        try:
            # Phase 1: Rough probing
            print("Phase 1: Rough probing...")
            while current_z > safe_min:
                # Move down by rough step
                self.marlin.move_axis("Z", -rough_step)
                current_z -= rough_step
                steps_taken += 1
                time.sleep(0.1)

                # Test connection
                result = self.measurement.get_diode_measurement()

                print(f"Z={current_z:.2f}mm, State: {result['connection_name']}")

                # Check if contact detected (state = 1: OK/connected)
                if result.get("is_connected", False):
                    print("Contact detected in rough probing!")

                    # Back up by 2x rough step
                    backup_distance = rough_step * 2
                    self.marlin.move_axis("Z", backup_distance)
                    current_z += backup_distance
                    steps_taken += 1
                    time.sleep(0.1)

                    print(f"Backed up to Z={current_z:.2f}mm")
                    break
            else:
                # Reached safe minimum without contact
                return {
                    "status": "failed",
                    "final_z": current_z,
                    "connection_state": "open",
                    "steps_taken": steps_taken,
                    "message": f"Reached safe minimum ({safe_min}mm) without detecting contact"
                }

            # Phase 2: Fine probing
            print("Phase 2: Fine probing...")
            while current_z > safe_min:
                # Move down by fine step
                self.marlin.move_axis("Z", -fine_step)
                current_z -= fine_step
                steps_taken += 1
                time.sleep(0.1)

                # Test connection
                result = self.measurement.get_diode_measurement()

                print(f"Z={current_z:.2f}mm, State: {result['connection_name']}")

                # Check if contact confirmed
                if result.get("is_connected", False):
                    print(f"Contact confirmed at Z={current_z:.2f}mm")

                    return {
                        "status": "connected",
                        "final_z": current_z,
                        "connection_state": result["connection_name"],
                        "steps_taken": steps_taken,
                        "message": f"Contact established at Z={current_z:.2f}mm after {steps_taken} steps"
                    }

            # Reached safe minimum in fine probing
            return {
                "status": "failed",
                "final_z": current_z,
                "connection_state": "open",
                "steps_taken": steps_taken,
                "message": f"Reached safe minimum ({safe_min}mm) in fine probing without confirming contact"
            }

        except Exception as e:
            return {
                "status": "error",
                "final_z": current_z,
                "connection_state": "error",
                "steps_taken": steps_taken,
                "message": f"Probing error: {str(e)}"
            }
