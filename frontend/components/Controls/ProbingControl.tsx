"use client";

/**
 * ProbingControl - Z-axis probing controls with progress display.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { useConfig } from "@/contexts/ConfigContext";

export default function ProbingControl() {
  const { marlin, measurement, probeZ, testDiode } = useHardware();
  const { config } = useConfig();
  const [probing, setProbing] = useState(false);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const probingConfig = config?.probing;

  const handleProbeZ = async () => {
    if (!marlin.connected) {
      alert("Marlin not connected!");
      return;
    }

    if (!measurement.connected) {
      alert("Measurement device not connected!");
      return;
    }

    if (marlin.emergencyStop) {
      alert("Emergency stop is active!");
      return;
    }

    if (!confirm(
      `Start Z-axis probing?\n\n` +
      `Current Z: ${marlin.position.Z.toFixed(2)} mm\n` +
      `Rough step: ${probingConfig?.rough_step || 1.0} mm\n` +
      `Fine step: ${probingConfig?.fine_step || 0.1} mm\n` +
      `Safe minimum: ${probingConfig?.safe_z_min || 40.0} mm\n\n` +
      `The head will move down until contact is detected.`
    )) {
      return;
    }

    setProbing(true);
    setResult(null);

    try {
      await probeZ(marlin.position.Z);
      setResult("✅ Contact detected successfully!");
    } catch (error) {
      setResult(`❌ Probing failed: ${error}`);
    } finally {
      setProbing(false);
    }
  };

  const handleTestDiode = async () => {
    if (!measurement.connected) {
      alert("Measurement device not connected!");
      return;
    }

    setTesting(true);
    setResult(null);

    try {
      await testDiode();
      setResult("✅ Diode test complete - check status panel");
    } catch (error) {
      setResult(`❌ Test failed: ${error}`);
    } finally {
      setTesting(false);
    }
  };

  const canProbe = marlin.connected && measurement.connected && !marlin.emergencyStop;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Testing & Probing</h3>

      {/* Test Diode Button */}
      <div className="mb-4">
        <button
          onClick={handleTestDiode}
          disabled={!measurement.connected || testing}
          className={`w-full px-4 py-3 rounded font-medium transition-colors ${
            measurement.connected && !testing
              ? "bg-purple-500 text-white hover:bg-purple-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {testing ? (
            <>
              <svg
                className="inline-block animate-spin h-4 w-4 mr-2"
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
              Testing...
            </>
          ) : (
            "🔌 Test Diode Connection"
          )}
        </button>
        <p className="text-xs text-gray-600 mt-1">
          Quick test of current POGO pin connection
        </p>
      </div>

      {/* Probe Z Button */}
      <div className="mb-4">
        <button
          onClick={handleProbeZ}
          disabled={!canProbe || probing}
          className={`w-full px-4 py-3 rounded font-bold text-lg transition-colors ${
            canProbe && !probing
              ? "bg-blue-500 text-white hover:bg-blue-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {probing ? (
            <>
              <svg
                className="inline-block animate-spin h-5 w-5 mr-2"
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
              Probing Z-Axis...
            </>
          ) : (
            "⬇️ Start Z-Axis Probing"
          )}
        </button>
        <p className="text-xs text-gray-600 mt-1">
          Automatic probing until contact detected
        </p>
      </div>

      {/* Result Display */}
      {result && (
        <div
          className={`p-3 rounded mb-4 ${
            result.startsWith("✅")
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          <div className="text-sm font-medium">{result}</div>
        </div>
      )}

      {/* Probing Parameters */}
      {probingConfig && (
        <div className="p-3 bg-gray-50 rounded text-xs">
          <div className="font-semibold text-gray-700 mb-2">
            Probing Parameters:
          </div>
          <div className="grid grid-cols-2 gap-2 text-gray-600">
            <div>
              <span className="font-medium">Rough step:</span> {probingConfig.rough_step} mm
            </div>
            <div>
              <span className="font-medium">Fine step:</span> {probingConfig.fine_step} mm
            </div>
            <div className="col-span-2">
              <span className="font-medium">Safe Z min:</span> {probingConfig.safe_z_min} mm
            </div>
          </div>
        </div>
      )}

      {/* Status Messages */}
      {!marlin.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect Marlin first
        </div>
      )}
      {!measurement.connected && marlin.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect measurement device first
        </div>
      )}
      {marlin.emergencyStop && (
        <div className="mt-3 p-2 bg-red-100 text-red-700 text-sm rounded">
          ⚠️ Emergency stop active!
        </div>
      )}
    </div>
  );
}
