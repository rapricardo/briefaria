// remotion/src/types.ts
export interface ManifestSettings {
  fps: number;
  width: number;
  height: number;
  duration_total_s: number;
}

export interface ManifestCharacter {
  voice_id: string | null;
  role: string;
}

export interface VideoJob {
  type: "lipsync" | "interpolation" | "action" | "broll";
  api?: string;
  prompt?: string;
  negative_prompt?: string;
}

export interface Beat {
  id: string;
  duration_s: number;
  type: "scene" | "broll" | "metafora" | "pausa" | "dado";
  visual: string;
  keyframes: string[];
  who: string;
  audio_text: string | null;
  audio_file: string | null;
  clip_file: string | null;
  motion?: string;
  caption: string | null;
  video_job: VideoJob;
}

export interface Scene {
  id: string;
  act: number;
  duration_s: number;
  beats: Beat[];
}

export interface SFX {
  id: string;
  description: string;
  file: string | null;
  attach_to: string;
}

export interface Manifest {
  project: string;
  client: string;
  branding_file: string;
  settings: ManifestSettings;
  characters: Record<string, ManifestCharacter>;
  scenes: Scene[];
  sfx: SFX[];
}

// --- Branding & Timeline types ---

export interface Branding {
  colors: {
    verde_escuro: string;
    creme: string;
    dourado: string;
  };
  fonts: {
    display: string;
    body: string;
  };
}

export interface BeatTimeline {
  beatId: string;
  startFrame: number;
  durationInFrames: number;
}

// Props passed from calculateMetadata to compositions (all paths pre-resolved)
// Index signature required by Remotion's Composition<Props extends Record<string, unknown>>
export interface CompositionProps extends Record<string, unknown> {
  manifest: Manifest;
  branding: Branding;
  timeline: BeatTimeline[];
}
