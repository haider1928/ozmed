import json
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional


class Memory:
    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        self.deep_memory_file = os.path.join(os.path.dirname(memory_file), "deep_memory.json")
        self.short_term_limit = 20
        self.deep_memory_limit = 250
        self._init_file(self.memory_file, self._default_regular_data())
        self._init_file(self.deep_memory_file, self._default_deep_data())

    def _default_regular_data(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"short_term": [], "long_term_compressed": [], "factual_memory": []}

    def _default_deep_data(self) -> Dict[str, Any]:
        return {"entries": []}

    def _init_file(self, path: str, default_data: Dict[str, Any]):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)

    def _load_json(self, path: str, default_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = default_data

        if not isinstance(data, dict):
            return default_data

        return self._normalize_loaded_data(path, data, default_data)

    def _normalize_loaded_data(self, path: str, data: Dict[str, Any], default_data: Dict[str, Any]) -> Dict[str, Any]:
        if path == self.memory_file:
            normalized = self._default_regular_data()

            if "short_term" in data or "long_term_compressed" in data or "factual_memory" in data:
                normalized["short_term"] = data.get("short_term", [])
                normalized["long_term_compressed"] = data.get("long_term_compressed", [])
                normalized["factual_memory"] = data.get("factual_memory", [])
                return normalized

            legacy_messages = data.get("messages", [])
            if isinstance(legacy_messages, list):
                normalized["short_term"] = [
                    {
                        "role": message.get("role", "user"),
                        "content": self._compress_text(message.get("content", ""), 800),
                    }
                    for message in legacy_messages
                    if isinstance(message, dict)
                ]
            return normalized

        if path == self.deep_memory_file:
            normalized = self._default_deep_data()
            entries = data.get("entries", [])
            if isinstance(entries, list):
                normalized["entries"] = entries
            return normalized

        return data if isinstance(data, dict) else default_data

    def _save_json(self, path: str, data: Dict[str, Any]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_memory(self):
        data = self._load_json(self.memory_file, self._default_regular_data())
        short_term = data.get("short_term", [])
        return short_term[-self.short_term_limit * 2 :]

    def add_to_memory(self, user_message, assistant_response):
        data = self._load_json(self.memory_file, self._default_regular_data())
        data.setdefault("short_term", [])
        data.setdefault("long_term_compressed", [])
        data.setdefault("factual_memory", [])
        data["short_term"].append({"role": "user", "content": self._compress_text(user_message, 700)})
        data["short_term"].append({"role": "assistant", "content": self._compress_text(assistant_response, 1000)})

        if len(data["short_term"]) > self.short_term_limit * 2:
            overflow = data["short_term"][:-self.short_term_limit * 2]
            data["short_term"] = data["short_term"][-self.short_term_limit * 2 :]
            data["long_term_compressed"].append(self._compress_messages(overflow))
            data["long_term_compressed"] = self._dedupe_entries(data["long_term_compressed"])
            data["long_term_compressed"] = data["long_term_compressed"][-100:]

        data["factual_memory"].extend(self._extract_facts(user_message, assistant_response))
        data["factual_memory"] = self._dedupe_entries(data["factual_memory"])
        data["factual_memory"] = data["factual_memory"][-250:]

        self._save_json(self.memory_file, data)
        self._auto_promote_to_deep_memory(user_message, assistant_response)

    def _compress_text(self, text: Any, max_chars: int = 800) -> str:
        value = str(text).strip()
        if len(value) <= max_chars:
            return value
        return value[: max_chars - 32] + " ...[truncated]"

    def _compress_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = " ".join(str(m.get("content", "")) for m in messages).strip()
        return {
            "type": "compressed_context",
            "message_count": len(messages),
            "summary": self._compress_text(text, 1200),
        }

    def _extract_facts(self, user_message: Any, assistant_response: Any) -> List[Dict[str, Any]]:
        return [
            {"type": "user_intent", "value": self._compress_text(user_message, 500)},
            {"type": "assistant_result", "value": self._compress_text(assistant_response, 1000)},
        ]

    def _dedupe_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        output = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            output.append(entry)
        return output

    def _load_deep_memory(self) -> Dict[str, Any]:
        data = self._load_json(self.deep_memory_file, self._default_deep_data())
        if "entries" not in data or not isinstance(data["entries"], list):
            data["entries"] = []
        return data

    def _save_deep_memory(self, data: Dict[str, Any]):
        data["entries"] = self._dedupe_entries(data.get("entries", []))
        data["entries"] = data["entries"][-self.deep_memory_limit :]
        self._save_json(self.deep_memory_file, data)

    def list_memory(self, memory_type: str = "deep") -> List[Dict[str, Any]]:
        if memory_type == "deep":
            return self._load_deep_memory().get("entries", [])
        if memory_type == "short":
            return self.get_memory()
        if memory_type == "all":
            deep = self._load_deep_memory().get("entries", [])
            return self.get_memory() + deep
        return []

    def add_memory(self, item: Dict[str, Any], memory_type: str = "deep"):
        if memory_type == "deep":
            data = self._load_deep_memory()
            data["entries"].append(self._normalize_deep_entry(item))
            self._save_deep_memory(data)
        else:
            data = self._load_json(self.memory_file, self._default_regular_data())
            data["factual_memory"].append(item)
            data["factual_memory"] = self._dedupe_entries(data["factual_memory"])
            self._save_json(self.memory_file, data)

    def update_memory(self, memory_id: str, updates: Dict[str, Any], memory_type: str = "deep") -> bool:
        if memory_type != "deep":
            return False
        data = self._load_deep_memory()
        for entry in data["entries"]:
            if entry.get("id") == memory_id:
                entry.update(updates)
                entry["updated_at"] = self._now()
                self._save_deep_memory(data)
                return True
        return False

    def delete_memory(self, memory_id: str, memory_type: str = "deep") -> bool:
        if memory_type != "deep":
            return False
        data = self._load_deep_memory()
        before = len(data["entries"])
        data["entries"] = [entry for entry in data["entries"] if entry.get("id") != memory_id]
        changed = len(data["entries"]) != before
        if changed:
            self._save_deep_memory(data)
        return changed

    def compress_memory(self, memory_type: str = "deep"):
        if memory_type != "deep":
            return
        data = self._load_deep_memory()
        merged = []
        for entry in data["entries"]:
            merged = self._merge_into_collection(merged, entry)
        data["entries"] = merged
        self._save_deep_memory(data)

    def get_relevant_deep_memory(self, current_text: str, limit: int = 8) -> List[Dict[str, Any]]:
        data = self._load_deep_memory()
        scored = []
        current_terms = self._tokenize(current_text)
        for entry in data.get("entries", []):
            score = self._score_relevance(current_terms, entry)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def _auto_promote_to_deep_memory(self, user_message: Any, assistant_response: Any):
        candidate_text = f"{user_message}\n{assistant_response}"
        candidates = self._extract_deep_candidates(candidate_text)
        if not candidates:
            return
        data = self._load_deep_memory()
        for candidate in candidates:
            normalized = self._normalize_deep_entry(candidate)
            data["entries"] = self._merge_into_collection(data["entries"], normalized)
        self._save_deep_memory(data)

    def _extract_deep_candidates(self, text: str) -> List[Dict[str, Any]]:
        lowered = text.lower()
        candidates: List[Dict[str, Any]] = []

        patterns = [
            ("preference", r"\b(i prefer|my preference is|i like|i dislike|i don't like)\b"),
            ("goal", r"\b(my goal is|i want to|i'm trying to|i need to)\b"),
            ("habit", r"\b(i usually|i always|every day|every week|most days)\b"),
            ("tool_preference", r"\b(use|prefer)\s+(summary|tail|head|grep|auto|full)\b"),
            ("project_context", r"\b(project|repo|codebase|feature|bug|task)\b"),
            ("stable_fact", r"\b(my name is|i am|i work as|i live in)\b"),
        ]

        for memory_type, pattern in patterns:
            if re.search(pattern, lowered):
                candidates.append(
                    {
                        "type": memory_type,
                        "summary": self._compress_text(text, 300),
                        "importance": "high" if memory_type in {"goal", "stable_fact", "tool_preference"} else "medium",
                        "confidence": 0.72,
                        "source": "auto",
                        "scope": "long_term",
                    }
                )
                break

        if self._looks_like_decision(text):
            candidates.append(
                {
                    "type": "decision",
                    "summary": self._compress_text(text, 300),
                    "importance": "high",
                    "confidence": 0.8,
                    "source": "auto",
                    "scope": "long_term",
                }
            )

        return candidates

    def _looks_like_decision(self, text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in ["we will", "let's", "use this", "decided", "going forward", "from now on"])

    def _normalize_deep_entry(self, item: Dict[str, Any]) -> Dict[str, Any]:
        summary = self._compress_text(item.get("summary") or item.get("value") or item.get("content") or "", 400)
        entry_type = item.get("type", "fact")
        return {
            "id": item.get("id") or self._make_id(entry_type, summary),
            "type": entry_type,
            "summary": summary,
            "importance": item.get("importance", "medium"),
            "confidence": float(item.get("confidence", 0.7)),
            "scope": item.get("scope", "long_term"),
            "source": item.get("source", "manual"),
            "updated_at": item.get("updated_at") or self._now(),
        }

    def _merge_into_collection(self, collection: List[Dict[str, Any]], new_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        normalized_new = self._normalize_deep_entry(new_entry)
        merged = []
        replaced = False
        new_terms = set(self._tokenize(normalized_new["summary"]))

        for entry in collection:
            if self._is_similar(entry, normalized_new) or self._same_topic(entry, normalized_new):
                entry = self._merge_entries(entry, normalized_new)
                replaced = True
            merged.append(entry)

        if not replaced:
            merged.append(normalized_new)
        return self._dedupe_entries(merged)

    def _merge_entries(self, old_entry: Dict[str, Any], new_entry: Dict[str, Any]) -> Dict[str, Any]:
        merged_summary = self._prefer_better_summary(old_entry.get("summary", ""), new_entry.get("summary", ""))
        return {
            **old_entry,
            "summary": merged_summary,
            "importance": self._max_importance(old_entry.get("importance"), new_entry.get("importance")),
            "confidence": max(float(old_entry.get("confidence", 0)), float(new_entry.get("confidence", 0))),
            "updated_at": self._now(),
        }

    def _prefer_better_summary(self, a: str, b: str) -> str:
        return b if len(b) <= len(a) and b else a if a else b

    def _max_importance(self, a: Optional[str], b: Optional[str]) -> str:
        order = {"low": 0, "medium": 1, "high": 2}
        a_score = order.get((a or "medium").lower(), 1)
        b_score = order.get((b or "medium").lower(), 1)
        return a if a_score >= b_score else b

    def _same_topic(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        return a.get("type") == b.get("type") and self._jaccard(a.get("summary", ""), b.get("summary", "")) >= 0.45

    def _is_similar(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        return self._jaccard(a.get("summary", ""), b.get("summary", "")) >= 0.6

    def _jaccard(self, a: str, b: str) -> float:
        sa = set(self._tokenize(a))
        sb = set(self._tokenize(b))
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    def _score_relevance(self, current_terms: List[str], entry: Dict[str, Any]) -> float:
        entry_terms = set(self._tokenize(entry.get("summary", "")))
        if not entry_terms:
            return 0.0
        overlap = len(set(current_terms) & entry_terms)
        base = overlap / max(len(entry_terms), 1)
        importance_boost = {"low": 0.0, "medium": 0.15, "high": 0.3}.get(str(entry.get("importance", "medium")).lower(), 0.15)
        return base + importance_boost

    def _tokenize(self, text: str) -> List[str]:
        return [token for token in re.findall(r"[a-z0-9_]+", str(text).lower()) if len(token) > 2]

    def _make_id(self, entry_type: str, summary: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{entry_type}-{summary.lower()}").strip("-")
        return slug[:80] or f"{entry_type}-{len(summary)}"

    def _now(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
