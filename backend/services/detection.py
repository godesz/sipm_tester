"""
OpenCV-based SiPM pad detection service.
Detects yellowish rectangular pads using color and shape analysis.
"""
import cv2
import numpy as np
from typing import List, Dict
from models.config import DetectionConfig


class SiPMDetector:
    """
    Detects SiPM pads in camera images using OpenCV.
    Uses HSV color space to find yellowish rectangular pads.
    """

    def __init__(self, config: DetectionConfig):
        """
        Initialize detector with configuration.

        Args:
            config: Detection configuration with HSV ranges and area limits
        """
        self.config = config
        self.lower_hsv = np.array(config.yellow_hsv_range["lower"])
        self.upper_hsv = np.array(config.yellow_hsv_range["upper"])
        self.min_area = config.min_pad_area
        self.max_area = config.max_pad_area

    def detect_pads(self, image: np.ndarray) -> List[Dict]:
        """
        Detect SiPM pads in the image.

        Args:
            image: Input image (BGR format)

        Returns:
            List of detection dictionaries with x, y, width, height, confidence
        """
        if image is None or image.size == 0:
            return []

        # Convert BGR to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for yellow color
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Morphological operations to clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Close small holes
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # Remove small noise

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter and extract detections
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self.min_area or area > self.max_area:
                continue

            # Check if rectangular (4 corners)
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

            # Accept rectangles (4 corners) or close approximations
            if len(approx) >= 4 and len(approx) <= 6:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate center coordinates
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)

                # Calculate confidence based on area (normalized to 0-1)
                confidence = min(area / self.max_area, 1.0)

                detections.append({
                    "x": center_x,
                    "y": center_y,
                    "width": int(w),
                    "height": int(h),
                    "confidence": float(confidence)
                })

        # Sort detections by confidence (highest first)
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        return detections

    def visualize_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw detection results on image for visualization.

        Args:
            image: Input image (BGR format)
            detections: List of detections from detect_pads()

        Returns:
            Image with detections drawn
        """
        vis_image = image.copy()

        for detection in detections:
            x = detection["x"]
            y = detection["y"]
            w = detection["width"]
            h = detection["height"]
            confidence = detection["confidence"]

            # Draw bounding box
            x1 = x - w // 2
            y1 = y - h // 2
            x2 = x + w // 2
            y2 = y + h // 2
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw center circle
            cv2.circle(vis_image, (x, y), 5, (0, 0, 255), -1)

            # Draw confidence label
            label = f"{confidence:.2f}"
            cv2.putText(vis_image, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return vis_image
