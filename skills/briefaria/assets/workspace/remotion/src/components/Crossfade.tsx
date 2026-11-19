import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

interface CrossfadeProps {
  durationInFrames: number;
  children: React.ReactNode;
}

export const Crossfade: React.FC<CrossfadeProps> = ({
  durationInFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ opacity, width: "100%", height: "100%" }}>{children}</div>
  );
};
