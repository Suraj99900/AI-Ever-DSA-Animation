from .llm_adapter import get_llm_adapter
import re

class CopilotEngine:
    def __init__(self):
        self.llm = get_llm_adapter()

    def generate_completion(self, prefix: str, suffix: str) -> str:
        """
        Generates inline code completion (ghost text).
        """
        system_prompt = (
            "You are an AI code completion assistant inside an IDE. "
            "You will be provided with the code before the cursor (PREFIX) and the code after the cursor (SUFFIX). "
            "Your task is to write ONLY the code that should be inserted exactly at the cursor to complete the snippet. "
            "DO NOT include markdown formatting (like ```python). "
            "DO NOT repeat the prefix or suffix. "
            "DO NOT provide explanations. "
            "Output ONLY the exact text to insert."
        )
        
        user_prompt = f"PREFIX:\n{prefix}\n\nSUFFIX:\n{suffix}\n\nCOMPLETION:"
        
        # We use a short prompt to get a quick response
        response = self.llm.generate(system_prompt, user_prompt)
        
        # Clean up possible markdown code blocks if the LLM ignores instructions
        response = re.sub(r"^```(python)?", "", response.strip())
        response = re.sub(r"```$", "", response.strip())
        
        return response.strip("\n")

    def generate_inline_code(self, prompt: str, context: dict):
        """
        Streams code generation for an inline prompt (Ctrl+I).
        """
        code = context.get("code", "")
        line = context.get("line", 0)
        
        system_prompt = (
            "You are an expert AI software engineer. "
            "The user has highlighted a section of code or placed their cursor in the editor and given you a prompt. "
            "Write the exact code to satisfy the prompt. "
            "You MUST output ONLY the raw code to be inserted or replaced. "
            "DO NOT wrap your response in markdown code blocks. "
            "DO NOT provide any conversational text or explanations. "
            "Just the raw, perfectly indented code."
        )
        
        user_prompt = f"Current Code Context:\n{code}\n\nCursor/Selection is around line {line}.\n\nUser Prompt: {prompt}\n\nGenerated Code:"
        
        for chunk in self.llm.generate_stream(system_prompt, user_prompt):
            # Strip markdown formatting chunks if they appear at the start or end
            if "```" in chunk:
                chunk = chunk.replace("```python", "").replace("```", "")
            yield chunk
