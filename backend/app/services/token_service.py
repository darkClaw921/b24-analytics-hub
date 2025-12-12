"""
Token counting service using tiktoken
"""
import tiktoken
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TokenService:
    """Service for counting tokens in text using tiktoken"""
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize token service
        
        Args:
            model: Model name for tiktoken encoding (default: gpt-4)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            logger.warning(f"Model {model} not found in tiktoken, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count tokens
        
        Returns:
            Number of tokens
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return 0
    
    def count_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count tokens in chat messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Total number of tokens
        """
        total_tokens = 0
        
        for message in messages:
            # Count tokens in message content
            content = message.get("content", "")
            total_tokens += self.count_tokens(content)
            
            # Add overhead for message formatting (role, etc)
            # OpenAI adds ~4 tokens per message for formatting
            total_tokens += 4
            
            # Add tokens for tool calls if present
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    if "function" in tool_call:
                        function_name = tool_call["function"].get("name", "")
                        function_args = tool_call["function"].get("arguments", "")
                        total_tokens += self.count_tokens(function_name)
                        total_tokens += self.count_tokens(function_args)
        
        # Add overhead for conversation formatting
        total_tokens += 3
        
        return total_tokens


# Global instance
token_service = TokenService()

