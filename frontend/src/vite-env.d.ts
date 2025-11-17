/// <reference types="vite/client" />
/// <reference types="vitest/globals" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_API_PREFIX?: string
  readonly VITE_WS_URL?: string
  // add more env vars as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
