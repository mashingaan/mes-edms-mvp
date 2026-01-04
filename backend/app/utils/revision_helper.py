"""Revision label logic according to plan specification.

Excluded letters: I, O, Q, S, X, Z
Allowed letters: A-H, J-N, P, R, T-W, Y (20 letters)
"""

EXCLUDED_LETTERS = {'I', 'O', 'Q', 'S', 'X', 'Z'}
ALLOWED_LETTERS = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',  # A-H
    'J', 'K', 'L', 'M', 'N',                  # J-N
    'P', 'R',                                  # P, R
    'T', 'U', 'V', 'W',                        # T-W
    'Y'                                        # Y
]


def get_next_revision(current_label: str) -> str:
    """Get the next revision label.
    
    Args:
        current_label: Current revision label ("-", "A", "B", etc.)
    
    Returns:
        Next revision label
    
    Raises:
        ValueError: If current label is invalid or max revision reached
    """
    if current_label == "-":
        return "A"
    
    if current_label in ALLOWED_LETTERS:
        idx = ALLOWED_LETTERS.index(current_label)
        if idx < len(ALLOWED_LETTERS) - 1:
            return ALLOWED_LETTERS[idx + 1]
        else:
            raise ValueError("Maximum revision reached")
    
    raise ValueError(f"Invalid revision label: {current_label}")

