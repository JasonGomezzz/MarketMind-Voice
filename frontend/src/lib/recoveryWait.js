export function createRecoveryWait(email, seconds, startedAt = Date.now()) {
  const duration = Number(seconds)
  return {
    email: email.trim().toLowerCase(),
    startedAt,
    until: startedAt + (Number.isFinite(duration) && duration > 0 ? duration : 60) * 1000,
  }
}
