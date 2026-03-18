## Endpoints

### Overview

This API provides endpoints for securely storing, retrieving, and deleting Snyk credentials using OpenBao (Vault) and Redis as backends.
All endpoints are versioned under `/credentials` and `/cache`.

---

### Authentication

This API does **not** implement authentication by default.
If you deploy in production, you should secure the API (e.g., with a reverse proxy, network policy, or FastAPI dependencies).

---

### Error Handling

- All endpoints return JSON responses.
- On error, the response will include an `error` field and an appropriate HTTP status code (e.g., 400, 404, 500, 503).

Example error response:
```json
{
  "error": "Vault is sealed, cannot store credentials."
}
```

### Endpoint Overview
::: api.endpoints