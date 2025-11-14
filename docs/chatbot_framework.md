# PublicBridge Advanced Chatbot Framework

## Project Analysis
- Objectives: assist citizens with reporting issues, tracking reports, and accessing county services in Kenya.
- Workflows: chat modal in `templates/dashboard/base.html` calls `reports/api/ai/chatbot/` with `conversation_history`.
- Integration: orchestrator coordinates agents in `ai_agents/`, endpoints in `reports/ai_api_views.py`.

## Enhancement Strategy
- Context-aware conversation: centralized `ContextManager` merges user/session data and history.
- NLP capabilities: `NLPEngine` for intent detection and entity extraction, Kenya-specific vocabulary.
- Workflow integration: orchestrator routes intents to actions and produces guidance aligned with report/track flows.
- Progressive enhancement: pluggable agents with advanced vs fallback initialization.

## Implementation Components
- `ai_agents/conversation.py`: `ContextManager` builds bounded conversation context.
- `ai_agents/nlp.py`: `NLPEngine` intent detection and basic entity extraction.
- `ai_agents/analytics_tracker.py`: lightweight chat analytics with snapshots.
- `ai_agents/orchestrator.py`: sync wrapper, analytics, context integration, chatbot fallback support.
- `ai_agents/civic_chatbot.py`: uses `NLPEngine` for intent detection.
- `reports/ai_api_views.py`: fixes async handling and capability flag.

## Analytics
- Metrics: total interactions, errors, average confidence, average response length.
- Access: via orchestrator `chat_analytics.snapshot()` for future dashboards.

## Quality Assurance
- Functional: `reports/tests/test_chatbot_api.py` validates chatbot endpoint shape.
- Performance: orchestrator tracks processing time; extend with timing decorators as needed.
- UX: chat modal remains responsive and accessible; progressive responses for Kenya context.

## Evolution
- Replace `NLPEngine` with ML model, extend `ContextManager` to persistent storage, export analytics to admin dashboards.
