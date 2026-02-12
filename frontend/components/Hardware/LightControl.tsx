"use client";

/**
 * LightControl - Controls Hardware 3 RGB LED lights.
 * Provides mode selector (left/right/all) and RGB sliders.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { LIGHT_MODES, LIGHT_MODE_NAMES } from "@/lib/constants";

export default function LightControl() {
  const { measurement, setLight, turnOffLEDs } = useHardware();

  const [mode, setMode] = useState<1 | 2 | 3>(LIGHT_MODES.ALL);
  const [r, setR] = useState(255);
  const [g, setG] = useState(255);
  const [b, setB] = useState(255);
  const [applying, setApplying] = useState(false);

  const handleApply = async () => {
    if (!measurement.connected) {
      alert("Measurement device not connected!");
      return;
    }

    setApplying(true);
    try {
      await setLight(mode, r, g, b);
    } catch (error) {
      console.error("Set light failed:", error);
    } finally {
      setApplying(false);
    }
  };

  const handleTurnOff = async () => {
    if (!measurement.connected) {
      alert("Measurement device not connected!");
      return;
    }

    setApplying(true);
    try {
      await turnOffLEDs();
    } catch (error) {
      console.error("Turn off LEDs failed:", error);
    } finally {
      setApplying(false);
    }
  };

  // Color preview
  const previewColor = `rgb(${r}, ${g}, ${b})`;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Light Control</h3>

      {/* Mode Selector */}
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
        <ColorSlider
          label="Red"
          value={r}
          onChange={setR}
          color="red"
        />
        <ColorSlider
          label="Green"
          value={g}
          onChange={setG}
          color="green"
        />
        <ColorSlider
          label="Blue"
          value={b}
          onChange={setB}
          color="blue"
        />
      </div>

      {/* Color Preview */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Preview
        </label>
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
          disabled={!measurement.connected || applying}
          className={`w-full px-4 py-2 rounded font-medium transition-colors ${
            measurement.connected && !applying
              ? "bg-green-500 text-white hover:bg-green-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {applying ? "Applying..." : "💡 Apply Light"}
        </button>

        <button
          onClick={handleTurnOff}
          disabled={!measurement.connected || applying}
          className={`w-full px-4 py-2 rounded font-medium transition-colors ${
            measurement.connected && !applying
              ? "bg-red-500 text-white hover:bg-red-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          Turn Off LEDs
        </button>
      </div>

      {/* Status Message */}
      {!measurement.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect measurement device first
        </div>
      )}

      {/* Preset Buttons */}
      <div className="mt-4 pt-4 border-t">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Quick Presets
        </label>
        <div className="grid grid-cols-3 gap-2">
          <PresetButton
            label="White"
            onClick={() => { setR(255); setG(255); setB(255); }}
          />
          <PresetButton
            label="Red"
            onClick={() => { setR(255); setG(0); setB(0); }}
          />
          <PresetButton
            label="Green"
            onClick={() => { setR(0); setG(255); setB(0); }}
          />
          <PresetButton
            label="Blue"
            onClick={() => { setR(0); setG(0); setB(255); }}
          />
          <PresetButton
            label="Yellow"
            onClick={() => { setR(255); setG(255); setB(0); }}
          />
          <PresetButton
            label="Off"
            onClick={() => { setR(0); setG(0); setB(0); }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Color slider component
 */
function ColorSlider({
  label,
  value,
  onChange,
  color,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  color: "red" | "green" | "blue";
}) {
  const colorClass = {
    red: "accent-red-500",
    green: "accent-green-500",
    blue: "accent-blue-500",
  }[color];

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm text-gray-600 font-mono">{value}</span>
      </div>
      <input
        type="range"
        min="0"
        max="255"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${colorClass}`}
      />
    </div>
  );
}

/**
 * Preset button component
 */
function PresetButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-xs font-medium text-gray-700 transition-colors"
    >
      {label}
    </button>
  );
}
