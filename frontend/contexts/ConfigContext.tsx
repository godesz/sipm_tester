"use client";

/**
 * Config Context - Manages global configuration state.
 * Handles reference points, camera offset, and hardware settings.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import type { StationConfig } from "@/lib/types";

// ============================================================================
// Context Types
// ============================================================================

interface ConfigContextType {
  // Configuration state
  config: StationConfig | null;
  loading: boolean;
  error: string | null;

  // Configuration actions
  loadConfig: () => Promise<void>;
  setReferencePoint: (x: number, y: number, z: number) => Promise<void>;
  setCameraOffset: (x: number, y: number) => Promise<void>;
  updatePorts: (marlinPort?: string, measurementPort?: string) => Promise<void>;
  reloadConfig: () => Promise<void>;
  saveConfig: () => Promise<void>;

  // Helper getters
  getReferencePoint: () => { x: number; y: number; z: number } | null;
  getCameraOffset: () => { x: number; y: number } | null;
  getMarlinPort: () => string;
  getMeasurementPort: () => string;
}

// ============================================================================
// Default Configuration
// ============================================================================

const DEFAULT_CONFIG: StationConfig = {
  version: "1.0",
  hardware: {
    marlin: {
      port: "COM4",
      baudrate: 115200,
      bounds: {
        X: { min: 0, max: 500 },
        Y: { min: 0, max: 500 },
        Z: { min: 40, max: 50 },
      },
    },
    camera: {
      default_id: 0,
      stream_resolution: [640, 480],
      capture_resolution: [1920, 1080],
    },
    measurement_device: {
      port: "COM5",
      baudrate: 115200,
    },
  },
  calibration: {
    reference_point: { x: 0, y: 0, z: 0 },
    camera_to_pogo_offset: { x: 0, y: 0 },
  },
  detection: {
    yellow_hsv_range: {
      lower: [20, 100, 100],
      upper: [40, 255, 255],
    },
    min_pad_area: 100,
    max_pad_area: 10000,
  },
  probing: {
    rough_step: 1.0,
    fine_step: 0.1,
    safe_z_min: 40.0,
  },
};

// ============================================================================
// Create Context
// ============================================================================

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<StationConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ========================================================================
  // Configuration Actions
  // ========================================================================

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.config.getConfig();
      setConfig(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load configuration");
      // Use default config on error
      setConfig(DEFAULT_CONFIG);
    } finally {
      setLoading(false);
    }
  }, []);

  const setReferencePoint = useCallback(async (x: number, y: number, z: number) => {
    try {
      await api.config.setReferencePoint({ x, y, z });
      // Reload config to get updated values
      await loadConfig();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set reference point");
      throw err;
    }
  }, [loadConfig]);

  const setCameraOffset = useCallback(async (x: number, y: number) => {
    try {
      await api.config.setCameraOffset({ x, y });
      // Reload config to get updated values
      await loadConfig();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set camera offset");
      throw err;
    }
  }, [loadConfig]);

  const updatePorts = useCallback(async (marlinPort?: string, measurementPort?: string) => {
    try {
      await api.config.updatePorts({
        marlin_port: marlinPort,
        measurement_port: measurementPort,
      });
      // Reload config to get updated values
      await loadConfig();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update ports");
      throw err;
    }
  }, [loadConfig]);

  const reloadConfig = useCallback(async () => {
    try {
      await api.config.reload();
      await loadConfig();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reload configuration");
      throw err;
    }
  }, [loadConfig]);

  const saveConfig = useCallback(async () => {
    try {
      await api.config.save();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save configuration");
      throw err;
    }
  }, []);

  // ========================================================================
  // Helper Getters
  // ========================================================================

  const getReferencePoint = useCallback(() => {
    return config?.calibration.reference_point || null;
  }, [config]);

  const getCameraOffset = useCallback(() => {
    return config?.calibration.camera_to_pogo_offset || null;
  }, [config]);

  const getMarlinPort = useCallback(() => {
    return config?.hardware.marlin.port || "COM4";
  }, [config]);

  const getMeasurementPort = useCallback(() => {
    return config?.hardware.measurement_device.port || "COM5";
  }, [config]);

  // ========================================================================
  // Load Configuration on Mount
  // ========================================================================

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // ========================================================================
  // Context Value
  // ========================================================================

  const value: ConfigContextType = {
    config,
    loading,
    error,
    loadConfig,
    setReferencePoint,
    setCameraOffset,
    updatePorts,
    reloadConfig,
    saveConfig,
    getReferencePoint,
    getCameraOffset,
    getMarlinPort,
    getMeasurementPort,
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
}

// ============================================================================
// Custom Hook
// ============================================================================

export function useConfig() {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error("useConfig must be used within ConfigProvider");
  }
  return context;
}
