import pytest

from app.utils.revision_helper import get_next_revision, ALLOWED_LETTERS


def test_next_revision_initial():
    """Initial revision '-' returns 'A'."""
    assert get_next_revision("-") == "A"


def test_next_revision_sequence():
    """Normal revision sequence works."""
    assert get_next_revision("A") == "B"
    assert get_next_revision("B") == "C"
    assert get_next_revision("C") == "D"


def test_next_revision_skip_excluded_i():
    """Skip 'I' - H goes to J."""
    assert get_next_revision("H") == "J"


def test_next_revision_skip_excluded_o():
    """Skip 'O' - N goes to P."""
    assert get_next_revision("N") == "P"


def test_next_revision_skip_excluded_q():
    """Skip 'Q' - P goes to R."""
    assert get_next_revision("P") == "R"


def test_next_revision_skip_excluded_s():
    """Skip 'S' - R goes to T."""
    assert get_next_revision("R") == "T"


def test_next_revision_skip_excluded_x():
    """Skip 'X' - W goes to Y."""
    assert get_next_revision("W") == "Y"


def test_next_revision_max():
    """Maximum revision 'Y' raises error."""
    with pytest.raises(ValueError) as exc_info:
        get_next_revision("Y")
    
    assert "Maximum revision reached" in str(exc_info.value)


def test_next_revision_invalid():
    """Invalid revision label raises error."""
    with pytest.raises(ValueError) as exc_info:
        get_next_revision("I")  # Excluded letter
    
    assert "Invalid revision label" in str(exc_info.value)


def test_next_revision_full_sequence():
    """Full revision sequence is correct."""
    expected = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R", "T", "U", "V", "W", "Y"]
    
    current = "-"
    for expected_rev in expected:
        next_rev = get_next_revision(current)
        assert next_rev == expected_rev
        current = next_rev
    
    assert len(ALLOWED_LETTERS) == 20

