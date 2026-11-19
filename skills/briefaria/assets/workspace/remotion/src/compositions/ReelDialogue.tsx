import React from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { Video } from "@remotion/media";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Subtitles } from "../components/Subtitles";

// Dados do reel — storyboard simplificado
export interface ReelShot {
  id: number;
  clipFile: string;
  duration: number; // segundos
  personagem: string;
  vo: string;
  secao: string;
}

export interface ReelProps extends Record<string, unknown> {
  shots: ReelShot[];
  logoFile: string;
  clientName: string;
  ctaText: string;
  ctaSubtext: string;
  accentColor: string;
  captionsFile: string;
  fps: number;
}

// Lower third — nome do personagem com animação
const LowerThird: React.FC<{
  name: string;
  accentColor: string;
  durationInFrames: number;
}> = ({ name, accentColor, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in nos primeiros 0.4s, fade out nos últimos 0.4s
  const fadeIn = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - Math.round(fps * 0.4), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );
  const opacity = Math.min(fadeIn, fadeOut);

  // Slide up de 10px
  const translateY = interpolate(frame, [0, Math.round(fps * 0.4)], [10, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 120,
        left: 40,
        opacity,
        transform: `translateY(${translateY}px)`,
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}
    >
      <div
        style={{
          width: 6,
          height: 48,
          backgroundColor: accentColor,
          borderRadius: 3,
        }}
      />
      <span
        style={{
          fontFamily: "Arial, sans-serif",
          fontWeight: 500,
          fontSize: 56,
          color: "white",
          textShadow: "0 3px 12px rgba(0,0,0,0.8)",
          letterSpacing: 2,
        }}
      >
        {name}
      </span>
    </div>
  );
};

// Logo watermark — canto superior direito
const LogoWatermark: React.FC<{ logoFile: string }> = ({ logoFile }) => {
  return (
    <Img
      src={staticFile(logoFile)}
      style={{
        position: "absolute",
        top: 40,
        right: 40,
        width: 200,
        opacity: 0.7,
      }}
    />
  );
};

// Card CTA final
const CtaCard: React.FC<{
  logoFile: string;
  clientName: string;
  ctaText: string;
  ctaSubtext: string;
  accentColor: string;
}> = ({ logoFile, ctaSubtext, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = interpolate(frame, [0, Math.round(fps * 0.6)], [0.85, 1], {
    extrapolateRight: "clamp",
  });
  const logoOpacity = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp",
  });
  const textOpacity = interpolate(
    frame,
    [Math.round(fps * 0.4), Math.round(fps * 0.9)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const lineWidth = interpolate(
    frame,
    [Math.round(fps * 0.3), Math.round(fps * 0.8)],
    [0, 400],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a0a",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 60,
      }}
    >
      {logoFile && (
        <Img
          src={staticFile(logoFile)}
          style={{ width: 500, opacity: logoOpacity, transform: `scale(${logoScale})` }}
        />
      )}
      {/* Linha decorativa laranja */}
      <div
        style={{
          width: lineWidth,
          height: 3,
          backgroundColor: accentColor,
          borderRadius: 2,
        }}
      />
      <div
        style={{
          opacity: textOpacity,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 0,
          maxWidth: 800,
          paddingLeft: 60,
          paddingRight: 60,
        }}
      >
        <span
          style={{
            fontFamily: "Arial, sans-serif",
            fontWeight: 700,
            fontSize: 52,
            color: "white",
            letterSpacing: 3,
            textAlign: "center",
            lineHeight: 1.25,
          }}
        >
          {ctaSubtext}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// Composição principal
export const ReelDialogue: React.FC<ReelProps> = ({
  shots,
  logoFile,
  clientName,
  ctaText,
  ctaSubtext,
  accentColor,
  captionsFile,
  fps,
}) => {
  const transitionDuration = Math.round(fps * 0.3); // 0.3s crossfade
  const ctaDuration = Math.round(fps * 3); // 3s CTA card

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <TransitionSeries>
        {shots.map((shot, i) => {
          const durationInFrames = Math.round(shot.duration * fps);
          return (
            <React.Fragment key={shot.id}>
              {i > 0 && (
                <TransitionSeries.Transition
                  presentation={fade()}
                  timing={linearTiming({
                    durationInFrames: transitionDuration,
                  })}
                />
              )}
              <TransitionSeries.Sequence durationInFrames={durationInFrames}>
                <AbsoluteFill>
                  <Video
                    src={staticFile(shot.clipFile)}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                  {logoFile && <LogoWatermark logoFile={logoFile} />}
                  <LowerThird
                    name={shot.personagem}
                    accentColor={accentColor}
                    durationInFrames={durationInFrames}
                  />
                </AbsoluteFill>
              </TransitionSeries.Sequence>
            </React.Fragment>
          );
        })}
        {/* CTA card final */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: transitionDuration })}
        />
        <TransitionSeries.Sequence durationInFrames={ctaDuration}>
          <CtaCard
            logoFile={logoFile}
            clientName={clientName}
            ctaText={ctaText}
            ctaSubtext={ctaSubtext}
            accentColor={accentColor}
          />
        </TransitionSeries.Sequence>
      </TransitionSeries>
      {/* Legendas desativadas — serão adicionadas direto no Instagram */}
      {/* <Subtitles captionsFile={captionsFile} /> */}
    </AbsoluteFill>
  );
};
