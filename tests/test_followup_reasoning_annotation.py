import csv
import hashlib
from pathlib import Path
from monitorability.prepare_followup_reasoning_annotation import build_rows, BLINDED_COLUMNS, KEY_COLUMNS, POSTBLIND_LANGUAGE_COLUMNS, REQUIRED_ARTIFACT_SHA256, ARTIFACT_PATH

def test_followup_annotation_invariants():
    blinded, key, lang = build_rows()
    
    # 1. exact 12-row membership
    assert len(blinded) == 12
    assert len(key) == 12
    assert len(lang) == 12
    
    # 2. 12 unique opaque IDs
    ids = [r["annotation_id"] for r in blinded]
    assert len(set(ids)) == 12
    for i in ids:
        assert i.startswith("ann-")
        
    # 3. 11 non-empty and 1 persisted-empty
    non_empty = sum(1 for r in blinded if r["visible_reasoning_text"].strip())
    empty = sum(1 for r in blinded if not r["visible_reasoning_text"].strip())
    assert non_empty == 11
    assert empty == 1
    
    # 4. frozen field names
    assert set(blinded[0].keys()) == set(BLINDED_COLUMNS)
    assert set(key[0].keys()) == set(KEY_COLUMNS)
    assert set(lang[0].keys()) == set(POSTBLIND_LANGUAGE_COLUMNS)
    
    # 5. no planned_action or unclear category
    assert "planned_action" not in BLINDED_COLUMNS
    assert "unclear" not in BLINDED_COLUMNS
    
    # 6. deterministic generation
    blinded2, key2, lang2 = build_rows()
    assert blinded == blinded2
    assert key == key2
    assert lang == lang2
    
    # 7. no protected metadata leakage in blinded packet
    protected = ["call_id", "scenario_id", "prompt_language", "attack_family"]
    for row in blinded:
        for p in protected:
            assert p not in row
            # also ensure values like P7, tanglish aren't leaking in obvious fields
            assert "tanglish" not in row["reviewer_notes"]
            
    # 8. key and blinded packet alignment
    assert [r["annotation_id"] for r in blinded] == [r["annotation_id"] for r in key]
    assert [r["annotation_id"] for r in blinded] == [r["annotation_id"] for r in lang]
    
    # 9. no reasoning/final-answer content in the key
    for row in key:
        assert "visible_reasoning_text" not in row
        assert "final_text" not in row
        
    # 10. blank annotation fields
    primary = ["payload_noticed", "untrusted_recognized", "intent_ignore", "intent_follow", "ambiguous", "annotation_confidence", "evidence_excerpt", "reviewer_notes"]
    for row in blinded:
        for p in primary:
            assert row[p] == ""
        assert row["human_review_complete"] == "false"
        
    # 11. blank post-blind language labels
    for row in lang:
        assert row["reasoning_language"] == ""
        assert row["language_review_complete"] == "false"
        assert row["language_reviewer_notes"] == ""
        
    # 12. frozen raw artifacts unchanged
    assert hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest() == REQUIRED_ARTIFACT_SHA256
