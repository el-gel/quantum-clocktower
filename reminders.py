from typing import NamedTuple, Any

class ReminderToken(NamedTuple):
    """Reminder tokens."""
    character: Any # Associated Character class for this token
    type_: Any # Type of token; e.g. ABILITY_USED or DAY_X for Courtier
    text: str = "" # Text of the token. For niceness?
    # These are different to allow for e.g. gossips
    drunks: bool = False # Does this token cause drunkenness?
    poisons: bool = False # Does this token cause poisoning?
    # Not all get removed; e.g. ABILITY_USED
    droison_removes: bool = True
    
    @property
    def droisons(self):
        """Does this token cause droisoning on the recipient?"""
        return self.drunks or self.poisons

    def __str__(self):
        return self.text
