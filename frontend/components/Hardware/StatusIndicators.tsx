"use client";

/**
 * StatusIndicators - Displays live position and hardware status.
 */

import React from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { CONNECTION_STATE_NAMES, CONNECTION_STATE_COLORS } from "@/lib/constants";

export default function StatusIndicators() {
  const { marlin, camera, measurement } = useHardware();

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Status</h3>

      {/* Current Position */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-gray-700 mb-2">Position</h4>
        <div className="grid grid-cols-3 gap-2">
          <PositionDisplay axis="X" value={marlin.position.X} />
          <PositionDisplay axis="Y" value={marlin.position.Y} />
          <PositionDisplay axis="Z" value={marlin.position.Z} />
        </div>
      </div>

      {/* Hardware Status */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-gray-700 mb-2">Hardware</h4>
        <div className="space-y-2">
          <HardwareStatus
            name="Marlin"
            connected={marlin.connected}
            details={marlin.emergencyStop ? "⚠️ E-STOP" : undefined}
          />
          <HardwareStatus
            name="Camera"
            connected={camera.connected}
            details={`${camera.detections.length} detections`}
          />
          <HardwareStatus
            name="Measurement"
            connected={measurement.connected}
            details={
              measurement.lastConnectionState !== null
                ? CONNECTION_STATE_NAMES[measurement.lastConnectionState as keyof typeof CONNECTION_STATE_NAMES] || "Unknown"
                : undefined
            }
          />
        </div>
      </div>

      {/* Emergency Stop Indicator */}
      {marlin.emergencyStop && (
        <div className="p-3 bg-red-100 border-2 border-red-500 rounded text-red-700 font-bold text-center animate-pulse">
          🚨 EMERGENCY STOP ACTIVE 🚨
        </div>
      )}

      {/* Connection Test Result */}
      {measurement.connected && measurement.lastConnectionState !== null && (
        <div className="mt-4 p-2 bg-gray-50 rounded">
          <div className="text-sm font-semibold text-gray-700 mb-1">
            Last Test:
          </div>
          <div
            className={`text-sm font-medium ${
              CONNECTION_STATE_COLORS[measurement.lastConnectionState as keyof typeof CONNECTION_STATE_COLORS] ||
              "text-gray-600"
            }`}
          >
            {CONNECTION_STATE_NAMES[measurement.lastConnectionState as keyof typeof CONNECTION_STATE_NAMES] ||
              `State ${measurement.lastConnectionState}`}
            {measurement.isContactDetected && " ✓"}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Position display for a single axis.
 */
function PositionDisplay({ axis, value }: { axis: string; value: number }) {
  return (
    <div className="bg-gray-100 rounded p-2 text-center">
      <div className="text-xs text-gray-600 font-medium">{axis}</div>
      <div className="text-lg font-bold text-gray-900">
        {value.toFixed(2)}
      </div>
      <div className="text-xs text-gray-500">mm</div>
    </div>
  );
}

/**
 * Hardware status indicator.
 */
function HardwareStatus({
  name,
  connected,
  details,
}: {
  name: string;
  connected: boolean;
  details?: string;
}) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            connected ? "bg-green-500" : "bg-red-500"
          }`}
        />
        <span className="text-sm font-medium">{name}</span>
      </div>
      {details && (
        <span className="text-xs text-gray-600">{details}</span>
      )}
    </div>
  );
}
