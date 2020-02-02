# WhereWholf!

Library to simulate a game of [Werewolf](https://en.wikipedia.org/wiki/Werewolf_(social_deduction_game).
Works like a modified variant of [Ultimate](https://beziergames.com/products/ultimate-werewolf-deluxe-edition).

The goal is that this can be used to write a game with actual human 
participation (...and, eventually, pass the Turing Test, totally). But we are
not there yet.

## Design Decisions

Werewolf is a game that relies on social manipulation and trickery. Players lie
all the time and that is part of the fun. The code is designed to reflect the
deceptive nature of this game: as much as possible, we try to prevent `Player`
objects from being able to introspect[^1] other players.

This might result to un-Pythonic code. Wherever this is done, the accompanying
documentation will make note of this decision.

[^1] In as much as we can do so in Python. Ultimately, classes might be able to
read memory segments it should not have access to, should this bug exist in the
Python interpreter.

## Running

A `requirements.txt` file is included, listing all Python dependencies. This
should run with a vanilla Python 3.7 interpreter but for development, the
dependencies are conveniences you'd want to have.

To run,

```
python -m src.main
```

You can set the following environment variables too, mostly for debugging:

- `WHEREWHOLF_MISC_LOG` - control the log output of computations that are not
strictly part of the main game loop.
