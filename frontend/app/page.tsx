"use client";

/**
 * Main page - SiPM Tester Station Control Interface
 * Complete UI with all Phase 1-4 features
 */

import CameraView from "@/components/Camera/CameraView";
import MotionControl from "@/components/Controls/MotionControl";
import CalibrationPanel from "@/components/Controls/CalibrationPanel";
import EmergencyStop from "@/components/Controls/EmergencyStop";
import ProbingControl from "@/components/Controls/ProbingControl";
import ConnectionPanel from "@/components/Hardware/ConnectionPanel";
import StatusIndicators from "@/components/Hardware/StatusIndicators";
import LightControl from "@/components/Hardware/LightControl";
import DetectionResults from "@/components/Detection/DetectionResults";
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

      {/* Main Layout - 3 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Left Column - Camera & Detection (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
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

          {/* Detection Results */}
          <DetectionResults />
        </div>

        {/* Middle Column - Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Motion Control */}
          <MotionControl />

          {/* Calibration Panel */}
          <CalibrationPanel />

          {/* Testing & Probing */}
          <ProbingControl />
        </div>

        {/* Right Column - Status & Hardware (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Emergency Stop */}
          <EmergencyStop />

          {/* Connection Panel */}
          <ConnectionPanel />

          {/* Status Indicators */}
          <StatusIndicators />

          {/* Light Control */}
          <LightControl />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-6 text-center text-sm text-gray-500">
        SiPM Tester Station v1.0 | Phase 4 Complete ✨
      </footer>
    </div>
  );
}
