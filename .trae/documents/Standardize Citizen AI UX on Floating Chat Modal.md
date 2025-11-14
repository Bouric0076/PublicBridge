## Current Usage Findings
- Floating AI button and chat modal exist globally in `templates/dashboard/base.html` with `toggleAIChat` and `sendAIMessage`.
- Admin-focused AI page (`templates/admin_dashboard/ai_chatbot.html`) is mapped via `dashboard/urls.py:37` for `ai_chatbot_interface`.
- Citizen AI routes exist: `citizen_ai_dashboard` and `ai_recommendations` in `dashboard/urls.py:41-42`.

## Decision
- Use the floating AI chat icon + modal as the unified, primary citizen UX.
- Keep the AI page only for admin workflows and advanced analytics.
- Provide a secondary citizen page for recommendations (`ai_recommendations`) with a sidebar link.

## Implementation Steps
1. Global Chat Availability
- Ensure the floating button and modal render on all citizen dashboard pages via `dashboard/base.html`.
- Remove duplicated `toggleAIChat`/`sendAIMessage` blocks and consolidate into one script.
- Confirm endpoint uses `'/dashboard/chatbot-api/'` with CSRF and `IsAuthenticated`.

2. Navigation & Visibility
- Sidebar: keep "AI Recommendations" linking to `ai_recommendations`.
- Hide or restrict `ai_chatbot_interface` page from citizens (admin-only).
- Add keyboard shortcut (`Ctrl+/`) and visible affordances.

3. Accessibility
- Add ARIA roles (`dialog`, `aria-modal="true"`, labeled inputs/buttons).
- Focus management on open/close; trap focus within modal; escape to close.
- High-contrast states and screen-reader-friendly messages.

4. Performance
- Debounce input; optional streaming responses (chunked updates).
- Persist light conversation history (localStorage) with size limits.
- Graceful error states; backoff/retry for transient failures.

5. Security & Permissions
- Keep `IsAuthenticated` on chatbot API; no `IsAdminUser` for citizen chat.
- Enforce CSRF, server-side validation, rate limiting.

## Verification
- Test as a normal logged-in user: button visibility, modal open, send/receive chat.
- Mobile: bottom-right positioning, safe-area checks, touch targets.
- Screen reader: keyboard-only flow and ARIA announcements.

## Rollout
- Feature flag the modal enhancements; enable progressively.
- Capture feedback (thumbs up/down) and basic analytics to iterate.

Please confirm this plan. Once approved, I will implement the consolidation, accessibility upgrades, and navigation changes to standardize on the floating chat modal for citizens.