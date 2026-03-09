"use client";

/**
 * LightControl - Controls RGB LED lights.
 * Supports both direct COM (measurement device) and external API service.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { LIGHT_MODES, LIGHT_MODE_NAMES } from "@/lib/constants";
import { extMeasurementAPI } from "@/lib/api";
import type { LedMode } from "@/lib/types";

/** Map our 1/2/3 mode to the external service's LedMode string. */
function toExtMode(mode: 1 | 2 | 3): LedMode {
  if (mode === 1) return "Left";
  if (mode === 2) return "Right";
  return "Both";
}

export default function LightControl() {
  const { measurement, measurementMode, setMeasurementMode, setLight, turnOffLEDs } = useHardware();

  const [mode, setMode] = useState<1 | 2 | 3>(LIGHT_MODES.ALL);
  const [r, setR] = useState(255);
  const [g, setG] = useState(255);
  const [b, setB] = useState(255);
  const [applying, setApplying] = useState(false);

  const isApi = measurementMode === "api";
  // In API mode the direct connection is not needed
  const canOperate = isApi || measurement.connected;

  const handleApply = async () => {
    if (!canOperate) {
      alert(isApi ? "External service not configured." : "Measurement device not connected!");
      return;
    }
    setApplying(true);
    try {
      if (isApi) {
        await extMeasurementAPI.setLed(toExtMode(mode), r, g, b);
      } else {
        await setLight(mode, r, g, b);
      }
    } catch (error) {
      console.error("Set light failed:", error);
      alert(`Set light failed: ${error instanceof Error ? error.message : error}`);
    } finally {
      setApplying(false);
    }
  };

  const handleTurnOff = async () => {
    if (!canOperate) {
      alert(isApi ? "External service not configured." : "Measurement device not connected!");
      return;
    }
    setApplying(true);
    try {
      if (isApi) {
        await extMeasurementAPI.ledOff();
      } else {
        await turnOffLEDs();
      }
    } catch (error) {
      console.error("Turn off LEDs failed:", error);
      alert(`Turn off failed: ${error instanceof Error ? error.message : error}`);
    } finally {
      setApplying(false);
    }
  };

  const previewColor = `rgb(${r}, ${g}, ${b})`;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold">Light Control</h3>
        {/* Mode Toggle */}
        <div className="flex items-center gap-1 bg-gray-100 rounded p-0.5">
          <button
            onClick={() => setMeasurementMode("direct")}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
              !isApi ? "bg-blue-500 text-white" : "text-gray-600 hover:bg-gray-200"
            }`}
          >
            Direct
          </button>
          <button
            onClick={() => setMeasurementMode("api")}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
              isApi ? "bg-purple-500 text-white" : "text-gray-600 hover:bg-gray-200"
            }`}
          >
            API
          </button>
        </div>
      </div>

      {/* Mode indicator */}
      {isApi && (
        <div className="mb-3 px-2 py-1 bg-purple-50 border border-purple-200 rounded text-xs text-purple-700">
          Using external service (localhost:8003)
        </div>
      )}

      {/* LED Mode Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          LED Mode
        </label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { value: LIGHT_MODES.LEFT, label: LIGHT_MODE_NAMES[LIGHT_MODES.LEFT] },
            { value: LIGHT_MODES.RIGHT, label: LIGHT_MODE_NAMES[LIGHT_MODES.RIGHT] },
            { value: LIGHT_MODES.ALL, label: LIGHT_MODE_NAMES[LIGHT_MODES.ALL] },
          ].map((m) => (
            <button
              key={m.value}
              onClick={() => setMode(m.value as 1 | 2 | 3)}
              className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                mode === m.value
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* RGB Sliders */}
      <div className="space-y-3 mb-4">
        <ColorSlider label="Red"   value={r} onChange={setR} color="red"   />
        <ColorSlider label="Green" value={g} onChange={setG} color="green" />
        <ColorSlider label="Blue"  value={b} onChange={setB} color="blue"  />
      </div>

      {/* Color Preview */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Preview</label>
        <div
          className="w-full h-12 rounded border-2 border-gray-300"
          style={{ backgroundColor: previewColor }}
        />
        <div className="text-xs text-center text-gray-600 mt-1">
          RGB({r}, {g}, {b})
        </div>
      </div>

      {/* Control Buttons */}
      <div className="space-y-2">
        <button
          onClick={handleApply}
          disabled={!canOperate || applying}
          className={`w-full px-4 py-2 rounded font-medium transition-colors ${
            canOperate && !applying
              ? "bg-green-500 text-white hover:bg-green-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {applying ? "Applying..." : "💡 Apply Light"}
        </button>

        <button
          onClick={handleTurnOff}
          disabled={!canOperate || applying}
          className={`w-full px-4 py-2 rounded font-medium transition-colors ${
            canOperate && !applying
              ? "bg-red-500 text-white hover:bg-red-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          Turn Off LEDs
        </button>
      </div>

      {/* Status Messages */}
      {!isApi && !measurement.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect measurement device first
        </div>
      )}

      {/* Quick Presets */}
      <div className="mt-4 pt-4 border-t">
        <label className="block text-sm font-medium text-gray-700 mb-2">Quick Presets</label>
        <div className="grid grid-cols-3 gap-2">
          <PresetButton label="White"  onClick={() => { setR(255); setG(255); setB(255); }} />
          <PresetButton label="Red"    onClick={() => { setR(255); setG(0);   setB(0);   }} />
          <PresetButton label="Green"  onClick={() => { setR(0);   setG(255); setB(0);   }} />
          <PresetButton label="Blue"   onClick={() => { setR(0);   setG(0);   setB(255); }} />
          <PresetButton label="Yellow" onClick={() => { setR(255); setG(255); setB(0);   }} />
          <PresetButton label="Off"    onClick={() => { setR(0);   setG(0);   setB(0);   }} />
        </div>
      </div>
    </div>
  );
}

function ColorSlider({ label, value, onChange, color }: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  color: "red" | "green" | "blue";
}) {
  const colorClass = { red: "accent-red-500", green: "accent-green-500", blue: "accent-blue-500" }[color];
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm text-gray-600 font-mono">{value}</span>
      </div>
      <input
        type="range" min="0" max="255" value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${colorClass}`}
      />
    </div>
  );
}

function PresetButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-xs font-medium text-gray-700 transition-colors"
    >
      {label}
    </button>
  );
}
