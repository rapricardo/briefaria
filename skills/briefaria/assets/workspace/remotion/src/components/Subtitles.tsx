import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { useDelayRender } from "remotion";
import type { Caption } from "@remotion/captions";

// Página de legenda curada manualmente
interface CaptionPageDef {
  startMs: number;
  endMs: number;
  lines: string[];
}

// Renderiza uma página com highlight palavra por palavra
const CaptionPage: React.FC<{
  page: CaptionPageDef;
  tokens: Caption[];
  globalStartMs: number;
}> = ({ page, tokens, globalStartMs }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tempo absoluto no vídeo
  const absoluteTimeMs = globalStartMs + (frame / fps) * 1000;

  // Encontrar tokens que pertencem a esta página (por overlap temporal)
  const pageTokens = tokens.filter(
    (t) => t.startMs >= page.startMs - 50 && t.endMs <= page.endMs + 50
  );

  // Montar as linhas com highlight por palavra
  // Juntar todo o texto dos tokens para match com as linhas manuais
  let tokenIndex = 0;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 60px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 4,
        }}
      >
        {page.lines.map((line, lineIdx) => {
          // Separar palavras da linha manual
          const lineWords = line.split(/\s+/);

          return (
            <div
              key={lineIdx}
              style={{
                fontSize: 72,
                fontFamily: "Arial, sans-serif",
                fontWeight: 700,
                textAlign: "center",
                textTransform: "uppercase",
                lineHeight: 1.2,
              }}
            >
              {lineWords.map((word, wordIdx) => {
                // Tentar match com próximo token
                const token = pageTokens[tokenIndex];
                let isActive = false;

                if (token) {
                  // Normalizar para comparação
                  const tokenWord = token.text.trim().toLowerCase().replace(/[.,?!;:]/g, "");
                  const pageWord = word.toLowerCase().replace(/[.,?!;:]/g, "");

                  if (tokenWord === pageWord) {
                    isActive =
                      token.startMs <= absoluteTimeMs &&
                      token.endMs > absoluteTimeMs;
                    tokenIndex++;
                  }
                }

                return (
                  <span
                    key={wordIdx}
                    style={{
                      color: isActive ? "#FFD700" : "#FFCC00",
                      textShadow: isActive
                        ? "3px 3px 0px #000, -1px -1px 0px #000, 1px -1px 0px #000, -1px 1px 0px #000, 0px 4px 0px #000"
                        : "3px 3px 0px #000, -1px -1px 0px #000, 1px -1px 0px #000, -1px 1px 0px #000",
                    }}
                  >
                    {wordIdx > 0 ? " " : ""}
                    {word}
                  </span>
                );
              })}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Container principal
export const Subtitles: React.FC<{ captionsFile: string }> = ({
  captionsFile,
}) => {
  const [tokens, setTokens] = useState<Caption[] | null>(null);
  const [pages, setPages] = useState<CaptionPageDef[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const { fps } = useVideoConfig();

  const fetchData = useCallback(async () => {
    try {
      const [tokensRes, pagesRes] = await Promise.all([
        fetch(staticFile(captionsFile)),
        fetch(staticFile("caption-pages.json")),
      ]);
      const tokensData = await tokensRes.json();
      const pagesData = await pagesRes.json();
      setTokens(tokensData);
      setPages(pagesData);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [captionsFile, continueRender, cancelRender, handle]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!tokens || !pages) return null;

  return (
    <AbsoluteFill>
      {pages.map((page, index) => {
        const startFrame = Math.round((page.startMs / 1000) * fps);
        const endFrame = Math.round((page.endMs / 1000) * fps);
        const durationInFrames = endFrame - startFrame;

        if (durationInFrames <= 0) return null;

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            <CaptionPage
              page={page}
              tokens={tokens}
              globalStartMs={page.startMs}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
