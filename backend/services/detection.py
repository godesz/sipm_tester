"""
OpenCV-based SiPM pad detection service.
Detects bright/white pads under colored (purple) lighting using
brightness + saturation analysis.
"""
import cv2
import numpy as np
from typing import List, Dict
from datetime import datetime
import os
from models.config import DetectionConfig


class SiPMDetector:
    """
    Detects SiPM pads in camera images using OpenCV.

    Under purple LED lighting, pads glow bright white/yellowish while
    the background is purple. Detection uses:
    1. Brightness filter (high V) - pads are the brightest spots
    2. Saturation filter (low S) - white has low saturation vs purple
    3. Optional yellow hue filter - catches slightly colored pads
    """

    def __init__(self, config: DetectionConfig):
        self.config = config
        self.debug_dir = "captures/debug"
        os.makedirs(self.debug_dir, exist_ok=True)

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
        h, s, v = cv2.split(hsv)

        # === Pass 1: Brightness-based detection ===
        # Find bright spots with low saturation (white/near-white pads)
        bright_mask = cv2.inRange(
            hsv,
            np.array([0, 0, self.config.brightness_threshold]),
            np.array([180, self.config.saturation_max, 255])
        )

        # === Pass 2: Yellow hue detection (optional) ===
        if self.config.use_yellow_detection:
            lower = np.array(self.config.yellow_hsv_range["lower"])
            upper = np.array(self.config.yellow_hsv_range["upper"])
            yellow_mask = cv2.inRange(hsv, lower, upper)
            # Combine both masks
            combined_mask = cv2.bitwise_or(bright_mask, yellow_mask)
        else:
            combined_mask = bright_mask

        # === Morphological cleanup ===
        # Use smaller kernel for small pads
        kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        # Close small gaps within pads
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_small)
        # Remove small noise
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel_small)
        # Dilate slightly to connect broken pad edges
        combined_mask = cv2.dilate(combined_mask, kernel_small, iterations=1)

        # === Find contours ===
        contours, _ = cv2.findContours(
            combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # === Filter and extract detections ===
        img_h, img_w = image.shape[:2]
        img_cx = img_w / 2
        img_cy = img_h / 2
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self.config.min_pad_area or area > self.config.max_pad_area:
                continue

            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by expected pad size (~60x60 px)
            expected = self.config.expected_pad_size
            tolerance = self.config.pad_size_tolerance
            min_size = expected * (1 - tolerance)
            max_size = expected * (1 + tolerance)

            if w < min_size or w > max_size or h < min_size or h > max_size:
                continue

            # Filter by aspect ratio (pads should be roughly square)
            aspect_ratio = max(w, h) / max(min(w, h), 1)
            if aspect_ratio > self.config.max_aspect_ratio:
                continue

            # Calculate center coordinates
            center_x = int(x + w / 2)
            center_y = int(y + h / 2)

            # Filter by distance from image center (removes pads from neighboring SiPMs)
            if self.config.max_distance_from_center > 0:
                dist = ((center_x - img_cx) ** 2 + (center_y - img_cy) ** 2) ** 0.5
                if dist > self.config.max_distance_from_center:
                    continue

            # Calculate confidence based on:
            # - brightness of the pad region (higher = better)
            # - how "white" it is (lower saturation = better)
            roi_v = v[y:y+h, x:x+w]
            roi_s = s[y:y+h, x:x+w]
            avg_brightness = np.mean(roi_v) / 255.0 if roi_v.size > 0 else 0
            avg_saturation = 1.0 - (np.mean(roi_s) / 255.0) if roi_s.size > 0 else 0
            confidence = (avg_brightness * 0.6 + avg_saturation * 0.4)

            detections.append({
                "x": center_x,
                "y": center_y,
                "width": int(w),
                "height": int(h),
                "confidence": float(min(confidence, 1.0))
            })

        # Sort detections by confidence (highest first)
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        # Save debug image if enabled
        if self.config.save_debug_image:
            self._save_debug(image, combined_mask, detections)

        print(f"Detection: found {len(detections)} pads")
        return detections

    def _save_debug(self, image: np.ndarray, mask: np.ndarray, detections: List[Dict]):
        """Save debug images: original with detections drawn + the binary mask."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Draw detections on original image
        vis = self.visualize_detections(image, detections)
        cv2.imwrite(f"{self.debug_dir}/detect_{ts}_result.jpg", vis)

        # Save the binary mask
        cv2.imwrite(f"{self.debug_dir}/detect_{ts}_mask.jpg", mask)

        # Save original
        cv2.imwrite(f"{self.debug_dir}/detect_{ts}_original.jpg", image)

        print(f"Debug images saved to {self.debug_dir}/detect_{ts}_*.jpg")

    def visualize_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection results on image for visualization."""
        vis_image = image.copy()

        for i, detection in enumerate(detections):
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

            # Draw label with index and confidence
            label = f"#{i+1} {confidence:.0%}"
            cv2.putText(vis_image, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        return vis_image
