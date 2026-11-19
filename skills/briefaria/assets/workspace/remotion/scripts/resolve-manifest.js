#!/usr/bin/env node
/**
 * Reads a manifest.json, resolves all relative asset paths,
 * parses branding, builds timeline, and outputs CompositionProps as JSON.
 *
 * Usage: resolve-manifest.js <manifest-path> [prefix]
 *
 * prefix: prepended to all asset paths (e.g. "prod" → "/prod/imagens/F01-A.png")
 *         This maps to the symlink inside remotion/public/.
 */
const fs = require("fs");
const path = require("path");

const manifestPath = process.argv[2];
const prefix = process.argv[3] || "";

if (!manifestPath) {
  console.error("Usage: resolve-manifest.js <manifest-path> [prefix]");
  process.exit(1);
}

const absManifestPath = path.resolve(manifestPath);
const manifestDir = path.dirname(absManifestPath);

const manifest = JSON.parse(fs.readFileSync(absManifestPath, "utf-8"));

// Resolve branding
const brandingPath = path.resolve(manifestDir, manifest.branding_file);
const brandingJson = JSON.parse(fs.readFileSync(brandingPath, "utf-8"));

// Parse colors
const colorMap = new Map();
const hexPattern = /(\w[\w\s]*?)\s*\(#([0-9A-Fa-f]{6})\)/g;
let match;
while ((match = hexPattern.exec(brandingJson.cores || "")) !== null) {
  colorMap.set(match[1].trim().toLowerCase(), `#${match[2]}`);
}

// Parse fonts
const displayMatch = (brandingJson.fontes || "").match(/Display:\s*(.+?)\s*\(/i);
const bodyMatch = (brandingJson.fontes || "").match(/Corpo:\s*(.+?)\s*\(/i);

const branding = {
  colors: {
    verde_escuro: colorMap.get("verde escuro") || "#2B4A2E",
    creme: colorMap.get("creme") || "#F6F1EB",
    dourado: colorMap.get("dourado") || "#C4975A",
  },
  fonts: {
    display: displayMatch ? displayMatch[1].trim() : "Instrument Serif",
    body: bodyMatch ? bodyMatch[1].trim() : "DM Sans",
  },
};

/** Convert a path relative to manifestDir into a staticFile path */
function toStaticPath(relativePath) {
  if (prefix) return `/${prefix}/${relativePath}`;
  return `/${relativePath}`;
}

// Resolve all asset paths as staticFile paths
for (const scene of manifest.scenes) {
  for (const beat of scene.beats) {
    beat.keyframes = beat.keyframes.map((kf) => toStaticPath(kf));
    if (beat.audio_file) beat.audio_file = toStaticPath(beat.audio_file);
    if (beat.clip_file) beat.clip_file = toStaticPath(beat.clip_file);
  }
}
for (const sfx of manifest.sfx || []) {
  if (sfx.file) sfx.file = toStaticPath(sfx.file);
}

// Build timeline
const fps = manifest.settings.fps;
const timeline = [];
let currentFrame = 0;
for (const scene of manifest.scenes) {
  for (const beat of scene.beats) {
    const durationInFrames = Math.round(beat.duration_s * fps);
    timeline.push({ beatId: beat.id, startFrame: currentFrame, durationInFrames });
    currentFrame += durationInFrames;
  }
}

const props = { manifest, branding, timeline };
console.log(JSON.stringify(props));
