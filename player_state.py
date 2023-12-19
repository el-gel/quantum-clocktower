from timeline import *

@timelined(ss_attrs=('alive','character','reminders','placed_reminders'))
class Player(object):
    """A (single-possibility) state of a player, including liveness and reminder tokens."""
    def __init__(self, character, position, alive=True, reminders=(), placed_reminders=()):
        self.alive = alive
        self.character = character
        self.position = position
        self.reminders = list(reminders) # Reminders on this player
        self.placed_reminders = list(placed_reminders) # (player, reminder) tuples this player is trying to apply

    def copy(self, alive=None, character=None, reminders=None, placed_reminders=None):
        """Make a copy of this state, applying modifications as specified."""
        raise NotImplementedError()

    def add_reminder(self, reminder_token):
        """Add a reminder token to this player, and apply any state changes as such."""
        self.reminders.append(reminder_token)

    def remove_reminder(self, reminder_token):
        """Remove a reminder token from this player, and apply any state changes."""
        if reminder_token not in self.reminders:
            raise ValueError("Reminder token "+ str(reminder_token) + " not on player" + str(self) + ".")
        self.reminders.remove(reminder_token)

    def place_reminder(self, reminder_token, other):
        """This player adds a reminder token to another."""
        self.placed_reminders.append((other, reminder_token)) 
        other.add_reminder(reminder_token)

    def take_reminder(self, reminder_token, other):
        """This player removes their reminder token from another."""
        self.placed_reminders.remove((other, reminder_token))
        other.remove_reminder(reminder_token)

    def droisoning_tokens(self):
        """Which placed tokens is this player trying to droison with?"""
        return [placed for placed in self.placed_reminders if placed[1].droisons]

    def __str__(self):
        return "Player in seat {}".format(self.position)
