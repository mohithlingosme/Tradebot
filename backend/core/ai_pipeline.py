"""
AI prompt processing pipeline for Finbot
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .safety import SafetyContext, SafetyFilter, SafetyResult
from ai.agents import NarrativeAI, ResearchAI, SignalAI

logger = logging.getLogger(__name__)

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. AI features will be limited.")


class PromptRequest(BaseModel):
    """Request model for AI prompts."""

    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7
    use_finetuned_model: bool = False


class PromptResponse(BaseModel):
    """Response model for AI prompts."""

    response: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    disclaimer: Optional[str] = None
    safety_findings: List[Dict[str, str]] = Field(default_factory=list)
    blocked: bool = False
    confidence: Optional[float] = None


@dataclass
class KnowledgeDocument:
    """Domain knowledge used for embeddings and similarity search."""

    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingService:
    """Simple TF-IDF embedding index for semantic search."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.documents: List[KnowledgeDocument] = []
        self._matrix = None
        self._dirty = True

    def add_document(self, document: KnowledgeDocument):
        self.documents.append(document)
        self._dirty = True

    def _ensure_index(self):
        if not self.documents:
            return
        if self._dirty:
            texts = [doc.content for doc in self.documents]
            self._matrix = self.vectorizer.fit_transform(texts)
            self._dirty = False

    def search(self, query: str, top_k: int = 3) -> List[Tuple[KnowledgeDocument, float]]:
        if not self.documents:
            return []
        self._ensure_index()
        if self._matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        results: List[Tuple[KnowledgeDocument, float]] = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            results.append((self.documents[idx], float(scores[idx])))
        return results


class PortfolioOptimizer:
    """Basic mean-variance style allocator for demo purposes."""

    def optimize(self, holdings: List[Dict[str, Any]], risk_profile: str) -> Dict[str, Any]:
        if not holdings:
            raise ValueError("No holdings provided")

        weights = np.array([h.get("weight", 1.0) for h in holdings], dtype=float)
        weights = weights / weights.sum()
        volatility = np.array([h.get("volatility", 0.2) for h in holdings], dtype=float)
        returns = np.array([h.get("expected_return", 0.08) for h in holdings], dtype=float)

        risk_scalar = {"conservative": 0.8, "moderate": 1.0, "aggressive": 1.2}.get(risk_profile, 1.0)
        target_returns = returns * risk_scalar
        adjusted_weights = target_returns / (volatility + 1e-6)
        adjusted_weights = adjusted_weights / adjusted_weights.sum()

        allocation = []
        for holding, weight in zip(holdings, adjusted_weights):
            allocation.append(
                {
                    "symbol": holding.get("symbol"),
                    "current_weight": round(float(weight), 4),
                    "target_weight": round(float(weight), 4),
                    "notes": f"Increase exposure" if weight > holding.get("weight", 0) else "Trim allocation",
                }
            )
        portfolio_return = float(np.dot(adjusted_weights, target_returns))
        portfolio_vol = float(np.sqrt(np.dot(adjusted_weights ** 2, volatility ** 2)))
        return {
            "allocations": allocation,
            "expected_return": round(portfolio_return, 4),
            "expected_volatility": round(portfolio_vol, 4),
            "risk_profile": risk_profile,
        }


