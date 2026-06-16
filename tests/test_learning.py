import json
from pathlib import Path

import pytest

from redaktsafe.cli import main
from redaktsafe.contracts import LearningContextCategory, LearningErrorType, ReviewRoute
from redaktsafe.learning import EncryptedSnippetStore, LearningLedger, score_correction


def test_false_negative_direct_identifier_routes_to_review_redact():
    result = score_correction(
        entity_type="MRN",
        error_type=LearningErrorType.FALSE_NEGATIVE,
        context_category=LearningContextCategory.PATIENT_CONTEXT,
        downstream_exposure="external",
        detector_disagreement=True,
        recurrence_count=0,
    )

    assert result.route == ReviewRoute.REVIEW_REDACT
    assert result.score >= 80


def test_medical_eponym_false_positive_routes_to_review_allow():
    result = score_correction(
        entity_type="NAME",
        error_type=LearningErrorType.FALSE_POSITIVE,
        context_category=LearningContextCategory.MEDICAL_EPONYM,
        downstream_exposure="local",
        detector_disagreement=False,
        recurrence_count=1,
    )

    assert result.route == ReviewRoute.REVIEW_ALLOW
    assert 25 <= result.score < 80


def test_contextual_allow_for_clean_eponym_can_auto_allow_with_trace():
    result = score_correction(
        entity_type="NAME",
        error_type=LearningErrorType.CONTEXTUAL_ALLOW,
        context_category=LearningContextCategory.MEDICAL_EPONYM,
        downstream_exposure="local",
        detector_disagreement=False,
        recurrence_count=0,
    )

    assert result.route == ReviewRoute.AUTO_ALLOW_WITH_TRACE
    assert result.score < 25


def test_score_ranks_missed_direct_identifier_above_eponym_false_positive():
    missed_identifier = score_correction(
        entity_type="SSN",
        error_type=LearningErrorType.FALSE_NEGATIVE,
        context_category=LearningContextCategory.PATIENT_CONTEXT,
        downstream_exposure="external",
        detector_disagreement=True,
        recurrence_count=2,
    )
    eponym_false_positive = score_correction(
        entity_type="NAME",
        error_type=LearningErrorType.FALSE_POSITIVE,
        context_category=LearningContextCategory.MEDICAL_EPONYM,
        downstream_exposure="local",
        detector_disagreement=False,
        recurrence_count=0,
    )

    assert missed_identifier.score > eponym_false_positive.score


def test_encrypted_snippet_store_does_not_write_plaintext(tmp_path):
    store = EncryptedSnippetStore(tmp_path)
    snippet_id = store.store("Patient DeVries MRN E1234567", passphrase="local-secret")
    payload = (tmp_path / f"{snippet_id}.snippet").read_bytes()

    assert b"Patient DeVries" not in payload
    assert store.load(snippet_id, passphrase="local-secret") == "Patient DeVries MRN E1234567"
    with pytest.raises(ValueError):
        store.load(snippet_id, passphrase="wrong-secret")


def test_learning_ledger_writes_no_raw_snippet_and_sorts_queue(tmp_path):
    ledger = LearningLedger(tmp_path, passphrase="local-secret")
    low = ledger.append_correction(
        text="DeVries syndrome was mentioned in the family history.",
        span_text="DeVries",
        entity_type="NAME",
        error_type=LearningErrorType.FALSE_POSITIVE,
        context_category=LearningContextCategory.MEDICAL_EPONYM,
        downstream_exposure="local",
        detector_disagreement=False,
        reviewer_id="reviewer-a",
        note="medical eponym",
    )
    high = ledger.append_correction(
        text="Patient DeVries, MRN E1234567, called today.",
        span_text="E1234567",
        entity_type="MRN",
        error_type=LearningErrorType.FALSE_NEGATIVE,
        context_category=LearningContextCategory.PATIENT_CONTEXT,
        downstream_exposure="external",
        detector_disagreement=True,
        reviewer_id="reviewer-a",
        note="missed MRN",
    )

    raw_ledger = (tmp_path / "corrections.jsonl").read_text(encoding="utf-8")
    assert "Patient DeVries" not in raw_ledger
    assert "E1234567" not in raw_ledger
    assert "DeVries syndrome" not in raw_ledger

    queue = ledger.review_queue()
    assert [item.correction_id for item in queue] == [high.correction_id, low.correction_id]


def test_learning_cli_adds_correction_without_plaintext(tmp_path):
    store = tmp_path / ".redaktsafe_learning"
    status = main(
        [
            "learning",
            "add-correction",
            "--store",
            str(store),
            "--passphrase",
            "local-secret",
            "--text",
            "Patient DeVries, MRN E1234567.",
            "--span-text",
            "E1234567",
            "--entity-type",
            "MRN",
            "--error-type",
            "false_negative",
            "--context-category",
            "patient_context",
            "--downstream-exposure",
            "external",
            "--detector-disagreement",
            "--reviewer-id",
            "reviewer-a",
        ]
    )

    assert status == 0
    raw_ledger = (store / "corrections.jsonl").read_text(encoding="utf-8")
    assert "Patient DeVries" not in raw_ledger
    assert "E1234567" not in raw_ledger


def test_learning_cli_queue_lists_highest_priority_first(tmp_path, capsys):
    store = tmp_path / ".redaktsafe_learning"
    ledger = LearningLedger(store, passphrase="local-secret")
    ledger.append_correction(
        text="DeVries syndrome.",
        span_text="DeVries",
        entity_type="NAME",
        error_type=LearningErrorType.FALSE_POSITIVE,
        context_category=LearningContextCategory.MEDICAL_EPONYM,
        downstream_exposure="local",
        detector_disagreement=False,
    )
    high = ledger.append_correction(
        text="Patient DeVries, MRN E1234567.",
        span_text="E1234567",
        entity_type="MRN",
        error_type=LearningErrorType.FALSE_NEGATIVE,
        context_category=LearningContextCategory.PATIENT_CONTEXT,
        downstream_exposure="external",
        detector_disagreement=True,
    )

    status = main(["learning", "queue", "--store", str(store)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert status == 0
    assert payload[0]["correction_id"] == high.correction_id


def test_learning_store_is_gitignored():
    ignore_text = Path(".gitignore").read_text(encoding="utf-8")

    assert ".redaktsafe_learning/" in ignore_text
