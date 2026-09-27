import pytest
import yaml
from pydantic import ValidationError

from weekly_report import config
from weekly_report.commentary_schema import commentary_model, json_schema

LAYOUT = yaml.safe_load(config.LAYOUT_FILE.read_text())
P = {"what": "Orders were 1,192 against a target of 982.", "so_what": "The week finished 21.4% ahead of target."}


def valid() -> dict:
    return {"summary": {"headline": "Ahead of target for the week.", "points": [P, P, P]},
            "watchouts": {"points": []},
            "vs_target": {"points": [P, P]},
            "drivers": {"points": [P, P]},
            "health": {"points": [P, P, P]}}


def test_schema_has_one_field_per_layout_slot_in_order():
    assert list(json_schema()["properties"]) == list(LAYOUT["commentary_slots"])


def test_valid_commentary_passes():
    commentary_model()(**valid())


def test_point_limits_come_from_layout():
    bad = valid()
    bad["summary"]["points"] = [P] * (LAYOUT["commentary_slots"]["summary"]["max_points"] + 1)
    with pytest.raises(ValidationError):
        commentary_model()(**bad)


def test_headline_only_where_layout_requires_it():
    bad = valid()
    del bad["summary"]["headline"]
    with pytest.raises(ValidationError):
        commentary_model()(**bad)
    extra = valid()
    extra["drivers"]["headline"] = "not allowed here"
    with pytest.raises(ValidationError):
        commentary_model()(**extra)


def test_every_point_needs_a_so_what_and_nothing_else():
    for bad_point in ({"what": "x"}, {"what": "x", "so_what": ""}, {**P, "cause": "a campaign"}):
        bad = valid()
        bad["vs_target"]["points"] = [bad_point, P]
        with pytest.raises(ValidationError):
            commentary_model()(**bad)


def test_schema_is_self_contained():
    import json
    assert "$ref" not in json.dumps(json_schema()) and "$defs" not in json_schema()
