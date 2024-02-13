class GameDeadLockError(Exception):
    """
    Thrown when game agents could not decide and must just break the loop.
    """
    pass

class InvalidGameStateError(Exception):
    """
    For when the game has reached an unworkable state.
    """
    pass
