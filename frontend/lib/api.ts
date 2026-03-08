/**
 * API client for communicating with the backend.
 * All functions are typed and match backend endpoints.
 */

import { API_BASE_URL, API_ENDPOINTS } from "./constants";
import type {
  ConnectionRequest,
  ConnectionResponse,
  MoveRequest,
  MoveResponse,
  SetLightRequest,
  DiodeTestResponse,
  DetectionResponse,
  ProbeRequest,
  ProbeResponse,
  ProbeSipmResponse,
  StationConfig,
  SetReferencePointRequest,
  SetCameraOffsetRequest,
  UpdatePortsRequest,
  StatusResponse,
} from "./types";

// ============================================================================
// Helper Functions
// ============================================================================

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// ============================================================================
// Motion API
// ============================================================================

export const motionAPI = {
  /**
   * Connect to Marlin controller.
   */
  connect: (request: ConnectionRequest): Promise<ConnectionResponse> =>
    fetchAPI(API_ENDPOINTS.MOTION_CONNECT, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Disconnect from Marlin controller.
   */
  disconnect: (): Promise<{ status: string }> =>
    fetchAPI(API_ENDPOINTS.MOTION_DISCONNECT, { method: "POST" }),

  /**
   * Get current position.
   */
  getPosition: (): Promise<{ position: { X: number; Y: number; Z: number } }> =>
    fetchAPI(API_ENDPOINTS.MOTION_POSITION),

  /**
   * Move an axis by relative distance.
   */
  move: (request: MoveRequest): Promise<MoveResponse> =>
    fetchAPI(API_ENDPOINTS.MOTION_MOVE, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Home all axes.
   */
  home: (): Promise<{ status: string; position: { X: number; Y: number; Z: number } }> =>
    fetchAPI(API_ENDPOINTS.MOTION_HOME, { method: "POST" }),

  /**
   * Activate emergency stop.
   */
  emergencyStop: (): Promise<{ status: string }> =>
    fetchAPI(API_ENDPOINTS.MOTION_EMERGENCY_STOP, { method: "POST" }),

  /**
   * Clear emergency stop.
   */
  clearEmergencyStop: (): Promise<{ status: string }> =>
    fetchAPI(API_ENDPOINTS.MOTION_CLEAR_EMERGENCY_STOP, { method: "POST" }),

  /**
   * Save current position as tray reference point.
   */
  setReference: (): Promise<{ status: string; reference_point: { x: number; y: number; z: number } }> =>
    fetchAPI(API_ENDPOINTS.MOTION_SET_REFERENCE, { method: "POST" }),

  /**
   * Move to saved tray reference point.
   */
  goReference: (): Promise<{ status: string; position: { X: number; Y: number; Z: number } }> =>
    fetchAPI(API_ENDPOINTS.MOTION_GO_REFERENCE, { method: "POST" }),

  /**
   * Move to SiPM by 0-based linear index (id = col + row * columns).
   */
  goSipm: (index: number): Promise<{ status: string; index: number; position: { X: number; Y: number; Z: number } }> =>
    fetchAPI(`/api/motion/go_sipm?index=${index}`, { method: "POST" }),

  /**
   * Get Marlin controller status.
   */
  getStatus: (): Promise<StatusResponse> =>
    fetchAPI(API_ENDPOINTS.MOTION_STATUS),
};

// ============================================================================
// Camera API
// ============================================================================

export const cameraAPI = {
  /**
   * List available cameras.
   */
  listCameras: (): Promise<{ available_cameras: number[] }> =>
    fetchAPI(API_ENDPOINTS.CAMERA_LIST),

  /**
   * Get camera stream URL.
   */
  getStreamURL: (cameraId: number = 0): string =>
    `${API_BASE_URL}${API_ENDPOINTS.CAMERA_STREAM}?camera_id=${cameraId}`,

  /**
   * Capture a high-resolution image.
   */
  capture: (cameraId: number = 0): Promise<{ status: string; file: string; resolution: { width: number; height: number } }> =>
    fetchAPI(API_ENDPOINTS.CAMERA_CAPTURE, {
      method: "POST",
      body: JSON.stringify({ camera_id: cameraId }),
    }),

  /**
   * Run SiPM detection on current camera frame.
   */
  detect: (cameraId: number = 0): Promise<DetectionResponse> =>
    fetchAPI(API_ENDPOINTS.CAMERA_DETECT, {
      method: "POST",
      body: JSON.stringify({ camera_id: cameraId }),
    }),

  /**
   * Get camera manager status.
   */
  getStatus: (): Promise<StatusResponse> =>
    fetchAPI(API_ENDPOINTS.CAMERA_STATUS),

  /**
   * Switch from one camera to another.
   * Properly closes old camera before opening new one.
   */
  switchCamera: (oldCameraId: number, newCameraId: number): Promise<{ status: string; current_camera: number }> =>
    fetchAPI(`${API_ENDPOINTS.CAMERA_SWITCH}?old_camera_id=${oldCameraId}&new_camera_id=${newCameraId}`, {
      method: "POST",
    }),
};

// ============================================================================
// Measurement API
// ============================================================================

export const measurementAPI = {
  /**
   * Connect to measurement device.
   */
  connect: (request: ConnectionRequest): Promise<ConnectionResponse> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_CONNECT, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Disconnect from measurement device.
   */
  disconnect: (): Promise<{ status: string }> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_DISCONNECT, { method: "POST" }),

  /**
   * Enable PSU for testing.
   */
  enablePSU: (): Promise<{ status: string; response: string }> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_ENABLE_PSU, { method: "POST" }),

  /**
   * Set LED light mode and color.
   */
  setLight: (request: SetLightRequest): Promise<{ status: string; response: string }> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_SET_LIGHT, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Turn off all LEDs.
   */
  turnOffLEDs: (): Promise<{ status: string; response: string }> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_TURN_OFF_LEDS, { method: "POST" }),

  /**
   * Get diode measurement / connection state.
   */
  testDiode: (): Promise<DiodeTestResponse> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_TEST_DIODE),

  /**
   * Run Z-axis probing workflow.
   */
  probeZ: (request: ProbeRequest): Promise<ProbeResponse> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_PROBE_Z, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Full SiPM test: detect pads → apply pogo offset → probe Z until contact.
   */
  probeSipm: (cameraId: number = 0): Promise<ProbeSipmResponse> =>
    fetchAPI(`${API_ENDPOINTS.MEASUREMENT_PROBE_SIPM}?camera_id=${cameraId}`, {
      method: "POST",
    }),

  /**
   * Get measurement device status.
   */
  getStatus: (): Promise<StatusResponse> =>
    fetchAPI(API_ENDPOINTS.MEASUREMENT_STATUS),
};

