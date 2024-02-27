# WhereWholf!

Library to simulate a game of [Werewolf](https://en.wikipedia.org/wiki/Werewolf_(social_deduction_game)).
Works like a modified variant of [Ultimate](https://beziergames.com/products/ultimate-werewolf-deluxe-edition).

The goal is that this can be used to write a game with actual human 
participation (...and, eventually, pass the Turing Test, totally). But we are
not there yet.

## Design Decisions

Werewolf is a game that relies on social manipulation and trickery. Players lie
all the time and that is part of the fun. The code is designed to reflect the
deceptive nature of this game: as much as possible, we try to prevent `Player`
objects from being able to introspect<sup>1</sup> other players.

This might result to un-Pythonic code. Wherever this is done, the accompanying
documentation will make note of this decision.

<sup>1</sup> In as much as we can do so in Python. Ultimately, classes might be able to
read memory segments it should not have access to, should this bug exist in the
Python interpreter. See also: Python's "We are all adults here" philosophy.

### Game Entities

For a player, a Wherewholf game is divided into two phases: night time and day
time.

**Night time** actions is role-dependent and facilitated largely by the
moderator. Most notably, during this phase, the player can learn things about
the game (e.g., other players' roles).

**Day time** is further divided into phases and each player has a set of
attributes that could influence their behavior during these phases:

1. Nomination phase. Players accuse each other of being a werewolf. A player's
   `aggression` attribute dictates how likely he is to nominate others.
2. Discussion phase. In a real-life game, this is where players argue over the
   nominations, coordinating their votes on who to lynch. In this simulation,
   each nominated player can advocate for themselves, the efficacy of this is
   dictated by the `pesuasiveness` attribute (DnD players might also call this
   _charisma_).
3. Votation phase. The player with the most votes gets lynched. Players who made
   a nomination in the first phase will automatically vote for who they
   nominated. In turn, players who were nominated will _never<sup>1</sup>_ vote
   for them. For everyone else, their `suggestibility` attribute will dictate
   how likely will they vote to lynch a nominated player.

At the end of the day time phase, the role of the lynched player is revealed;
this is information gained by all the players in the game.

<sup>1</sup> This might change upon introduction of the Tanner role.

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
