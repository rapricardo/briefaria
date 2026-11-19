import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import type { Branding } from "../types";

interface CaptionProps {
  text: string;
  branding: Branding;
}

export const Caption: React.FC<CaptionProps> = ({ text, branding }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
      }}
    >
      <div
        style={{
          backgroundColor: `${branding.colors.verde_escuro}CC`,
          color: branding.colors.creme,
          fontFamily: branding.fonts.body,
          fontSize: 36,
          padding: "12px 32px",
          borderRadius: 12,
          textAlign: "center",
          maxWidth: "90%",
        }}
      >
        {text}
      </div>
    </div>
  );
};
