"use client";

/**
 * ProbingControl - Z-axis probing and contact detection.
 * Supports both direct COM (measurement device) and external API service.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { useConfig } from "@/contexts/ConfigContext";
import { extMeasurementAPI } from "@/lib/api";
import type { ContactStatusResult, ContactStatus } from "@/lib/types";

// Contact status → display helpers
const CONTACT_COLOR: Record<ContactStatus, string> = {
  Contact:      "bg-green-100 text-green-800 border-green-300",
  OpenCircuit:  "bg-orange-100 text-orange-800 border-orange-300",
  ShortCircuit: "bg-red-100 text-red-800 border-red-300",
  IicBusError:  "bg-red-100 text-red-800 border-red-300",
  Unknown:      "bg-gray-100 text-gray-700 border-gray-300",
};

export default function ProbingControl() {
  const { marlin, measurement, measurementMode, probeZ, testDiode } = useHardware();
  const { config } = useConfig();

  const [probing, setProbing] = useState(false);
  const [testing, setTesting] = useState(false);
  const [autoRunning, setAutoRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [extContactResult, setExtContactResult] = useState<ContactStatusResult | null>(null);

  const probingConfig = config?.probing;
  const isApi = measurementMode === "api";

  // ── Test diode / contact status ────────────────────────────────────────────

  const handleTestDiode = async () => {
    if (!isApi && !measurement.connected) {
      alert("Measurement device not connected!");
      return;
    }
    setTesting(true);
    setResult(null);
    setExtContactResult(null);
    try {
      if (isApi) {
        const res = await extMeasurementAPI.getContactStatus();
        setExtContactResult(res);
        setResult(res.status === "Contact" ? "✅ Contact!" : `⚪ ${res.statusLabel}`);
      } else {
        await testDiode();
        setResult("✅ Diode test complete — check status panel");
      }
    } catch (error) {
      setResult(`❌ Test failed: ${error instanceof Error ? error.message : error}`);
    } finally {
      setTesting(false);
    }
  };

  // ── Auto contact start/stop (API mode only) ────────────────────────────────

  const handleStartAuto = async () => {
    try {
      setAutoRunning(true);
      await extMeasurementAPI.startContactAuto();
    } catch (error) {
      setResult(`❌ Start auto failed: ${error instanceof Error ? error.message : error}`);
      setAutoRunning(false);
    }
  };

  const handleStopAuto = async () => {
    try {
      await extMeasurementAPI.stopContactAuto();
    } catch (error) {
      setResult(`❌ Stop auto failed: ${error instanceof Error ? error.message : error}`);
    } finally {
      setAutoRunning(false);
    }
  };

  // ── Z probing (direct only) ────────────────────────────────────────────────

  const handleProbeZ = async () => {
    if (!marlin.connected) { alert("Marlin not connected!"); return; }
    if (!measurement.connected) { alert("Measurement device not connected!"); return; }
    if (marlin.emergencyStop) { alert("Emergency stop is active!"); return; }

    if (!confirm(
      `Start Z-axis probing?\n\n` +
      `Current Z: ${marlin.position.Z.toFixed(2)} mm\n` +
      `Rough step: ${probingConfig?.rough_step || 1.0} mm\n` +
      `Fine step: ${probingConfig?.fine_step || 0.1} mm\n` +
      `Safe minimum: ${probingConfig?.safe_z_min || 40.0} mm\n\n` +
      `The head will move down until contact is detected.`
    )) return;

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

  const canProbe = marlin.connected && measurement.connected && !marlin.emergencyStop;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Testing & Probing</h3>

      {/* Test / Contact Status Button */}
      <div className="mb-4">
        <button
          onClick={handleTestDiode}
          disabled={(!isApi && !measurement.connected) || testing}
          className={`w-full px-4 py-3 rounded font-medium transition-colors ${
            (isApi || measurement.connected) && !testing
              ? "bg-purple-500 text-white hover:bg-purple-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {testing ? <Spinner /> : (isApi ? "📡 Get Contact Status" : "🔌 Test Diode Connection")}
        </button>
        <p className="text-xs text-gray-600 mt-1">
          {isApi ? "Query contact status from external service" : "Quick test of current POGO pin connection"}
        </p>
      </div>

      {/* API mode: ext contact result card */}
      {isApi && extContactResult && (
        <div className={`mb-4 p-3 rounded border text-sm ${CONTACT_COLOR[extContactResult.status]}`}>
          <div className="font-semibold">{extContactResult.statusLabel}</div>
          <div className="text-xs mt-1 opacity-75">{extContactResult.timestamp}</div>
        </div>
      )}

      {/* API mode: Auto start/stop */}
      {isApi && (
        <div className="mb-4 flex gap-2">
          <button
            onClick={handleStartAuto}
            disabled={autoRunning}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
              !autoRunning
                ? "bg-green-500 text-white hover:bg-green-600"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            ▶ Start Auto
          </button>
          <button
            onClick={handleStopAuto}
            disabled={!autoRunning}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
              autoRunning
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            ■ Stop Auto
          </button>
        </div>
      )}

      {/* Z Probe Button (direct only — requires Marlin + measurement COM) */}
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
          {probing ? <Spinner size="lg" /> : "⬇️ Start Z-Axis Probing"}
        </button>
        <p className="text-xs text-gray-600 mt-1">
          Automatic probing until contact detected (direct mode only)
        </p>
      </div>

      {/* Result */}
      {result && (
        <div className={`p-3 rounded mb-4 ${
          result.startsWith("✅") ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
        }`}>
          <div className="text-sm font-medium">{result}</div>
        </div>
      )}

      {/* Probing Parameters */}
      {probingConfig && (
        <div className="p-3 bg-gray-50 rounded text-xs">
          <div className="font-semibold text-gray-700 mb-2">Probing Parameters:</div>
          <div className="grid grid-cols-2 gap-2 text-gray-600">
            <div><span className="font-medium">Rough step:</span> {probingConfig.rough_step} mm</div>
            <div><span className="font-medium">Fine step:</span> {probingConfig.fine_step} mm</div>
            <div className="col-span-2"><span className="font-medium">Safe Z min:</span> {probingConfig.safe_z_min} mm</div>
          </div>
        </div>
      )}

      {/* Status Messages */}
      {!marlin.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect Marlin first
        </div>
      )}
      {!isApi && !measurement.connected && marlin.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect measurement device first (or switch to API mode)
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

function Spinner({ size = "sm" }: { size?: "sm" | "lg" }) {
  const cls = size === "lg" ? "inline-block animate-spin h-5 w-5 mr-2" : "inline-block animate-spin h-4 w-4 mr-2";
  return (
    <svg className={cls} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}
