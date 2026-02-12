"use client";

/**
 * CalibrationPanel - Manages calibration settings.
 * Set reference point and camera-to-POGO offset.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { useConfig } from "@/contexts/ConfigContext";

export default function CalibrationPanel() {
  const { marlin } = useHardware();
  const { config, setReferencePoint, setCameraOffset, getReferencePoint, getCameraOffset } = useConfig();
  const [saving, setSaving] = useState(false);

  const refPoint = getReferencePoint();
  const camOffset = getCameraOffset();

  const handleSetReferencePoint = async () => {
    if (!marlin.connected) {
      alert("Marlin not connected!");
      return;
    }

    if (!confirm(
      `Set current position as reference point?\n\n` +
      `Current Position:\n` +
      `X: ${marlin.position.X.toFixed(2)} mm\n` +
      `Y: ${marlin.position.Y.toFixed(2)} mm\n` +
      `Z: ${marlin.position.Z.toFixed(2)} mm`
    )) {
      return;
    }

    setSaving(true);
    try {
      await setReferencePoint(
        marlin.position.X,
        marlin.position.Y,
        marlin.position.Z
      );
      alert("Reference point saved!");
    } catch (error) {
      alert(`Failed to set reference point: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSetCameraOffset = async () => {
    // Show input dialog for offset
    const offsetX = prompt("Enter X offset (mm):", camOffset?.x.toString() || "0");
    const offsetY = prompt("Enter Y offset (mm):", camOffset?.y.toString() || "0");

    if (offsetX === null || offsetY === null) {
      return; // User cancelled
    }

    const x = parseFloat(offsetX);
    const y = parseFloat(offsetY);

    if (isNaN(x) || isNaN(y)) {
      alert("Invalid offset values!");
      return;
    }

    setSaving(true);
    try {
      await setCameraOffset(x, y);
      alert("Camera offset saved!");
    } catch (error) {
      alert(`Failed to set camera offset: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Calibration</h3>

      {/* Reference Point Section */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-sm">Reference Point</h4>
          <button
            onClick={handleSetReferencePoint}
            disabled={!marlin.connected || saving}
            className={`px-3 py-1 rounded text-sm font-medium ${
              marlin.connected && !saving
                ? "bg-blue-500 text-white hover:bg-blue-600"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            {saving ? "Saving..." : "Set Current"}
          </button>
        </div>

        {refPoint ? (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="bg-gray-100 rounded p-2">
              <div className="text-xs text-gray-600">X</div>
              <div className="font-mono font-bold">{refPoint.x.toFixed(2)}</div>
            </div>
            <div className="bg-gray-100 rounded p-2">
              <div className="text-xs text-gray-600">Y</div>
              <div className="font-mono font-bold">{refPoint.y.toFixed(2)}</div>
            </div>
            <div className="bg-gray-100 rounded p-2">
              <div className="text-xs text-gray-600">Z</div>
              <div className="font-mono font-bold">{refPoint.z.toFixed(2)}</div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">
            Not set - move to tray corner and click "Set Current"
          </div>
        )}
      </div>

      {/* Camera Offset Section */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-sm">Camera-to-POGO Offset</h4>
          <button
            onClick={handleSetCameraOffset}
            disabled={saving}
            className={`px-3 py-1 rounded text-sm font-medium ${
              !saving
                ? "bg-green-500 text-white hover:bg-green-600"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            {saving ? "Saving..." : "Set Offset"}
          </button>
        </div>

        {camOffset ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="bg-gray-100 rounded p-2">
              <div className="text-xs text-gray-600">ΔX</div>
              <div className="font-mono font-bold">{camOffset.x.toFixed(2)} mm</div>
            </div>
            <div className="bg-gray-100 rounded p-2">
              <div className="text-xs text-gray-600">ΔY</div>
              <div className="font-mono font-bold">{camOffset.y.toFixed(2)} mm</div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500 italic">
            Not set - measure offset between camera center and POGO pins
          </div>
        )}

        <div className="mt-2 text-xs text-gray-600">
          💡 Tip: Use visual observation to determine the offset between camera crosshair and POGO pins
        </div>
      </div>

      {/* Current Machine Position */}
      <div>
        <h4 className="font-semibold text-sm mb-2">Current Position</h4>
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="bg-blue-50 rounded p-2">
            <div className="text-xs text-blue-600">X</div>
            <div className="font-mono font-bold text-blue-900">
              {marlin.position.X.toFixed(2)}
            </div>
          </div>
          <div className="bg-blue-50 rounded p-2">
            <div className="text-xs text-blue-600">Y</div>
            <div className="font-mono font-bold text-blue-900">
              {marlin.position.Y.toFixed(2)}
            </div>
          </div>
          <div className="bg-blue-50 rounded p-2">
            <div className="text-xs text-blue-600">Z</div>
            <div className="font-mono font-bold text-blue-900">
              {marlin.position.Z.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 p-3 bg-blue-50 rounded text-sm">
        <div className="font-semibold text-blue-900 mb-1">📋 Calibration Steps:</div>
        <ol className="text-blue-800 text-xs space-y-1 list-decimal list-inside">
          <li>Move machine to tray corner (reference point)</li>
          <li>Click "Set Current" to save reference point</li>
          <li>Observe camera crosshair vs POGO pins position</li>
          <li>Measure offset and click "Set Offset"</li>
        </ol>
      </div>
    </div>
  );
}
