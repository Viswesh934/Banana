from typing import Optional
import tiktoken


class TokenCounter:
    """Token counter using tiktoken with fallback estimation."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        self.encoding_name = encoding_name
        self._encoding: Optional[tiktoken.Encoding] = None

    @property
    def encoding(self) -> tiktoken.Encoding:
        if self._encoding is None:
            try:
                self._encoding = tiktoken.get_encoding(self.encoding_name)
            except Exception:
                # Fallback to cl100k_base or p50k_base if available
                self._encoding = tiktoken.encoding_for_model("gpt-4o")
        return self._encoding

    def count(self, text: str) -> int:
        """Count tokens in text string."""
        if not text:
            return 0
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback heuristic: 1 token ~= 4 characters for English text
            return max(1, len(text) // 4)


_default_token_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """Return default singleton TokenCounter instance."""
    global _default_token_counter
    if _default_token_counter is None:
        _default_token_counter = TokenCounter()
    return _default_token_counter


def count_tokens(text: str) -> int:
    """Convenience function to count tokens in text."""
    return get_token_counter().count(text)
