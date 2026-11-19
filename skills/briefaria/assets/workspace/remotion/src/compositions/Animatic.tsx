import React from "react";
import { Sequence } from "remotion";
import { Beat } from "../components/Beat";
import type { CompositionProps } from "../types";

export const Animatic: React.FC<CompositionProps> = ({
  manifest,
  branding,
  timeline,
}) => {
  return (
    <div style={{ width: "100%", height: "100%", backgroundColor: branding.colors.creme }}>
      {manifest.scenes.flatMap((scene) =>
        scene.beats.map((beat) => {
          const entry = timeline.find((t) => t.beatId === beat.id);
          if (!entry) return null;
          return (
            <Sequence
              key={beat.id}
              from={entry.startFrame}
              durationInFrames={entry.durationInFrames}
            >
              <Beat
                beat={beat}
                mode="animatic"
                branding={branding}
                sfxList={manifest.sfx}
                durationInFrames={entry.durationInFrames}
              />
            </Sequence>
          );
        })
      )}
    </div>
  );
};
