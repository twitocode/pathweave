/**
 * FastAPI backend origin used for auth redirects.
 * Set NEXT_PUBLIC_API_ORIGIN in `.env.local` if API is not on localhost:8000.
 */
export function getApiOrigin(): string {
  const raw =
    typeof process.env.NEXT_PUBLIC_API_ORIGIN === "string"
      ? process.env.NEXT_PUBLIC_API_ORIGIN.trim()
      : "";
  return raw.length > 0 ? raw.replace(/\/$/, "") : "http://localhost:8000";
}

export function getAuthLoginHref(): string {
  return `${getApiOrigin()}/auth/login`;
}
