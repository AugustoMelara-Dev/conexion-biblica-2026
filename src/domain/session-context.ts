import type { AttemptContext, SessionMode } from "@/domain/types"

export function sessionContextForMode(mode: SessionMode): AttemptContext {
  return mode === "simulation" || mode === "final" || mode === "speed" || mode === "championship"
    ? "simulation"
    : "practice"
}

export function showsImmediateFeedback(mode: SessionMode) {
  return mode === "learn" || mode === "smart-review" || mode === "training"
}
