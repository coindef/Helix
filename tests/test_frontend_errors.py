import pytest

from helix.frontend.errors import SpecError, parse_source


def test_parse_source_rejects_unsupported_format_instead_of_parsing_as_helix():
    with pytest.raises(SpecError, match="unsupported source format: 'json'") as exc_info:
        parse_source("experiment: é", fmt="json")

    assert exc_info.value.kind == "spec"


def test_parse_source_reports_unicode_yaml_syntax_location():
    with pytest.raises(SpecError, match="invalid YAML") as exc_info:
        parse_source("name: é\ntarget: [", fmt="yaml")

    assert (exc_info.value.line, exc_info.value.col) == (2, 10)


def test_parse_source_rejects_empty_yaml_document_as_spec_error():
    with pytest.raises(SpecError, match="must be a mapping") as exc_info:
        parse_source("", fmt="yaml")

    assert exc_info.value.kind == "spec"
