class GameDeadLockError(Exception):
    """
    Thrown when game agents could not decide and must just break the loop.
    """
    pass
