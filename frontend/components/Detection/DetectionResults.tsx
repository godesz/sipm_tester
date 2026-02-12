"use client";

/**
 * DetectionResults - Displays detected SiPM pads in a table.
 */

import React from "react";
import { useHardware } from "@/contexts/HardwareContext";
import type { SiPMDetection } from "@/lib/types";

export default function DetectionResults() {
  const { camera, clearDetections } = useHardware();

  if (camera.detections.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-lg font-bold mb-4">Detection Results</h3>
        <div className="text-center py-8 text-gray-400">
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-sm">No detections yet</p>
          <p className="text-xs mt-1">Click "Detect SiPMs" to find pads</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">
          Detection Results ({camera.detections.length})
        </h3>
        <button
          onClick={() => clearDetections()}
          className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
        >
          Clear
        </button>
      </div>

      <div className="overflow-auto max-h-96">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              <th className="px-3 py-2 text-left">#</th>
              <th className="px-3 py-2 text-right">X (px)</th>
              <th className="px-3 py-2 text-right">Y (px)</th>
              <th className="px-3 py-2 text-right">Size</th>
              <th className="px-3 py-2 text-right">Conf.</th>
              <th className="px-3 py-2 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {camera.detections.map((detection, index) => (
              <DetectionRow
                key={index}
                detection={detection}
                index={index}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-600">Total Detections:</div>
          <div className="font-bold text-lg">{camera.detections.length}</div>
        </div>
        <div>
          <div className="text-gray-600">Avg Confidence:</div>
          <div className="font-bold text-lg">
            {(
              camera.detections.reduce((sum, d) => sum + d.confidence, 0) /
              camera.detections.length *
              100
            ).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Single detection row component
 */
function DetectionRow({
  detection,
  index,
}: {
  detection: SiPMDetection;
  index: number;
}) {
  const { move } = useHardware();

  const handleMoveTo = async () => {
    // This is a placeholder - actual coordinate conversion needed
    // In a real implementation, you'd convert pixel coordinates to machine coordinates
    // using camera calibration and reference points
    alert(
      `Moving to detection #${index + 1}\n` +
      `Pixel: (${detection.x}, ${detection.y})\n\n` +
      `Note: Coordinate conversion from pixels to mm will be implemented with calibration data.`
    );
  };

  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="px-3 py-2 font-medium">#{index + 1}</td>
      <td className="px-3 py-2 text-right font-mono">{detection.x}</td>
      <td className="px-3 py-2 text-right font-mono">{detection.y}</td>
      <td className="px-3 py-2 text-right font-mono text-xs">
        {detection.width}×{detection.height}
      </td>
      <td className="px-3 py-2 text-right">
        <span
          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            detection.confidence > 0.7
              ? "bg-green-100 text-green-700"
              : detection.confidence > 0.4
              ? "bg-yellow-100 text-yellow-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {(detection.confidence * 100).toFixed(0)}%
        </span>
      </td>
      <td className="px-3 py-2 text-center">
        <button
          onClick={handleMoveTo}
          className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs"
          title="Move to this detection"
        >
          Go
        </button>
      </td>
    </tr>
  );
}
