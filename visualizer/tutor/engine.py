from .llm_adapter import get_llm_adapter
from .prompts import TutorPrompts

class TutorEngine:
    def __init__(self):
        self.llm = get_llm_adapter()

    def handle_chat(self, user_message: str, context: dict) -> str:
        """
        Handle a one-off chat request.
        """
        code = context.get("code", "")
        line = context.get("line", 0)
        locals_dict = context.get("locals", {})
        
        user_prompt = TutorPrompts.build_context_prompt(code, line, locals_dict) + user_message
        return self.llm.generate(TutorPrompts.SYSTEM_TUTOR, user_prompt)
        
    def stream_chat(self, user_message: str, context: dict):
        """
        Stream a chat response.
        """
        code = context.get("code", "")
        line = context.get("line", 0)
        locals_dict = context.get("locals", {})
        
        user_prompt = TutorPrompts.build_context_prompt(code, line, locals_dict) + user_message
        return self.llm.generate_stream(TutorPrompts.SYSTEM_TUTOR, user_prompt)
