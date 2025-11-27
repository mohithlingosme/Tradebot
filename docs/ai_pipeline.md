# AI Pipeline

Finbot uses an AI pipeline to generate research briefs, trading plans, portfolio suggestions, and free-form responses. All AI outputs are advisory-only and wrapped with disclaimers.

Diagram: [ai_pipeline.mmd](./diagrams/ai_pipeline.mmd)

## Flow
1) **Inputs**: User prompts (frontend), optional context (portfolio/market state), and system settings (`FINBOT_MODE`, `APP_USE_CASE`).
2) **Prompt build**: `backend/api/ai.py` and `ai_models/` construct prompts and route to helpers in `backend/core/ai_pipeline.py`.
3) **Model call**: LLM or model host executes the prompt; errors surface as JSON with disclaimers.
4) **Post-processing**: Responses are parsed/normalized (plans, recommendations, analyses) and wrapped with:
   - `disclaimer`, `mode`, `regulatory_flags`, `app_use_case`
   - Strategy/risk metadata when relevant
5) **Delivery**: Backend returns REST responses; frontend renders outputs with on-page disclaimers (e.g., AI assistant UI).

## Code landmarks
- API surface: `backend/api/ai.py` (analyze-market, portfolio-advice, trading-assistant, ai-advice, recommendations, prompt).
- Pipeline helpers: `backend/core/ai_pipeline.py`, `ai_models/` for model orchestration.
- Frontend consumption: `frontend/src/pages/AIAssistant.tsx` (with visible disclaimers).
- Guardrails: responses always include disclaimer + mode metadata; live trading never auto-executes AI outputs.
