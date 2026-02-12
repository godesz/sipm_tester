"use client";

/**
 * CameraOverlay - SVG overlay for camera view.
 * Displays crosshair, detections, grid, and POGO offset indicator.
 */

import React, { useState } from "react";
import { COLORS, DETECTION_CIRCLE_RADIUS } from "@/lib/constants";
import type { Position, SiPMDetection } from "@/lib/types";

interface CameraOverlayProps {
  width: number;
  height: number;
  position: Position;
  detections: SiPMDetection[];
  cameraOffset?: { x: number; y: number } | null;
  showCrosshair?: boolean;
  showGrid?: boolean;
  showPOGOOffset?: boolean;
}

export default function CameraOverlay({
  width,
  height,
  position,
  detections,
  cameraOffset,
  showCrosshair = true,
  showGrid = false,
  showPOGOOffset = true,
}: CameraOverlayProps) {
  const centerX = width / 2;
  const centerY = height / 2;

  // Calculate POGO pin position based on offset
  const pogoX = centerX + (cameraOffset?.x || 0);
  const pogoY = centerY + (cameraOffset?.y || 0);

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      width={width}
      height={height}
      style={{ zIndex: 10 }}
    >
      {/* Grid Overlay */}
      {showGrid && (
        <g opacity={0.3}>
          {/* Vertical lines */}
          {Array.from({ length: 10 }).map((_, i) => {
            const x = (i / 9) * width;
            return (
              <line
                key={`v-${i}`}
                x1={x}
                y1={0}
                x2={x}
                y2={height}
                stroke={COLORS.GRID}
                strokeWidth={1}
              />
            );
          })}
          {/* Horizontal lines */}
          {Array.from({ length: 10 }).map((_, i) => {
            const y = (i / 9) * height;
            return (
              <line
                key={`h-${i}`}
                x1={0}
                y1={y}
                x2={width}
                y2={y}
                stroke={COLORS.GRID}
                strokeWidth={1}
              />
            );
          })}
        </g>
      )}

      {/* Crosshair (Camera Center) */}
      {showCrosshair && (
        <g>
          {/* Vertical line */}
          <line
            x1={centerX}
            y1={0}
            x2={centerX}
            y2={height}
            stroke={COLORS.CROSSHAIR}
            strokeWidth={1}
            opacity={0.7}
          />
          {/* Horizontal line */}
          <line
            x1={0}
            y1={centerY}
            x2={width}
            y2={centerY}
            stroke={COLORS.CROSSHAIR}
            strokeWidth={1}
            opacity={0.7}
          />
          {/* Center circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={5}
            stroke={COLORS.CROSSHAIR}
            strokeWidth={2}
            fill="none"
            opacity={0.7}
          />
          {/* Label */}
          <text
            x={centerX + 10}
            y={centerY - 10}
            fill={COLORS.CROSSHAIR}
            fontSize="12"
            fontWeight="bold"
          >
            Camera
          </text>
        </g>
      )}

      {/* Detection Circles */}
      {detections.map((detection, index) => (
        <g key={index}>
          <circle
            cx={detection.x}
            cy={detection.y}
            r={DETECTION_CIRCLE_RADIUS}
            stroke={COLORS.DETECTION}
            strokeWidth={2}
            fill="none"
            opacity={0.8}
          />
          {/* Center dot */}
          <circle
            cx={detection.x}
            cy={detection.y}
            r={3}
            fill={COLORS.DETECTION}
            opacity={0.8}
          />
          {/* Confidence label */}
          <text
            x={detection.x + DETECTION_CIRCLE_RADIUS + 5}
            y={detection.y - DETECTION_CIRCLE_RADIUS - 5}
            fill={COLORS.DETECTION}
            fontSize="10"
            fontWeight="bold"
          >
            #{index + 1} ({(detection.confidence * 100).toFixed(0)}%)
          </text>
        </g>
      ))}

      {/* Camera-to-POGO Offset Indicator */}
      {showPOGOOffset && cameraOffset && (cameraOffset.x !== 0 || cameraOffset.y !== 0) && (
        <g>
          {/* Dashed line from camera to POGO */}
          <line
            x1={centerX}
            y1={centerY}
            x2={pogoX}
            y2={pogoY}
            stroke={COLORS.POGO_OFFSET}
            strokeWidth={2}
            strokeDasharray="5,5"
            opacity={0.8}
          />
          {/* POGO pin position circle */}
          <circle
            cx={pogoX}
            cy={pogoY}
            r={8}
            stroke={COLORS.POGO_OFFSET}
            strokeWidth={2}
            fill={COLORS.POGO_OFFSET}
            opacity={0.5}
          />
          {/* Label */}
          <text
            x={pogoX + 15}
            y={pogoY - 15}
            fill={COLORS.POGO_OFFSET}
            fontSize="12"
            fontWeight="bold"
          >
            POGO
          </text>
          {/* Offset values */}
          <text
            x={pogoX + 15}
            y={pogoY}
            fill={COLORS.POGO_OFFSET}
            fontSize="10"
          >
            Δ({cameraOffset.x.toFixed(1)}, {cameraOffset.y.toFixed(1)})
          </text>
        </g>
      )}
    </svg>
  );
}
