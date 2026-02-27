"use client";

/**
 * MotionControl - XYZ movement control panel.
 * Provides buttons for moving axes and homing.
 */

import { useState, useEffect } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { MOVEMENT_STEPS } from "@/lib/constants";
import { motionAPI, configAPI } from "@/lib/api";

export default function MotionControl() {
  const { marlin, move, home } = useHardware();
  const [step, setStep] = useState<number>(MOVEMENT_STEPS.MEDIUM);
  const [moving, setMoving] = useState(false);
  const [refPoint, setRefPoint] = useState<{ x: number; y: number; z: number } | null>(null);
  const [sipmCol, setSipmCol] = useState(0);
  const [sipmRow, setSipmRow] = useState(0);

  // Load saved reference point from config on mount
  useEffect(() => {
    configAPI.getConfig().then((cfg) => {
      const ref = cfg.calibration.reference_point;
      if (ref.x !== 0 || ref.y !== 0) {
        setRefPoint({ x: ref.x, y: ref.y, z: ref.z ?? 0 });
      }
    }).catch(() => {});
  }, []);

  const handleReloadConfig = async () => {
    try {
      await configAPI.reload();
    } catch (error) {
      alert(`Failed to reload config: ${error instanceof Error ? error.message : error}`);
    }
  };

  const handleMove = async (axis: string, distance: number) => {
    if (marlin.emergencyStop) {
      alert("Emergency stop is active! Clear it first.");
      return;
    }

    setMoving(true);
    try {
      await move(axis, distance);
    } catch (error) {
      console.error("Move failed:", error);
    } finally {
      setMoving(false);
    }
  };

  const handleGoSipm = async () => {
    if (marlin.emergencyStop) {
      alert("Emergency stop is active! Clear it first.");
      return;
    }
    setMoving(true);
    try {
      await fetch(`http://localhost:8000/api/motion/go_sipm_rc?col=${sipmCol}&row=${sipmRow}`, { method: "POST" })
        .then(async (r) => {
          if (!r.ok) {
            const err = await r.json().catch(() => ({ detail: r.statusText }));
            throw new Error(err.detail || `HTTP ${r.status}`);
          }
        });
    } catch (error) {
      alert(`Failed to go to SiPM (${sipmCol}, ${sipmRow}): ${error instanceof Error ? error.message : error}`);
    } finally {
      setMoving(false);
    }
  };

  const handleSetReference = async () => {
    try {
      const result = await motionAPI.setReference();
      setRefPoint(result.reference_point);
      alert(`Reference point saved: X=${result.reference_point.x.toFixed(2)}, Y=${result.reference_point.y.toFixed(2)}`);
    } catch (error) {
      console.error("Set reference failed:", error);
      alert("Failed to set reference point");
    }
  };

  const handleGoReference = async () => {
    if (!refPoint) {
      alert("No reference point set yet. Use SET REF first.");
      return;
    }
    if (marlin.emergencyStop) {
      alert("Emergency stop is active! Clear it first.");
      return;
    }
    setMoving(true);
    try {
      await motionAPI.goReference();
    } catch (error) {
      console.error("Go reference failed:", error);
      alert(`Failed to go to reference: ${error instanceof Error ? error.message : error}`);
    } finally {
      setMoving(false);
    }
  };

  const handleHome = async () => {
    if (marlin.emergencyStop) {
      alert("Emergency stop is active! Clear it first.");
      return;
    }

    if (!confirm("Home all axes? This will move to the endstops.")) {
      return;
    }

    setMoving(true);
    try {
      await home();
    } catch (error) {
      console.error("Home failed:", error);
    } finally {
      setMoving(false);
    }
  };

  const buttonClass = (disabled: boolean) =>
    `px-4 py-2 rounded font-semibold transition-colors ${
      disabled
        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
        : "bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700"
    }`;

  const disabled = !marlin.connected || moving || marlin.emergencyStop;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">Motion Control</h3>
        <button
          onClick={handleReloadConfig}
          title="Reload config from JSON file"
          className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600 hover:bg-gray-200 active:bg-gray-300 transition-colors"
        >
          ↺ Reload Config
        </button>
      </div>

      {/* Step Size Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Step Size
        </label>
        <div className="flex gap-2">
          {[
            { value: MOVEMENT_STEPS.SMALL, label: "0.1mm" },
            { value: MOVEMENT_STEPS.MEDIUM, label: "1mm" },
            { value: MOVEMENT_STEPS.LARGE, label: "10mm" },
          ].map((s) => (
            <button
              key={s.value}
              onClick={() => setStep(s.value)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                step === s.value
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* XY Control */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          XY Control
        </label>
        <div className="grid grid-cols-3 gap-2 max-w-[200px]">
          {/* Top row */}
          <div />
          <button
            onClick={() => handleMove("Y", step)}
            disabled={disabled}
            className={buttonClass(disabled)}
            title="Move Y+"
          >
            ↑
          </button>
          <div />

          {/* Middle row */}
          <button
            onClick={() => handleMove("X", -step)}
            disabled={disabled}
            className={buttonClass(disabled)}
            title="Move X-"
          >
            ←
          </button>
          <div className="flex items-center justify-center text-gray-400 text-sm">
            XY
          </div>
          <button
            onClick={() => handleMove("X", step)}
            disabled={disabled}
            className={buttonClass(disabled)}
            title="Move X+"
          >
            →
          </button>

          {/* Bottom row */}
          <div />
          <button
            onClick={() => handleMove("Y", -step)}
            disabled={disabled}
            className={buttonClass(disabled)}
            title="Move Y-"
          >
            ↓
          </button>
          <div />
        </div>
      </div>

      {/* Z Control */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Z Control
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => handleMove("Z", step)}
            disabled={disabled}
            className={`${buttonClass(disabled)} flex-1`}
            title="Move Z Up"
          >
            Z ↑
          </button>
          <button
            onClick={() => handleMove("Z", -step)}
            disabled={disabled}
            className={`${buttonClass(disabled)} flex-1`}
            title="Move Z Down"
          >
            Z ↓
          </button>
        </div>
      </div>

      {/* Home Button */}
      <button
        onClick={handleHome}
        disabled={disabled}
        className={`w-full ${buttonClass(disabled)} bg-purple-500 hover:bg-purple-600 active:bg-purple-700`}
      >
        🏠 Home All Axes
      </button>

      {/* Reference Point Buttons */}
      <div className="mt-3 flex gap-2">
        <button
          onClick={handleSetReference}
          disabled={disabled}
          className={`flex-1 px-4 py-2 rounded font-semibold transition-colors ${
            disabled
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-green-500 text-white hover:bg-green-600 active:bg-green-700"
          }`}
          title="Save current position as tray reference"
        >
          📍 SET REF
        </button>
        <button
          onClick={handleGoReference}
          disabled={disabled || !refPoint}
          className={`flex-1 px-4 py-2 rounded font-semibold transition-colors ${
            disabled || !refPoint
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-orange-500 text-white hover:bg-orange-600 active:bg-orange-700"
          }`}
          title={refPoint ? `Go to reference: X=${refPoint.x.toFixed(1)}, Y=${refPoint.y.toFixed(1)}` : "No reference set"}
        >
          ➡ GO REF
        </button>
      </div>

      {/* Reference Point Display */}
      {refPoint && (
        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
          Reference: X={refPoint.x.toFixed(2)}  Y={refPoint.y.toFixed(2)}  Z={refPoint.z.toFixed(2)}
        </div>
      )}

      {/* SiPM Navigation */}
      <div className="mt-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">Go to SiPM (col, row)</label>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            min={0}
            value={sipmCol}
            onChange={(e) => setSipmCol(Number(e.target.value))}
            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
            placeholder="col"
          />
          <span className="text-gray-400 text-sm">,</span>
          <input
            type="number"
            min={0}
            value={sipmRow}
            onChange={(e) => setSipmRow(Number(e.target.value))}
            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
            placeholder="row"
          />
          <button
            onClick={handleGoSipm}
            disabled={disabled}
            className={`flex-1 px-3 py-1 rounded font-semibold text-sm transition-colors ${
              disabled
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700"
            }`}
          >
            Go
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {marlin.emergencyStop && (
        <div className="mt-3 p-2 bg-red-100 text-red-700 text-sm rounded">
          ⚠️ Emergency stop active!
        </div>
      )}
      {!marlin.connected && (
        <div className="mt-3 p-2 bg-yellow-100 text-yellow-700 text-sm rounded">
          ℹ️ Connect Marlin first
        </div>
      )}
      {moving && (
        <div className="mt-3 p-2 bg-blue-100 text-blue-700 text-sm rounded">
          ⏳ Moving...
        </div>
      )}
    </div>
  );
}
