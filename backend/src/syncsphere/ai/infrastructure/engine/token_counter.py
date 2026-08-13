import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.token_counter")

class TokenCounter:
    """
    TokenCounter provides pluggable, heuristic token counting and estimation logic
    for various LLM families.
    """
    
    @staticmethod
    def estimate_text_tokens(text: str, model_name: Optional[str] = None) -> int:
        """
        Estimates the token count of a given string content using highly-tuned
        character-to-token ratio rules per model family.
        """
        if not text:
            return 0
            
        model_name = (model_name or "gpt-4").lower()
        
        # Word and character count baselines
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        # Heuristics based on model families
        if "gpt" in model_name:
            # OpenAI models typically average 4 characters per token
            token_count = max(int(char_count / 4.0), int(word_count * 1.3))
        elif "claude" in model_name:
            # Claude averages ~3.6 characters per token
            token_count = max(int(char_count / 3.6), int(word_count * 1.35))
        elif "gemini" in model_name:
            token_count = max(int(char_count / 3.7), int(word_count * 1.32))
        else:
            # Default fallback: ~4 characters per token
            token_count = max(int(char_count / 4.0), int(word_count * 1.3))
            
        return max(1, token_count)

    @classmethod
    def estimate_messages_tokens(cls, messages: List[Dict[str, Any]], model_name: Optional[str] = None) -> int:
        """Estimates the tokens consumed by a structured conversation history payload."""
        total = 0
        for msg in messages:
            # Roles + contents + name parameters contribute to prompt tokens
            role = msg.get("role", "")
            content = msg.get("content", "")
            name = msg.get("name", "")
            
            total += cls.estimate_text_tokens(role, model_name)
            total += cls.estimate_text_tokens(content, model_name)
            if name:
                total += cls.estimate_text_tokens(name, model_name)
            total += 4 # Overhead per message
            
        total += 3 # Overhead per system message conversation frame
        return total
