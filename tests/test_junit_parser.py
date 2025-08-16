import pytest

from utils.junit import parse_junit_summary


def test_parse_single_testsuite():
    xml = '<testsuite tests="3" failures="1" errors="0"></testsuite>'
    passed, total = parse_junit_summary(xml)
    assert (passed, total) == (2, 3)


def test_parse_testsuites():
    xml = (
        '<testsuites>'
        '<testsuite tests="2" failures="1" />'
        '<testsuite tests="1" errors="1" />'
        '</testsuites>'
    )
    passed, total = parse_junit_summary(xml)
    assert (passed, total) == (1, 3)


def test_invalid_xml():
    with pytest.raises(ValueError):
        parse_junit_summary('<notxml>')
