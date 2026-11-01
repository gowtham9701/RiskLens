# Generated reports

Portfolio reports (Excel/PDF) are generated on demand by the backend
(`backend/app/services/reporting_service.py`) and streamed to the client via
`GET /reports/portfolio/{id}?format=xlsx|pdf`. This directory is a placeholder
for any persisted report output; it is git-ignored by default.