// ============================================================================
// Config API
// ============================================================================

export const configAPI = {
  /**
   * Get current configuration.
   */
  getConfig: (): Promise<StationConfig> =>
    fetchAPI(API_ENDPOINTS.CONFIG_GET),

  /**
   * Set tray corner reference point.
   */
  setReferencePoint: (request: SetReferencePointRequest): Promise<{ status: string; reference_point: { x: number; y: number; z: number } }> =>
    fetchAPI(API_ENDPOINTS.CONFIG_REFERENCE_POINT, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Set camera-to-POGO offset.
   */
  setCameraOffset: (request: SetCameraOffsetRequest): Promise<{ status: string; camera_offset: { x: number; y: number } }> =>
    fetchAPI(API_ENDPOINTS.CONFIG_CAMERA_OFFSET, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Update COM port settings.
   */
  updatePorts: (request: UpdatePortsRequest): Promise<{ status: string; marlin_port?: string; measurement_port?: string }> =>
    fetchAPI(API_ENDPOINTS.CONFIG_PORTS, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Reload configuration from file.
   */
  reload: (): Promise<{ status: string; message: string }> =>
    fetchAPI(API_ENDPOINTS.CONFIG_RELOAD, { method: "POST" }),

  /**
   * Save current configuration to file.
   */
  save: (): Promise<{ status: string; message: string }> =>
    fetchAPI(API_ENDPOINTS.CONFIG_SAVE, { method: "POST" }),
};

// ============================================================================
// Export combined API object
// ============================================================================

export const api = {
  motion: motionAPI,
  camera: cameraAPI,
  measurement: measurementAPI,
  config: configAPI,
};

export default api;
