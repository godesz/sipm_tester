"use client";

/**
 * Main page - SiPM Tester Station Control Interface
 */

import CameraView from "@/components/Camera/CameraView";
import MotionControl from "@/components/Controls/MotionControl";
import ConnectionPanel from "@/components/Hardware/ConnectionPanel";
import StatusIndicators from "@/components/Hardware/StatusIndicators";
import { useHardware } from "@/contexts/HardwareContext";

export default function Home() {
  const { camera, captureImage, detectSiPMs, clearDetections } = useHardware();

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          SiPM Tester Station
        </h1>
        <p className="text-gray-600">
          LumenPnP Machine Control & Testing Interface
        </p>
      </header>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column - Camera & Camera Controls */}
        <div className="lg:col-span-2 space-y-4">
          {/* Camera View */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Camera View</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => captureImage()}
                  className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                >
                  📷 Capture
                </button>
                <button
                  onClick={() => detectSiPMs()}
                  disabled={camera.detecting}
                  className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400 text-sm"
                >
                  {camera.detecting ? "Detecting..." : "🔍 Detect SiPMs"}
                </button>
                {camera.detections.length > 0 && (
                  <button
                    onClick={() => clearDetections()}
                    className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
            <CameraView showOverlay={true} />
          </div>

          {/* Motion Control */}
          <MotionControl />
        </div>

        {/* Right Column - Status & Connection */}
        <div className="space-y-4">
          {/* Connection Panel */}
          <ConnectionPanel />

          {/* Status Indicators */}
          <StatusIndicators />

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-bold mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <QuickActionButton
                label="Test Diode Connection"
                onClick={() => {
                  // This will be implemented in Phase 4
                  alert("Test diode functionality coming in Phase 4!");
                }}
              />
              <QuickActionButton
                label="Set Reference Point"
                onClick={() => {
                  // This will be implemented in Phase 4
                  alert("Calibration features coming in Phase 4!");
                }}
              />
              <QuickActionButton
                label="Set Camera Offset"
                onClick={() => {
                  // This will be implemented in Phase 4
                  alert("Calibration features coming in Phase 4!");
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-6 text-center text-sm text-gray-500">
        SiPM Tester Station v1.0 | Phase 3 Complete
      </footer>
    </div>
  );
}

/**
 * Quick action button component
 */
function QuickActionButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium text-gray-700 transition-colors"
    >
      {label}
    </button>
  );
}
