import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProcessedOutput:
    command: str
    status: str
    mode_used: str
    summary: str
    extracted_output: Any
    errors: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "status": self.status,
            "mode_used": self.mode_used,
            "summary": self.summary,
            "extracted_output": self.extracted_output,
            "errors": self.errors,
        }


class OutputProcessor:
    def __init__(self, head_chars: int = 500, tail_chars: int = 1200, slice_chars: int = 1200):
        self.head_chars = head_chars
        self.tail_chars = tail_chars
        self.slice_chars = slice_chars

    def process(self, command: str, output: Any, mode: str = "AUTO") -> ProcessedOutput:
        raw_text = self._to_text(output)
        errors = self._extract_errors(output, raw_text)
        chosen_mode = self._select_mode(mode, raw_text, errors)
        summary = self._build_summary(raw_text, errors, chosen_mode)
        excerpt = self._extract_excerpt(raw_text, chosen_mode, output)

        return ProcessedOutput(
            command=command,
            status="error" if errors else "ok",
            mode_used=chosen_mode,
            summary=summary,
            extracted_output=excerpt,
            errors=errors,
        )

    def _select_mode(self, mode: str, raw_text: str, errors: List[str]) -> str:
        requested = (mode or "AUTO").upper()
        if requested != "AUTO":
            return requested

        if errors:
            return "TAIL"

        if len(raw_text) <= 1200:
            return "FULL"

        if self._looks_structured(raw_text):
            return "SUMMARY"

        if self._looks_repetitive(raw_text):
            return "SUMMARY"

        return "TAIL"

    def _to_text(self, output: Any) -> str:
        if output is None:
            return ""
        if isinstance(output, str):
            return output
        return json.dumps(output, indent=2, ensure_ascii=False, default=str)

    def _extract_errors(self, output: Any, raw_text: str) -> List[str]:
        errors: List[str] = []

        if isinstance(output, dict):
            for key in ("error", "errors", "stderr"):
                value = output.get(key)
                if isinstance(value, str) and value.strip():
                    errors.append(value.strip())
                elif isinstance(value, list):
                    errors.extend(str(item).strip() for item in value if str(item).strip())

        for line in raw_text.splitlines():
            if line.startswith("ERROR:") or "Traceback" in line:
                errors.append(line.strip())

        return self._dedupe(errors)

    def _build_summary(self, raw_text: str, errors: List[str], mode_used: str) -> str:
        if errors:
            return f"{len(errors)} error(s) detected."
        if not raw_text.strip():
            return "No output returned."
        if mode_used == "FULL":
            return "Full output returned."
        if self._looks_structured(raw_text):
            return "Structured output captured and reduced."
        if self._looks_repetitive(raw_text):
            return "Repetitive output deduplicated."
        return "Large output truncated for context safety."

    def _extract_excerpt(self, raw_text: str, mode_used: str, output: Any) -> Any:
        text = raw_text.strip()
        if mode_used == "FULL":
            return output
        if mode_used == "HEAD":
            return text[: self.head_chars]
        if mode_used == "TAIL":
            return text[-self.tail_chars :]
        if mode_used == "SLICE":
            start = max(0, (len(text) // 2) - (self.slice_chars // 2))
            end = start + self.slice_chars
            return text[start:end]
        if mode_used == "GREP":
            return self._grep_excerpt(text)
        if mode_used == "SUMMARY":
            return self._summarize_structured(output, text)
        return text[-self.tail_chars :]

    def _grep_excerpt(self, text: str) -> List[str]:
        lines = text.splitlines()
        selected = [line for line in lines if re.search(r"(error|warn|fail|traceback|exception|result|status)", line, re.I)]
        return self._dedupe(selected)[:25]

    def _summarize_structured(self, output: Any, text: str) -> Any:
        if isinstance(output, list):
            return {
                "count": len(output),
                "first_items": output[:5],
                "last_items": output[-5:] if len(output) > 5 else output[:5],
            }
        if isinstance(output, dict):
            keys = list(output.keys())
            return {
                "keys": keys[:15],
                "preview": {k: output[k] for k in keys[:10]},
            }
        return self._grep_excerpt(text)

    def _looks_structured(self, text: str) -> bool:
        stripped = text.lstrip()
        return stripped.startswith("{") or stripped.startswith("[")

    def _looks_repetitive(self, text: str) -> bool:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return len(lines) >= 8 and len(self._dedupe(lines)) < len(lines) * 0.6

    def _dedupe(self, items: List[str]) -> List[str]:
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def package_tool_result(self, tool_name: str, command: str, output: Any, mode: str = "AUTO") -> Dict[str, Any]:
        processed = self.process(command=command, output=output, mode=mode)
        return {
            "tool": tool_name,
            "result": processed.as_dict(),
        }
