from redaktsafe.detectors.regex_detectors import detect


def test_detects_core_synthetic_identifiers():
    text = "Patient Jane Doe, MRN E4567890, phone 617-555-0142, email jane@example.com."
    entity_types = {span.entity_type for span in detect(text)}
    assert {"NAME", "MRN", "PHONE", "EMAIL"}.issubset(entity_types)


def test_drug_names_are_not_patient_names():
    text = "Patient takes Jardiance and metformin. Dr. Green reviewed the case. No patient name provided."
    entity_types = {span.entity_type for span in detect(text)}
    assert "NAME" not in entity_types


def test_high_risk_fixture_entities_detected():
    text = """Name: Maria Rivera
MRN: MRN-992188
DOB: 04/05/1965
Phone: (212) 555-0101
Address: 123 Oak Street, Boston MA
"""
    entity_types = {span.entity_type for span in detect(text)}
    assert {"NAME", "MRN", "DATE", "PHONE", "ADDRESS"}.issubset(entity_types)


def test_detects_expanded_entity_taxonomy_without_weakening_structured_identifiers():
    text = (
        "Provider Dr. Ada Lovelace works in Cardiology Department at Johns Hopkins Hospital. "
        "Specimen went to DeVries Lab in East Tower. Username: alovelace. Passport: X12345678. "
        "MRN E4567890."
    )

    entity_types = {span.entity_type for span in detect(text)}

    assert {
        "PROVIDER",
        "DEPARTMENT",
        "INSTITUTION",
        "LAB",
        "BUILDING",
        "USERNAME",
        "ID",
        "MRN",
    }.issubset(entity_types)
