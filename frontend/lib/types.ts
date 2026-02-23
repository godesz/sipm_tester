/**
 * TypeScript types matching backend Pydantic models.
 * Ensures type safety between frontend and backend.
 * 
 */

// ============================================================================
// Hardware Types
// ============================================================================

export interface ConnectionRequest {
  port: string;
  baudrate?: number;
  timeout?: number;
}

export interface ConnectionResponse {
  status: string;
  port?: string;
  message?: string;
}

export interface StatusResponse {
  device: string;
  connected: boolean;
  [key: string]: any; // Allow additional fields
}

// ============================================================================
// Position Types
// ============================================================================

export interface Position {
  X: number;
  Y: number;
  Z: number;
}

export interface MoveRequest {
  axis: string;
  distance: number;
  feedrate?: number;
}

export interface MoveResponse {
  status: string;
  position: { [axis: string]: number };
  message?: string;
}

export interface Bounds {
  min: number;
  max: number;
}

export interface SetBoundsRequest {
  axis: string;
  min: number;
  max: number;
}

// ============================================================================
// Measurement Types
// ============================================================================

export interface SetLightRequest {
  mode: 1 | 2 | 3; // 1=left, 2=right, 3=all
  r: number; // 0-255
  g: number; // 0-255
  b: number; // 0-255
}

export interface DiodeTestResponse {
  status: string;
  connection_state: number | null;
  connection_name: string;
  is_connected: boolean;
  raw_response?: string;
  message?: string;
}

export interface SiPMDetection {
  x: number; // Center X coordinate in pixels
  y: number; // Center Y coordinate in pixels
  width: number;
  height: number;
  confidence: number; // 0-1
}

export interface DetectionResponse {
  status: string;
  detections: SiPMDetection[];
  count: number;
  message?: string;
}

export interface ProbeRequest {
  start_z?: number;
  rough_step?: number;
  fine_step?: number;
  safe_z_min?: number;
}

export interface ProbeResponse {
  status: string;
  final_z: number | null;
  connection_state: string | null;
  steps_taken: number;
  message?: string;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface MarlinConfig {
  port: string;
  baudrate: number;
  bounds: {
    X: { min: number; max: number };
    Y: { min: number; max: number };
    Z: { min: number; max: number };
  };
}

export interface CameraConfig {
  default_id: number;
  stream_resolution: [number, number];
  capture_resolution: [number, number];
}

export interface MeasurementDeviceConfig {
  port: string;
  baudrate: number;
}

export interface HardwareConfig {
  marlin: MarlinConfig;
  camera: CameraConfig;
  measurement_device: MeasurementDeviceConfig;
}

export interface CalibrationData {
  reference_point: { x: number; y: number; z: number };
  camera_to_pogo_offset: { x: number; y: number };
}

export interface DetectionConfig {
  yellow_hsv_range: {
    lower: [number, number, number];
    upper: [number, number, number];
  };
  min_pad_area: number;
  max_pad_area: number;
}

export interface ProbingConfig {
  rough_step: number;
  fine_step: number;
  safe_z_min: number;
}

export interface StationConfig {
  version: string;
  hardware: HardwareConfig;
  calibration: CalibrationData;
  detection: DetectionConfig;
  probing: ProbingConfig;
}

export interface SetReferencePointRequest {
  x: number;
  y: number;
  z: number;
}

export interface SetCameraOffsetRequest {
  x: number;
  y: number;
}

export interface UpdatePortsRequest {
  marlin_port?: string;
  measurement_port?: string;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface HardwareState {
  marlin: {
    connected: boolean;
    position: Position;
    emergencyStop: boolean;
  };
  camera: {
    connected: boolean;
    availableCameras: number[];
    currentCamera: number;
  };
  measurement: {
    connected: boolean;
    psuEnabled: boolean;
  };
}

export interface OverlaySettings {
  showCrosshair: boolean;
  showGrid: boolean;
  showPOGOOffset: boolean;
  showDetections: boolean;
}

// ============================================================================
// Connection State
// ============================================================================

export type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

export interface DeviceConnection {
  state: ConnectionState;
  port: string;
  error?: string;
}
