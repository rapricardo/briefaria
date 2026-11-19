import React from "react";
import { Composition } from "remotion";
import { Animatic } from "./compositions/Animatic";
import { Final } from "./compositions/Final";
import { ReelDialogue } from "./compositions/ReelDialogue";
import type { ReelProps } from "./compositions/ReelDialogue";
import type { CompositionProps } from "./types";

const defaultProps: CompositionProps = {
  manifest: {
    project: "",
    client: "",
    branding_file: "",
    settings: { fps: 30, width: 1080, height: 1920, duration_total_s: 33 },
    characters: {},
    scenes: [],
    sfx: [],
  },
  branding: {
    colors: { verde_escuro: "#2B4A2E", creme: "#F6F1EB", dourado: "#C4975A" },
    fonts: { display: "Instrument Serif", body: "DM Sans" },
  },
  timeline: [],
};

function calcDuration(props: CompositionProps) {
  if (props.timeline.length === 0) {
    return { durationInFrames: 990, fps: 30, width: 1080, height: 1920 };
  }
  const last = props.timeline[props.timeline.length - 1];
  return {
    durationInFrames: last.startFrame + last.durationInFrames,
    fps: props.manifest.settings.fps,
    width: props.manifest.settings.width,
    height: props.manifest.settings.height,
  };
}

const reelProps: ReelProps = {
  fps: 30,
  accentColor: "#2563EB",
  logoFile: "",
  clientName: "",
  ctaText: "",
  ctaSubtext: "Sua mensagem final",
  captionsFile: "",
  shots: [],
};

function calcReelDuration(props: ReelProps) {
  const fps = props.fps;
  const transitionFrames = Math.round(fps * 0.3);
  const ctaFrames = Math.round(fps * 3);
  const shotFrames = props.shots.reduce((sum, s) => sum + Math.round(s.duration * fps), 0);
  // Transições encurtam: (nShots) transições * duração
  const totalTransitions = props.shots.length * transitionFrames;
  return {
    durationInFrames: shotFrames - totalTransitions + ctaFrames,
    fps,
    width: 1080,
    height: 1920,
  };
}

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Animatic"
        component={Animatic}
        calculateMetadata={({ props }) => calcDuration(props)}
        defaultProps={defaultProps}
      />
      <Composition
        id="Final"
        component={Final}
        calculateMetadata={({ props }) => calcDuration(props)}
        defaultProps={defaultProps}
      />
      <Composition
        id="ReelDialogue"
        component={ReelDialogue}
        calculateMetadata={({ props }) => calcReelDuration(props)}
        defaultProps={reelProps}
      />
    </>
  );
};
