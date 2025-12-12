from typing import Any, Dict


def mock_llm_runner(prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """
    A mock LLM runner that returns a dummy response.
    """
    return {
        "response": f"This is a mock response for the prompt: {prompt}",
    }
