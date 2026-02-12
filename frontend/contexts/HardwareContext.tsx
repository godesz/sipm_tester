"use client";

/**
 * Hardware Context - Manages global state for all hardware devices.
 * Provides connection state, position, and control functions.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import { POLLING_INTERVALS } from "@/lib/constants";
import type { Position, ConnectionState, SiPMDetection } from "@/lib/types";

// ============================================================================
// Context Types
// ============================================================================

interface HardwareContextType {
  // Marlin state
  marlin: {
    connected: boolean;
    connecting: boolean;
    position: Position;
    emergencyStop: boolean;
    error: string | null;
  };

  // Camera state
  camera: {
    connected: boolean;
    availableCameras: number[];
    currentCamera: number;
    detections: SiPMDetection[];
    detecting: boolean;
    error: string | null;
  };

  // Measurement device state
  measurement: {
    connected: boolean;
    connecting: boolean;
    lastConnectionState: number | null;
    lastConnectionName: string;
    isContactDetected: boolean;
    error: string | null;
  };

  // Marlin actions
  connectMarlin: (port: string, baudrate?: number) => Promise<void>;
  disconnectMarlin: () => Promise<void>;
  move: (axis: string, distance: number) => Promise<void>;
  home: () => Promise<void>;
  activateEmergencyStop: () => Promise<void>;
  clearEmergencyStop: () => Promise<void>;
  refreshPosition: () => Promise<void>;

  // Camera actions
  listCameras: () => Promise<void>;
  setCurrentCamera: (id: number) => void;
  captureImage: () => Promise<void>;
  detectSiPMs: () => Promise<void>;
  clearDetections: () => void;

  // Measurement device actions
  connectMeasurement: (port: string, baudrate?: number) => Promise<void>;
  disconnectMeasurement: () => Promise<void>;
  enablePSU: () => Promise<void>;
  setLight: (mode: 1 | 2 | 3, r: number, g: number, b: number) => Promise<void>;
  turnOffLEDs: () => Promise<void>;
  testDiode: () => Promise<void>;
  probeZ: (startZ?: number) => Promise<void>;
}

// ============================================================================
// Create Context
// ============================================================================

const HardwareContext = createContext<HardwareContextType | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

export function HardwareProvider({ children }: { children: React.ReactNode }) {
  // Marlin state
  const [marlin, setMarlin] = useState({
    connected: false,
    connecting: false,
    position: { X: 0, Y: 0, Z: 0 },
    emergencyStop: false,
    error: null as string | null,
  });

  // Camera state
  const [camera, setCamera] = useState({
    connected: true, // Camera manager is always "connected"
    availableCameras: [] as number[],
    currentCamera: 0,
    detections: [] as SiPMDetection[],
    detecting: false,
    error: null as string | null,
  });

  // Measurement device state
  const [measurement, setMeasurement] = useState({
    connected: false,
    connecting: false,
    lastConnectionState: null as number | null,
    lastConnectionName: "unknown",
    isContactDetected: false,
    error: null as string | null,
  });

  // ========================================================================
  // Marlin Actions
  // ========================================================================

  const connectMarlin = useCallback(async (port: string, baudrate: number = 115200) => {
    setMarlin(prev => ({ ...prev, connecting: true, error: null }));
    try {
      await api.motion.connect({ port, baudrate });
      setMarlin(prev => ({ ...prev, connected: true, connecting: false }));
      // Refresh position after connection
      refreshPosition();
    } catch (error) {
      setMarlin(prev => ({
        ...prev,
        connected: false,
        connecting: false,
        error: error instanceof Error ? error.message : "Connection failed"
      }));
    }
  }, []);

  const disconnectMarlin = useCallback(async () => {
    try {
      await api.motion.disconnect();
      setMarlin(prev => ({ ...prev, connected: false }));
    } catch (error) {
      setMarlin(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Disconnection failed"
      }));
    }
  }, []);

  const move = useCallback(async (axis: string, distance: number) => {
    try {
      const response = await api.motion.move({ axis, distance });
      setMarlin(prev => ({ ...prev, position: response.position as Position, error: null }));
    } catch (error) {
      setMarlin(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Movement failed"
      }));
      throw error;
    }
  }, []);

  const home = useCallback(async () => {
    try {
      const response = await api.motion.home();
      setMarlin(prev => ({ ...prev, position: response.position as Position, error: null }));
    } catch (error) {
      setMarlin(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Homing failed"
      }));
      throw error;
    }
  }, []);

  const activateEmergencyStop = useCallback(async () => {
    try {
      await api.motion.emergencyStop();
      setMarlin(prev => ({ ...prev, emergencyStop: true }));
    } catch (error) {
      console.error("Emergency stop activation failed:", error);
    }
  }, []);

  const clearEmergencyStop = useCallback(async () => {
    try {
      await api.motion.clearEmergencyStop();
      setMarlin(prev => ({ ...prev, emergencyStop: false, error: null }));
    } catch (error) {
      console.error("Clear emergency stop failed:", error);
    }
  }, []);

  const refreshPosition = useCallback(async () => {
    if (!marlin.connected) return;

    try {
      const response = await api.motion.getPosition();
      setMarlin(prev => ({ ...prev, position: response.position as Position }));
    } catch (error) {
      console.error("Position refresh failed:", error);
    }
  }, [marlin.connected]);

  // ========================================================================
  // Camera Actions
  // ========================================================================

  const listCameras = useCallback(async () => {
    try {
      const response = await api.camera.listCameras();
      setCamera(prev => ({ ...prev, availableCameras: response.available_cameras, error: null }));
    } catch (error) {
      setCamera(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Failed to list cameras"
      }));
    }
  }, []);

  const setCurrentCamera = useCallback((id: number) => {
    setCamera(prev => ({ ...prev, currentCamera: id }));
  }, []);

  const captureImage = useCallback(async () => {
    try {
      await api.camera.capture(camera.currentCamera);
      // Success - image saved on backend
    } catch (error) {
      setCamera(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Image capture failed"
      }));
    }
  }, [camera.currentCamera]);

  const detectSiPMs = useCallback(async () => {
    setCamera(prev => ({ ...prev, detecting: true, error: null }));
    try {
      const response = await api.camera.detect(camera.currentCamera);
      setCamera(prev => ({
        ...prev,
        detections: response.detections,
        detecting: false
      }));
    } catch (error) {
      setCamera(prev => ({
        ...prev,
        detecting: false,
        error: error instanceof Error ? error.message : "Detection failed"
      }));
    }
  }, [camera.currentCamera]);

  const clearDetections = useCallback(() => {
    setCamera(prev => ({ ...prev, detections: [] }));
  }, []);

  // ========================================================================
  // Measurement Device Actions
  // ========================================================================

  const connectMeasurement = useCallback(async (port: string, baudrate: number = 115200) => {
    setMeasurement(prev => ({ ...prev, connecting: true, error: null }));
    try {
      await api.measurement.connect({ port, baudrate });
      setMeasurement(prev => ({ ...prev, connected: true, connecting: false }));
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        connected: false,
        connecting: false,
        error: error instanceof Error ? error.message : "Connection failed"
      }));
    }
  }, []);

  const disconnectMeasurement = useCallback(async () => {
    try {
      await api.measurement.disconnect();
      setMeasurement(prev => ({ ...prev, connected: false }));
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Disconnection failed"
      }));
    }
  }, []);

  const enablePSU = useCallback(async () => {
    try {
      await api.measurement.enablePSU();
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "PSU enable failed"
      }));
    }
  }, []);

  const setLight = useCallback(async (mode: 1 | 2 | 3, r: number, g: number, b: number) => {
    try {
      await api.measurement.setLight({ mode, r, g, b });
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Set light failed"
      }));
    }
  }, []);

  const turnOffLEDs = useCallback(async () => {
    try {
      await api.measurement.turnOffLEDs();
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Turn off LEDs failed"
      }));
    }
  }, []);

  const testDiode = useCallback(async () => {
    try {
      const response = await api.measurement.testDiode();
      setMeasurement(prev => ({
        ...prev,
        lastConnectionState: response.connection_state,
        lastConnectionName: response.connection_name,
        isContactDetected: response.is_connected,
        error: null
      }));
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Diode test failed"
      }));
    }
  }, []);

  const probeZ = useCallback(async (startZ?: number) => {
    try {
      const response = await api.measurement.probeZ({ start_z: startZ });
      if (response.status === "connected") {
        // Probing successful
        console.log(`Contact detected at Z=${response.final_z}`);
      }
    } catch (error) {
      setMeasurement(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Z probing failed"
      }));
    }
  }, []);

  // ========================================================================
  // Position Polling
  // ========================================================================

  useEffect(() => {
    if (!marlin.connected) return;

    const interval = setInterval(() => {
      refreshPosition();
    }, POLLING_INTERVALS.POSITION);

    return () => clearInterval(interval);
  }, [marlin.connected, refreshPosition]);

  // ========================================================================
  // Context Value
  // ========================================================================

  const value: HardwareContextType = {
    marlin,
    camera,
    measurement,
    connectMarlin,
    disconnectMarlin,
    move,
    home,
    activateEmergencyStop,
    clearEmergencyStop,
    refreshPosition,
    listCameras,
    setCurrentCamera,
    captureImage,
    detectSiPMs,
    clearDetections,
    connectMeasurement,
    disconnectMeasurement,
    enablePSU,
    setLight,
    turnOffLEDs,
    testDiode,
    probeZ,
  };

  return (
    <HardwareContext.Provider value={value}>
      {children}
    </HardwareContext.Provider>
  );
}

// ============================================================================
// Custom Hook
// ============================================================================

export function useHardware() {
  const context = useContext(HardwareContext);
  if (!context) {
    throw new Error("useHardware must be used within HardwareProvider");
  }
  return context;
}
