import React from "react";
import { Audio, OffthreadVideo, staticFile } from "remotion";
import type { Beat as BeatType, Branding, SFX } from "../types";
import { KenBurns } from "./KenBurns";
import { Caption } from "./Caption";

interface BeatProps {
  beat: BeatType;
  mode: "animatic" | "final";
  branding: Branding;
  sfxList: SFX[];
  durationInFrames: number;
}

export const Beat: React.FC<BeatProps> = ({
  beat,
  mode,
  branding,
  sfxList,
  durationInFrames,
}) => {
  const firstKeyframe = beat.keyframes.length > 0 ? beat.keyframes[0] : null;

  const renderVisual = () => {
    if (mode === "final" && beat.clip_file) {
      return (
        <OffthreadVideo
          src={staticFile(beat.clip_file)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      );
    }

    if (firstKeyframe) {
      return <KenBurns src={firstKeyframe} durationInFrames={durationInFrames} motion={beat.motion} />;
    }

    return null;
  };

  const shouldRenderAudio = (): boolean => {
    if (!beat.audio_file) return false;
    if (mode === "final" && beat.video_job.type === "lipsync") return false;
    return true;
  };

  const beatSfx = sfxList.filter(
    (sfx) => sfx.attach_to === beat.id && sfx.file !== null,
  );

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {renderVisual()}

      {shouldRenderAudio() && <Audio src={staticFile(beat.audio_file!)} />}

      {beatSfx.map((sfx) => (
        <Audio key={sfx.id} src={staticFile(sfx.file!)} volume={0.5} />
      ))}

      {beat.caption !== null && (
        <Caption text={beat.caption} branding={branding} />
      )}
    </div>
  );
};
