"""Memory management for conversations."""

from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback for local testing

    class _FallbackEncoding:
        def encode(self, text: str) -> list[int]:
            return list(text.encode("utf-8"))

    class _TiktokenFallback:
        @staticmethod
        def get_encoding(_: str) -> _FallbackEncoding:
            return _FallbackEncoding()

    tiktoken = _TiktokenFallback()  # type: ignore[assignment]

logger = structlog.get_logger()


class ConversationMemory:
    """Manages conversation memory with sliding window and summarization."""

    def __init__(self, max_token_limit: int = 4000):
        """Initialize conversation memory.

        Args:
            max_token_limit: Maximum tokens to maintain in memory
        """
        self.max_token_limit = max_token_limit
        self.messages: List[Dict[str, str]] = []
        self.summary: str = ""
        self.key_points: List[str] = []

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:  # Fall back when the preferred encoding is unavailable
            logger.debug("Falling back to gpt2 tokenizer for conversation memory")
            self.tokenizer = tiktoken.get_encoding("gpt2")

    def add_message(self, role: str, content: str) -> None:
        """Add a message to memory.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        # Manage memory size
        self._manage_memory()

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM.

        Returns:
            List of message dictionaries
        """
        # Start with summary if available
        messages: List[Dict[str, str]] = []

        if self.summary:
            messages.append(
                {"role": "system", "content": f"Previous conversation summary: {self.summary}"}
            )

        # Add recent messages
        for msg in self.messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        return messages

    def get_context(self) -> str:
        """Get conversation context as a string.

        Returns:
            Context string
        """
        context_parts: List[str] = []

        if self.summary:
            context_parts.append(f"Summary: {self.summary}")

        if self.key_points:
            context_parts.append(f"Key points: {', '.join(self.key_points)}")

        return "\n".join(context_parts)

    def get_summary(self) -> str:
        """Get conversation summary.

        Returns:
            Summary string
        """
        return self.summary

    def _manage_memory(self) -> None:
        """Manage memory size using sliding window and summarization."""
        total_tokens = self._count_total_tokens()

        if total_tokens > self.max_token_limit:
            # Keep only recent messages
            messages_to_keep = len(self.messages) // 2

            # Summarize older messages
            older_messages = self.messages[:messages_to_keep]
            self.summary = self._create_summary(older_messages)

            # Extract key points
            self._extract_key_points(older_messages)

            # Keep recent messages
            self.messages = self.messages[messages_to_keep:]

    def _count_total_tokens(self) -> int:
        """Count total tokens in memory.

        Returns:
            Total token count
        """
        total = 0

        # Count summary tokens
        if self.summary:
            total += len(self.tokenizer.encode(self.summary))

        # Count message tokens
        for msg in self.messages:
            total += len(self.tokenizer.encode(msg["content"]))

        return total

    def _create_summary(self, messages: List[Dict[str, str]]) -> str:
        """Create a summary of messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary string
        """
        # Simple summarization for now
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]

        assistant_messages = [msg["content"] for msg in messages if msg["role"] == "assistant"]

        summary_parts: List[str] = []

        if user_messages:
            summary_parts.append(f"User discussed: {self._extract_topics(user_messages)}")

        if assistant_messages:
            summary_parts.append(f"Coach explored: {self._extract_topics(assistant_messages)}")

        return " ".join(summary_parts)

    def _extract_topics(self, messages: List[str]) -> str:
        """Extract main topics from messages.

        Args:
            messages: List of message contents

        Returns:
            Comma-separated topics
        """
        # Simple keyword extraction
        keywords: List[str] = []

        # Common coaching keywords to look for
        topic_words = [
            "values",
            "purpose",
            "goals",
            "vision",
            "motivation",
            "passion",
            "fulfillment",
            "success",
            "growth",
            "challenge",
            "relationship",
            "career",
            "family",
            "health",
            "wealth",
        ]

        combined_text = " ".join(messages).lower()

        for word in topic_words:
            if word in combined_text:
                keywords.append(word)

        return ", ".join(keywords[:5]) if keywords else "various topics"

    def _extract_key_points(self, messages: List[Dict[str, str]]) -> None:
        """Extract key points from messages.

        Args:
            messages: Messages to analyze
        """
        self.key_points = []

        # Look for statements with strong indicators
        indicators = [
            "important",
            "key",
            "main",
            "core",
            "fundamental",
            "essential",
            "critical",
            "significant",
            "valuable",
        ]

        for msg in messages:
            content_lower = msg["content"].lower()
            for indicator in indicators:
                if indicator in content_lower:
                    # Extract the sentence
                    sentences = msg["content"].split(".")
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            self.key_points.append(sentence.strip()[:100])
                            break

        # Keep only unique key points
        self.key_points = list(set(self.key_points[:5]))

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "messages": self.messages,
            "summary": self.summary,
            "key_points": self.key_points,
            "max_token_limit": self.max_token_limit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """Create memory from dictionary.

        Args:
            data: Dictionary data

        Returns:
            ConversationMemory instance
        """
        memory = cls(max_token_limit=data.get("max_token_limit", 4000))
        memory.messages = data.get("messages", [])
        memory.summary = data.get("summary", "")
        memory.key_points = data.get("key_points", [])
        return memory
