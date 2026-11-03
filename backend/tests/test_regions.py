import pytest

from lol_coach.riot.regions import regional_for


def test_known_platforms() -> None:
    assert regional_for("jp1") == "asia"
    assert regional_for("kr") == "asia"
    assert regional_for("na1") == "americas"
    assert regional_for("euw1") == "europe"
    assert regional_for("oc1") == "sea"


def test_case_insensitive() -> None:
    assert regional_for("JP1") == "asia"
    assert regional_for("Kr") == "asia"


def test_unknown_platform_raises() -> None:
    with pytest.raises(ValueError, match="unknown platform"):
        regional_for("xyz1")
