## Calendar Endpoints

### Overview

This API interacts with the CSH Google calendar to pull the number of events set in the .env file to display in the calendar widget on Jumpstart

---

### Authentication

The API we are using does not require authenication. It just needs the Public URL of the calendar. This can be any calendar for testing purposes.

---

### Error Handling

- All endpoints return JSON responses.
- On error, the response will include an `error` field and an appropriate HTTP status code (e.g., 400, 404, 500, 503).

Example error response:
```json
{
  "error": "Failed to fetch the Calendar!"
}
```

### Endpoint Overview
::: api.endpoints.get_calendar