"use client";

/**
 * EmergencyStop - Emergency stop button with double-press safety.
 * Requires two presses within 2 seconds to activate.
 */

import React, { useState, useEffect, useRef } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { EMERGENCY_STOP_TIMEOUT } from "@/lib/constants";

export default function EmergencyStop() {
  const { marlin, activateEmergencyStop, clearEmergencyStop } = useHardware();
  const [pressCount, setPressCount] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clear timers on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // Reset press count after timeout
  useEffect(() => {
    if (pressCount === 1) {
      // Start countdown
      setTimeRemaining(EMERGENCY_STOP_TIMEOUT);

      // Update countdown every 100ms
      intervalRef.current = setInterval(() => {
        setTimeRemaining((prev) => Math.max(0, prev - 100));
      }, 100);

      // Reset after timeout
      timerRef.current = setTimeout(() => {
        setPressCount(0);
        setTimeRemaining(0);
        if (intervalRef.current) clearInterval(intervalRef.current);
      }, EMERGENCY_STOP_TIMEOUT);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [pressCount]);

  const handlePress = async () => {
    if (pressCount === 0) {
      // First press
      setPressCount(1);
    } else if (pressCount === 1) {
      // Second press - activate emergency stop
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
      setPressCount(0);
      setTimeRemaining(0);

      await activateEmergencyStop();
    }
  };

  const handleClear = async () => {
    if (confirm("Clear emergency stop? This will re-enable machine movement.")) {
      await clearEmergencyStop();
    }
  };

  if (marlin.emergencyStop) {
    // Emergency stop is active
    return (
      <div className="bg-white rounded-lg shadow-md p-4 border-4 border-red-500">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse">🚨</div>
          <h3 className="text-2xl font-bold text-red-600 mb-2">
            EMERGENCY STOP ACTIVE
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            All movement commands are blocked
          </p>
          <button
            onClick={handleClear}
            className="w-full px-6 py-3 bg-green-500 text-white rounded-lg font-bold text-lg hover:bg-green-600 transition-colors"
          >
            Clear Emergency Stop
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4 text-gray-900">Emergency Stop</h3>

      {/* Emergency Stop Button */}
      <button
        onClick={handlePress}
        className={`w-full px-6 py-8 rounded-lg font-bold text-xl transition-all transform active:scale-95 ${
          pressCount === 0
            ? "bg-red-500 hover:bg-red-600 text-white"
            : "bg-red-600 text-white animate-pulse shadow-lg shadow-red-500/50"
        }`}
      >
        {pressCount === 0 ? (
          <>
            🛑 EMERGENCY STOP
            <div className="text-sm font-normal mt-1">
              Press twice to activate
            </div>
          </>
        ) : (
          <>
            PRESS AGAIN TO CONFIRM
            <div className="text-sm font-normal mt-1">
              ({(timeRemaining / 1000).toFixed(1)}s remaining)
            </div>
          </>
        )}
      </button>

      {/* Progress Bar */}
      {pressCount === 1 && (
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-red-500 h-full transition-all duration-100"
            style={{
              width: `${(timeRemaining / EMERGENCY_STOP_TIMEOUT) * 100}%`,
            }}
          />
        </div>
      )}

      {/* Instructions */}
      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs">
        <div className="font-semibold text-yellow-900 mb-1">
          ⚠️ Double-Press Safety
        </div>
        <p className="text-yellow-800">
          This button requires two presses within {EMERGENCY_STOP_TIMEOUT / 1000} seconds to prevent
          accidental activation. When activated, all machine movements will be blocked until cleared.
        </p>
      </div>
    </div>
  );
}