class AIPipeline:
    """AI prompt processing pipeline (advisory-only, never executes trades)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize AI pipeline.

        Args:
            api_key: OpenAI API key (or from env)
            model: Model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.finetuned_model = os.getenv("OPENAI_FINETUNED_MODEL")
        self.client = None
        self.embedding_service = EmbeddingService()
        self.optimizer = PortfolioOptimizer()
        self.safety_filter = SafetyFilter()
        self._load_knowledge_base()
        self.advisory_only = True

        if OPENAI_AVAILABLE and self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info("AI pipeline initialized with OpenAI")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        else:
            logger.warning("AI pipeline initialized in mock mode (no OpenAI API key)")

        # Compose role-specific agents to keep LLM responsibilities isolated.
        self.research_ai = ResearchAI(self.run_prompt)
        self.narrative_ai = NarrativeAI(self.research_ai, self.run_prompt)
        self.signal_ai = SignalAI(self.run_prompt)

    def _build_safety_context(self, request: PromptRequest) -> SafetyContext:
        """Translate PromptRequest context into a SafetyContext."""
        data = request.context or {}
        intent = str(data.get("data_type") or data.get("intent") or "general")
        format_hint = str(data.get("format", "")).lower()
        expect_json = bool(data.get("expect_json")) or format_hint == "json"
        confidence = (
            data.get("confidence")
            or data.get("confidence_score")
            or data.get("probability")
        )
        metadata = dict(data)
        return SafetyContext(intent=intent, confidence=confidence, expect_json=expect_json, metadata=metadata)

    def _apply_safety_filters(self, raw_text: str, request: PromptRequest) -> SafetyResult:
        """Run the safety filter for the given prompt/response."""
        context = self._build_safety_context(request)
        return self.safety_filter.evaluate(raw_text, context)

    def _serialize_findings(self, findings: List) -> List[Dict[str, str]]:
        """Convert safety findings into serializable dicts."""
        serialized: List[Dict[str, str]] = []
        for finding in findings:
            if hasattr(finding, "to_dict"):
                serialized.append(finding.to_dict())
            elif isinstance(finding, dict):
                serialized.append(finding)
        return serialized

    def run_prompt(
        self,
        *,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 400,
        temperature: float = 0.4,
        use_finetuned_model: bool = True,
        expect_json: bool = False,
    ) -> PromptResponse:
        """
        Helper for downstream agents to invoke the LLM with safety metadata.
        """
        ctx = dict(context or {})
        if expect_json:
            ctx.setdefault("format", "json")
            ctx["expect_json"] = True
        request = PromptRequest(
            prompt=prompt,
            context=ctx or None,
            max_tokens=max_tokens,
            temperature=temperature,
            use_finetuned_model=use_finetuned_model,
        )
        return self.process_prompt(request)

    def process_prompt(self, request: PromptRequest) -> PromptResponse:
        """
        Process an AI prompt.

        Args:
            request: Prompt request

        Returns:
            Prompt response
        """
        selected_model = self.finetuned_model if request.use_finetuned_model and self.finetuned_model else self.model

        if not self.client:
            # Mock response for development while still applying safety metadata
            mock_text = "AI features require OpenAI API key. Please configure OPENAI_API_KEY environment variable."
            safety_result = self._apply_safety_filters(mock_text, request)
            return PromptResponse(
                response=safety_result.text,
                model="mock",
                disclaimer=safety_result.disclaimer,
                safety_findings=self._serialize_findings(safety_result.findings),
                blocked=safety_result.blocked,
                confidence=safety_result.confidence,
            )

        try:
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a financial trading assistant. Provide helpful, accurate, and safe financial advice.",
                }
            ]

            # Add context if provided
            if request.context:
                context_str = "\n".join([f"{k}: {v}" for k, v in request.context.items()])
                messages.append({"role": "user", "content": f"Context: {context_str}\n\n{request.prompt}"})
            else:
                messages.append({"role": "user", "content": request.prompt})

            # Make API call
            response = self.client.ChatCompletion.create(
                model=selected_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            raw_text = response.choices[0].message.content
            safety_result = self._apply_safety_filters(raw_text, request)
            return PromptResponse(
                response=safety_result.text,
                tokens_used=response.usage.total_tokens,
                model=selected_model,
                disclaimer=safety_result.disclaimer,
                safety_findings=self._serialize_findings(safety_result.findings),
                blocked=safety_result.blocked,
                confidence=safety_result.confidence,
            )

        except Exception as e:
            logger.error(f"Error processing AI prompt: {e}")
            return PromptResponse(
                response=f"Error processing request: {str(e)}",
                model=self.model
            )

    def analyze_market_signal(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and provide trading signal.

        Args:
            symbol: Stock symbol
            market_data: Market data dictionary

        Returns:
            Advisory-only analysis payload
        """
        horizon = str(market_data.get("horizon") or "intraday")
        if horizon not in {"intraday", "swing"}:
            horizon = "intraday"
        research_summary = self.research_ai.summarize_news(
            [symbol],
            articles=market_data.get("news"),
        )
        sentiment_summary = self.research_ai.summarize_sentiment(
            [symbol],
            sentiment_samples=market_data.get("sentiment"),
        )
        narrative = self.narrative_ai.symbol_narrative(
            symbol,
            horizon=horizon,
            research_summary=research_summary,
            sentiment_summary=sentiment_summary,
            market_data=market_data,
        )
        signal_payload = self.signal_ai.generate_signal(
            symbol=symbol,
            horizon=horizon,
            research_summary=research_summary,
            narrative=narrative,
            market_snapshot=market_data,
        )
        llm_signal = signal_payload["signal"]
        meta = signal_payload["meta"]

        return {
            "symbol": symbol,
            "analysis": narrative,
            "research_summary": research_summary,
            "sentiment_summary": sentiment_summary,
            "signal": llm_signal.model_dump(),
            "advisory_only": True,
            "disclaimer": meta.get("disclaimer"),
            "safety_findings": meta.get("safety_findings"),
            "blocked": meta.get("blocked"),
            "raw_signal_text": meta.get("raw_text"),
            "confidence": getattr(llm_signal, "confidence", None),
        }

    def get_portfolio_advice(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get portfolio optimization advice.

        Args:
            portfolio_data: Portfolio data dictionary

        Returns:
            Advice text
        """
        prompt = f"""
        Analyze the following portfolio and provide optimization advice:
        
        Portfolio: {portfolio_data}
        
        Provide:
        1. Risk assessment
        2. Diversification analysis
        3. Recommendations for improvement
        """
        
        request = PromptRequest(
            prompt=prompt,
            context={"data_type": "portfolio_analysis"},
            max_tokens=400,
            temperature=0.6,
            use_finetuned_model=True,
        )
        
        response = self.process_prompt(request)
        return {
            "advice": response.response,
            "disclaimer": response.disclaimer,
            "safety_findings": response.safety_findings,
            "blocked": response.blocked,
            "confidence": response.confidence,
            "advisory_only": True,
        }

    def generate_research_brief(self, topic: str, focus: Optional[List[str]] = None) -> Dict[str, Any]:
        """Produce a multi-section research brief using embeddings as context."""
        context_docs = self.embedding_service.search(topic, top_k=3)
        context_text = "\n\n".join(
            [f"{doc.title}: {doc.content}" for doc, _ in context_docs]
        ) or "No prior knowledge found."
        focus_items = ", ".join(focus or ["valuation", "growth catalysts", "risks"])
        prompt = f"""
        Using the following knowledge base and latest market understanding produce
        a financial research brief about "{topic}".

        Context:
        {context_text}

        The brief must include sections for Overview, Fundamentals, Catalysts, and Risks.
        Emphasize {focus_items}. Return JSON with keys overview, fundamentals, catalysts, risks.
        """
        request = PromptRequest(
            prompt=prompt,
            max_tokens=500,
            temperature=0.4,
            use_finetuned_model=True,
            context={
                "data_type": "research_brief",
                "format": "json",
                "topic": topic,
                "requires_disclaimer": True,
            },
        )
        response = self.process_prompt(request)
        payload: Dict[str, Any] = {
            "disclaimer": response.disclaimer,
            "safety_findings": response.safety_findings,
            "blocked": response.blocked,
            "confidence": response.confidence,
        }
        if response.blocked:
            payload["brief"] = {}
            payload["message"] = response.response
            return payload
        try:
            payload["brief"] = json.loads(response.response)
        except Exception:
            payload["brief"] = {"overview": response.response}
        return payload

    def generate_trading_plan(self, symbol: str, risk_profile: str, account_size: float) -> Dict[str, Any]:
        """Create a structured trading plan for a given symbol."""
        prompt = f"""
        Design a trading plan for {symbol} with risk profile "{risk_profile}" and account size ${account_size:,.2f}.
        Include entry criteria, sizing, stop-loss, take-profit, and risk notes in JSON.
        This output is advisory only and must not include broker or execution commands.
        """
        request = PromptRequest(
            prompt=prompt,
            max_tokens=350,
            temperature=0.45,
            use_finetuned_model=True,
            context={
                "data_type": "trading_plan",
                "format": "json",
                "symbol": symbol,
                "risk_profile": risk_profile,
                "requires_disclaimer": True,
            },
        )
        response = self.process_prompt(request)
        payload: Dict[str, Any] = {
            "disclaimer": response.disclaimer,
            "safety_findings": response.safety_findings,
            "blocked": response.blocked,
            "confidence": response.confidence,
            "advisory_only": True,
        }
        if response.blocked:
            payload["plan"] = {}
            payload["message"] = response.response
            return payload
        try:
            payload["plan"] = json.loads(response.response)
        except Exception:
            payload["plan"] = response.response
        return payload

    def optimize_portfolio(self, holdings: List[Dict[str, Any]], risk_profile: str) -> Dict[str, Any]:
        """Return optimized weights plus AI commentary."""
        optimization = self.optimizer.optimize(holdings, risk_profile)
        prompt = f"""
        Provide commentary for the following optimized portfolio: {optimization}.
        Highlight risk drivers and rebalancing suggestions.
        """
        request = PromptRequest(
            prompt=prompt,
            max_tokens=250,
            temperature=0.5,
            use_finetuned_model=True,
            context={
                "data_type": "portfolio_optimizer",
                "requires_disclaimer": True,
            },
        )
        response = self.process_prompt(request)
        optimization["commentary"] = response.response
        optimization["disclaimer"] = response.disclaimer
        optimization["safety_findings"] = response.safety_findings
        optimization["blocked"] = response.blocked
        optimization["confidence"] = response.confidence
        optimization["advisory_only"] = True
        return optimization

    def analyze_company_decision(self, company: str, question: str) -> Dict[str, Any]:
        """Use similarity search to find related historical decisions."""
        query = f"{company} {question}"
        matches = self.embedding_service.search(query, top_k=5)
        context = "\n\n".join([f"{doc.title}: {doc.content}" for doc, _ in matches])
        prompt = f"""
        You are analyzing historical corporate decisions. Question: {question} for {company}.
        Reference the snippets below when formulating your answer.

        {context}

        Respond with JSON: {{"analysis": "...", "historical_refs": ["..."]}}
        """
        request = PromptRequest(
            prompt=prompt,
            max_tokens=400,
            temperature=0.45,
            use_finetuned_model=True,
            context={
                "data_type": "decision_analysis",
                "format": "json",
                "company": company,
                "requires_disclaimer": True,
            },
        )
        response = self.process_prompt(request)
        try:
            parsed = json.loads(response.response)
        except Exception:
            parsed = {"analysis": response.response, "historical_refs": []}
        parsed["matches"] = [
            {"title": doc.title, "score": score, "tags": doc.tags} for doc, score in matches
        ]
        parsed["disclaimer"] = response.disclaimer
        parsed["safety_findings"] = response.safety_findings
        parsed["blocked"] = response.blocked
        parsed["confidence"] = response.confidence
        return parsed

    def _load_knowledge_base(self):
        """Load canned knowledge docs for embeddings."""
        data_dir = Path(__file__).parent / "data"
        kb_file = data_dir / "company_decisions.json"
        if not kb_file.exists():
            return
        try:
            with open(kb_file, "r", encoding="utf-8") as handle:
                entries = json.load(handle)
            for entry in entries:
                document = KnowledgeDocument(
                    title=f"{entry.get('company')} - {entry.get('title')}",
                    content=entry.get("summary", ""),
                    tags=entry.get("tags", []),
                    metadata={"year": entry.get("year"), "company": entry.get("company")},
                )
                self.embedding_service.add_document(document)
        except Exception as exc:
            logger.error("Failed to load knowledge base: %s", exc)


# Global AI pipeline instance
ai_pipeline = AIPipeline()

