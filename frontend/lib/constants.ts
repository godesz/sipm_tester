/**
 * Application constants.
 */

// ============================================================================
// API Configuration
// ============================================================================

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  // Motion endpoints
  MOTION_CONNECT: "/api/motion/connect",
  MOTION_DISCONNECT: "/api/motion/disconnect",
  MOTION_POSITION: "/api/motion/position",
  MOTION_MOVE: "/api/motion/move",
  MOTION_HOME: "/api/motion/home",
  MOTION_EMERGENCY_STOP: "/api/motion/emergency_stop",
  MOTION_CLEAR_EMERGENCY_STOP: "/api/motion/clear_emergency_stop",
  MOTION_STATUS: "/api/motion/status",

  // Camera endpoints
  CAMERA_LIST: "/api/camera/list",
  CAMERA_STREAM: "/api/camera/stream",
  CAMERA_CAPTURE: "/api/camera/capture",
  CAMERA_DETECT: "/api/camera/detect",
  CAMERA_STATUS: "/api/camera/status",
  CAMERA_SWITCH: "/api/camera/switch",

  // Measurement endpoints
  MEASUREMENT_CONNECT: "/api/measurement/connect",
  MEASUREMENT_DISCONNECT: "/api/measurement/disconnect",
  MEASUREMENT_ENABLE_PSU: "/api/measurement/enable_psu",
  MEASUREMENT_SET_LIGHT: "/api/measurement/set_light",
  MEASUREMENT_TURN_OFF_LEDS: "/api/measurement/turn_off_leds",
  MEASUREMENT_TEST_DIODE: "/api/measurement/test_diode",
  MEASUREMENT_PROBE_Z: "/api/measurement/probe_z",
  MEASUREMENT_STATUS: "/api/measurement/status",

  // Config endpoints
  CONFIG_GET: "/api/config",
  CONFIG_REFERENCE_POINT: "/api/config/reference_point",
  CONFIG_CAMERA_OFFSET: "/api/config/camera_offset",
  CONFIG_PORTS: "/api/config/ports",
  CONFIG_RELOAD: "/api/config/reload",
  CONFIG_SAVE: "/api/config/save",
} as const;

// ============================================================================
// Hardware Configuration
// ============================================================================

export const DEFAULT_PORTS = {
  MARLIN: "COM3",
  MEASUREMENT: "COM5",
} as const;

export const DEFAULT_BAUDRATE = 115200;

export const MOVEMENT_STEPS = {
  SMALL: 0.1, // mm
  MEDIUM: 1.0, // mm
  LARGE: 10.0, // mm
} as const;

export const FEEDRATE = {
  SLOW: 1000, // mm/min
  NORMAL: 5000, // mm/min
  FAST: 10000, // mm/min
} as const;

// ============================================================================
// Light Modes
// ============================================================================

export const LIGHT_MODES = {
  LEFT: 1,
  RIGHT: 2,
  ALL: 3,
} as const;

export const LIGHT_MODE_NAMES = {
  [LIGHT_MODES.LEFT]: "Left",
  [LIGHT_MODES.RIGHT]: "Right",
  [LIGHT_MODES.ALL]: "All",
} as const;

// ============================================================================
// Connection States
// ============================================================================

export const CONNECTION_STATE_NAMES = {
  0: "Short",
  1: "OK (Connected)",
  2: "Not Valid",
  3: "Open",
  255: "I2C Error",
} as const;

export const CONNECTION_STATE_COLORS = {
  0: "text-red-500", // Short
  1: "text-green-500", // OK
  2: "text-yellow-500", // Not Valid
  3: "text-orange-500", // Open
  255: "text-red-600", // I2C Error
} as const;

// ============================================================================
// UI Colors
// ============================================================================

export const COLORS = {
  CROSSHAIR: "#FF0000", // Red
  DETECTION: "#00FF00", // Green
  POGO_OFFSET: "#0000FF", // Blue
  GRID: "#888888", // Gray
} as const;

// ============================================================================
// Polling Intervals (ms)
// ============================================================================

export const POLLING_INTERVALS = {
  POSITION: 500, // Poll position every 500ms
  STATUS: 2000, // Poll device status every 2s
} as const;

// ============================================================================
// Emergency Stop
// ============================================================================

export const EMERGENCY_STOP_TIMEOUT = 2000; // 2 seconds for double-press

// ============================================================================
// Detection Settings
// ============================================================================

export const DETECTION_CIRCLE_RADIUS = 30; // pixels

// ============================================================================
// Camera Settings
// ============================================================================

export const CAMERA_STREAM_SIZE = {
  WIDTH: 640,
  HEIGHT: 480,
} as const;
