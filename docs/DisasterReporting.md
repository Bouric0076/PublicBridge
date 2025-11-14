# PublicBridge – Live Disaster Reporting (Kenya)

## Overview
PublicBridge’s live disaster reporting enables citizens to geotag emergencies (fires, floods, crimes, medical) and submit rich reports in real time. The system integrates an interactive map, multimedia uploads, optional anonymity, automated dispatch to the nearest agency, and status updates.

## Key Features
- Real-time map with live markers for new reports
- Visual indicators by emergency type and severity (low/medium/high/critical)
- Multimedia attachments (images/videos) with client-side image compression
- Optional anonymous submission; identified users see tracking and status
- Automated routing to nearest relevant agency; live status broadcasts
- Low-bandwidth optimizations for mobile devices common in Kenya

## How It Works
1. Citizens open the report page and select an incident location on the map.
2. They choose a category and severity, add a description and attachments.
3. On submit, the system generates a tracking code (e.g., `KE-20251114-ABC123`).
4. The report is dispatched to the nearest active agency and shown live on the map.
5. Status updates (e.g., `in_progress`, `resolved`) are broadcast to connected clients.

## Screenshots
> Replace placeholders with actual screenshots
- Map with category-specific icons – `screenshots/map_overview.png`
- Report form with severity and anonymity – `screenshots/report_form.png`
- Success modal with tracking code – `screenshots/success_modal.png`

## Submission Workflow
1. Geotagging: Select location on the map or use current location.
2. Details: Pick category, set severity, describe incident, add media.
3. Identity: Check “Submit anonymously” if preferred.
4. Submit: The system validates media, compresses images, and posts to `/api/reports/`.
5. Confirmation: A tracking code is returned; status updates stream via WebSocket.

## Response Workflow
1. Routing: The report is assigned to the nearest relevant agency automatically.
2. Updates: Agencies update status (`pending` → `in_progress` → `resolved`), broadcast to clients.
3. Communication: Optional two-way messaging can be enabled via WebSocket to share clarifications.

## Usage Guidelines
### Citizens
- Provide precise location and clear description.
- Add photos/videos when safe and possible; ensure files are under size limits.
- Use anonymity if needed; tracking still works without revealing identity.

### Responders
- Monitor the live map and assigned queue.
- Update report status promptly; the system informs citizens in real time.
- Attach notes or additional evidence when appropriate.

## Kenyan Considerations
- Map defaults to Nairobi region; supports all Kenyan counties.
- Works well on low-bandwidth mobile connections (image compression, minimal payloads).
- Dispatch respects local emergency services (fire, medical, police, infrastructure).

## Technical Notes
- Frontend: Leaflet map; WebSocket feed at `/ws/reports/`; AJAX POST to `/api/reports/`.
- Backend: Django + DRF; Channels for WebSockets; models support severity, anonymity, tracking, and media.
- Security: CSRF protected POST; media type validation; duplicate/spam detection.

## Maintenance
- Keep agency locations updated.
- Review duplicate detection thresholds per locality.
- Periodically refresh tiles and libraries to ensure performance and compatibility.

