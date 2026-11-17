API modules should use the shared `client.js` instance. The base URL comes from
`VITE_API_BASE_URL`; configure the FastAPI CORS allowlist for the Vite origin
before making browser requests. Keep feature endpoint paths aligned with the
backend routes under `/api/v1`.
