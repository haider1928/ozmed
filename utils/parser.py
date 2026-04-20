import json
import re

class Parser:
    @staticmethod
    def extract_json(text_response):
        """
        Safely extracts JSON from a model's textual response.
        Handles markdown blocks (```json ... ```) or pure JSON strings.
        Returns a dict. Raises ValueError if unparseable.
        """
        text_response = text_response.strip()
        
        # 1. Try raw JSON parsing first
        try:
            return json.loads(text_response)
        except json.JSONDecodeError:
            pass

        # 2. Try extracting from markdown block
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        # 3. Try to find the first `{` and last `}`
        start_idx = text_response.find('{')
        end_idx = text_response.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text_response[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
                
        raise ValueError("Could not extract valid JSON from the response.")
