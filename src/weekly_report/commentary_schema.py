"""Output format for the AI commentary, generated from the commentary slots in report_layout.yaml.

The layout is the single source: adding a slot or changing its point limits there changes the
format Claude must return, the validation below, and the boxes on the page, all at once.
"""

from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, create_model

from . import config

SENTENCE_MAX_CHARS = 240   # about 30 words; the exact word limit is checked by the guards


class Point(BaseModel):
    """One bullet: the fact, then what it means for the business."""
    model_config = ConfigDict(extra="forbid")
    what: str = Field(min_length=1, max_length=SENTENCE_MAX_CHARS, description="One sentence: the fact, with numbers from the brief")
    so_what: str = Field(min_length=1, max_length=SENTENCE_MAX_CHARS, description="One sentence: the business implication, grounded in the brief")


def _slot_model(name: str, rules: dict) -> type[BaseModel]:
    fields: dict = {
        "points": (list[Point], Field(min_length=rules["min_points"], max_length=rules["max_points"],
                                      description=f"{rules['min_points']} to {rules['max_points']} points")),
    }
    if (rules.get("headline") or {}).get("required"):
        fields = {"headline": (str, Field(min_length=1, max_length=SENTENCE_MAX_CHARS,
                                          description=f"At most {rules['headline']['max_words']} words")), **fields}
    return create_model(f"{name.title().replace('_', '')}Slot", __config__=ConfigDict(extra="forbid"), **fields)


def commentary_model(layout: Optional[dict] = None) -> type[BaseModel]:
    """Pydantic model for the whole commentary: one field per slot, in layout order."""
    layout = layout or yaml.safe_load(config.LAYOUT_FILE.read_text())
    slots = {name: (_slot_model(name, rules), ...) for name, rules in layout["commentary_slots"].items()}
    return create_model("Commentary", __config__=ConfigDict(extra="forbid"), **slots)


def json_schema(layout: Optional[dict] = None) -> dict:
    """JSON Schema handed to Claude (--json-schema) so the answer always has the page's shape.

    References ($ref / $defs) are inlined so the schema is one self-contained object.
    """
    schema = commentary_model(layout).model_json_schema()
    defs = schema.pop("$defs", {})

    def inline(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return inline(defs[node["$ref"].split("/")[-1]])
            return {k: inline(v) for k, v in node.items()}
        if isinstance(node, list):
            return [inline(v) for v in node]
        return node

    return inline(schema)
