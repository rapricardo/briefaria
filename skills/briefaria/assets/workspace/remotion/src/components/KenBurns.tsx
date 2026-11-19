import React from "react";
import { useCurrentFrame, interpolate, Img, staticFile } from "remotion";

type MotionType =
  | "static"
  | "slow_zoom_in"
  | "slow_zoom_out"
  | "slow_pan_left"
  | "slow_pan_right"
  | "slow_pan_up"
  | "slow_pan_down"
  | "zoom_and_pan_right"
  | "zoom_and_pan_left";

interface MotionConfig {
  scale: [number, number];
  x: [number, number];
  y: [number, number];
}

const MOTION_CONFIGS: Record<MotionType, MotionConfig> = {
  static:             { scale: [1.02, 1.02], x: [0, 0],  y: [0, 0] },
  slow_zoom_in:       { scale: [1.0, 1.08],  x: [0, 0],  y: [0, 0] },
  slow_zoom_out:      { scale: [1.08, 1.0],  x: [0, 0],  y: [0, 0] },
  slow_pan_right:     { scale: [1.05, 1.05], x: [0, -3], y: [0, 0] },
  slow_pan_left:      { scale: [1.05, 1.05], x: [0, 3],  y: [0, 0] },
  slow_pan_up:        { scale: [1.05, 1.05], x: [0, 0],  y: [0, -3] },
  slow_pan_down:      { scale: [1.05, 1.05], x: [0, 0],  y: [0, 3] },
  zoom_and_pan_right: { scale: [1.0, 1.08],  x: [0, -3], y: [0, 0] },
  zoom_and_pan_left:  { scale: [1.0, 1.08],  x: [0, 3],  y: [0, 0] },
};

interface KenBurnsProps {
  src: string;
  durationInFrames: number;
  motion?: string;
}

export const KenBurns: React.FC<KenBurnsProps> = ({
  src,
  durationInFrames,
  motion,
}) => {
  const frame = useCurrentFrame();
  const motionKey = (motion && motion in MOTION_CONFIGS
    ? motion
    : "slow_zoom_in") as MotionType;
  const config = MOTION_CONFIGS[motionKey];

  const scale = interpolate(frame, [0, durationInFrames], config.scale, {
    extrapolateRight: "clamp",
  });
  const x = interpolate(frame, [0, durationInFrames], config.x, {
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [0, durationInFrames], config.y, {
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${x}%, ${y}%)`,
        }}
      />
    </div>
  );
};
