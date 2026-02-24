"use client";

/**
 * ConnectionPanel - Manages hardware connections.
 * Provides port configuration and connect/disconnect controls.
 */

import React, { useState } from "react";
import { useHardware } from "@/contexts/HardwareContext";
import { useConfig } from "@/contexts/ConfigContext";
import { DEFAULT_BAUDRATE } from "@/lib/constants";

export default function ConnectionPanel() {
  const { marlin, measurement, connectMarlin, disconnectMarlin, connectMeasurement, disconnectMeasurement } = useHardware();
  const { getMarlinPort, getMeasurementPort } = useConfig();

  const [marlinPort, setMarlinPort] = useState(getMarlinPort());
  const [measurementPort, setMeasurementPort] = useState(getMeasurementPort());

  const handleConnectMarlin = async () => {
    await connectMarlin(marlinPort, DEFAULT_BAUDRATE);
  };

  const handleDisconnectMarlin = async () => {
    await disconnectMarlin();
  };

  const handleConnectMeasurement = async () => {
    await connectMeasurement(measurementPort, DEFAULT_BAUDRATE);
  };

  const handleDisconnectMeasurement = async () => {
    await disconnectMeasurement();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">Hardware Connections</h3>

      {/* Marlin Connection */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold">Marlin (LumenPnP)</h4>
          <StatusDot connected={marlin.connected} />
        </div>

        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={marlinPort}
            onChange={(e) => setMarlinPort(e.target.value)}
            placeholder="COM4"
            disabled={marlin.connected || marlin.connecting}
            className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          {marlin.connected ? (
            <button
              onClick={handleDisconnectMarlin}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 font-medium"
            >
              Disconnect
            </button>
          ) : (
            <button
              onClick={handleConnectMarlin}
              disabled={marlin.connecting}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400 font-medium"
            >
              {marlin.connecting ? "Connecting..." : "Connect"}
            </button>
          )}
        </div>

        {marlin.error && (
          <div className="text-red-600 text-sm">{marlin.error}</div>
        )}
      </div>

      {/* Measurement Device Connection */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold">Measurement Device</h4>
          <StatusDot connected={measurement.connected} />
        </div>

        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={measurementPort}
            onChange={(e) => setMeasurementPort(e.target.value)}
            placeholder="COM5"
            disabled={measurement.connected || measurement.connecting}
            className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          {measurement.connected ? (
            <button
              onClick={handleDisconnectMeasurement}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 font-medium"
            >
              Disconnect
            </button>
          ) : (
            <button
              onClick={handleConnectMeasurement}
              disabled={measurement.connecting}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400 font-medium"
            >
              {measurement.connecting ? "Connecting..." : "Connect"}
            </button>
          )}
        </div>

        {measurement.error && (
          <div className="text-red-600 text-sm">{measurement.error}</div>
        )}
      </div>

      {/* Camera Info (Always Available) */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold">Camera</h4>
          <StatusDot connected={true} />
        </div>
        <div className="text-sm text-gray-600">
          Camera manager ready (USB cameras auto-detected)
        </div>
      </div>

      {/* Quick Connect All Button */}
      {!marlin.connected && !measurement.connected && (
        <button
          onClick={() => {
            handleConnectMarlin();
            handleConnectMeasurement();
          }}
          disabled={marlin.connecting || measurement.connecting}
          className="w-full mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 font-medium"
        >
          Connect All
        </button>
      )}
    </div>
  );
}

/**
 * Status indicator dot component.
 */
function StatusDot({ connected }: { connected: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-3 h-3 rounded-full ${
          connected ? "bg-green-500 animate-pulse" : "bg-red-500"
        }`}
      />
      <span className="text-sm text-gray-600">
        {connected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}
