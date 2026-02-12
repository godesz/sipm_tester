"use client";

/**
 * CameraView - Displays MJPEG video stream from backend with overlay.
 */

import React, { useRef, useEffect, useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { useConfig } from "@/contexts/ConfigContext";
import { api } from "@/lib/api";
import { CAMERA_STREAM_SIZE } from "@/lib/constants";
import CameraOverlay from "./CameraOverlay";

interface CameraViewProps {
  showOverlay?: boolean;
  className?: string;
}

export default function CameraView({ showOverlay = true, className = "" }: CameraViewProps) {
  const { camera, marlin } = useHardware();
  const { config } = useConfig();
  const [imageError, setImageError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  const streamUrl = api.camera.getStreamURL(camera.currentCamera);

  // Reset error state when camera changes
  useEffect(() => {
    setImageError(false);
  }, [camera.currentCamera]);

  return (
    <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      {/* Video Stream */}
      <div
        className="relative"
        style={{
          width: CAMERA_STREAM_SIZE.WIDTH,
          height: CAMERA_STREAM_SIZE.HEIGHT,
        }}
      >
        {!imageError ? (
          <>
            <img
              ref={imgRef}
              src={streamUrl}
              alt="Camera stream"
              className="w-full h-full object-contain"
              onError={() => setImageError(true)}
            />

            {/* Overlay */}
            {showOverlay && (
              <CameraOverlay
                width={CAMERA_STREAM_SIZE.WIDTH}
                height={CAMERA_STREAM_SIZE.HEIGHT}
                position={marlin.position}
                detections={camera.detections}
                cameraOffset={config?.calibration.camera_to_pogo_offset}
              />
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <svg
                className="w-16 h-16 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <p className="text-sm">Camera stream unavailable</p>
              <p className="text-xs mt-2">Check backend connection</p>
            </div>
          </div>
        )}
      </div>

      {/* Camera Info Badge */}
      <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
        Camera {camera.currentCamera}
      </div>

      {/* Detection Count Badge */}
      {camera.detections.length > 0 && (
        <div className="absolute top-2 right-2 bg-green-500/80 text-white text-xs px-2 py-1 rounded">
          {camera.detections.length} detection{camera.detections.length !== 1 ? "s" : ""}
        </div>
      )}

      {/* Detecting Indicator */}
      {camera.detecting && (
        <div className="absolute bottom-2 left-2 bg-blue-500/80 text-white text-xs px-2 py-1 rounded flex items-center">
          <svg
            className="animate-spin h-3 w-3 mr-1"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Detecting...
        </div>
      )}
    </div>
  );
}
