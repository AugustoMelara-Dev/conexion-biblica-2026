export function formatElapsedMs(milliseconds: number): string {
  const totalSeconds = Math.max(0, milliseconds) / 1000
  if (totalSeconds < 60) return `${totalSeconds.toFixed(1)} s`
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, "0")
  return `${minutes}:${seconds}`
}

export function getRemainingSeconds(deadline: number, now: number) {
  return Math.max(0, Math.ceil((deadline - now) / 1000))
}
