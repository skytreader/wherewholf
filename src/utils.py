from collections import Counter
from collections.abc import Iterable as IterableBaseClass

from typing import (
    Any, Counter as t_Counter, Dict, Iterable, Iterator, List, Mapping,
    Optional, Set, Sequence, Tuple, TYPE_CHECKING, Union
)

import _collections_abc
import logging
import os

if TYPE_CHECKING:
    from .game_characters import SanitizedPlayer


logger: logging.Logger = logging.getLogger("WHEREWHOLF_UTILS")
logger.setLevel(logging.getLevelName(
    os.environ.get("WHEREWHOLF_MISC_LOG", "INFO")
))
log_format: str = "%(asctime)s - UTIL:%(levelname)s - %(message)s"
handler: logging.Handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(handler)


class ValueIndex(object):
    """
    Items that are not in the set are technically in index 0 but since there is
    an infinite number of items not included in the set...

    Behavior of such items are undefined as of yet.
    """

    def __init__(self) -> None:
        self.value_index: Dict[int, Set[Any]] = {}

    def __getitem__(self, key: int) -> Set[Any]:
        return self.value_index[key]

    def update_index(self, value: int, reference: Any) -> None:
        if self.value_index.get(value):
            self.value_index[value].add(reference)
        else:
            self.value_index[value] = set((reference,))

    def remove_reference(self, index: int, reference: Any) -> None:
        current_index: Set[Any] = self.value_index.get(index, set())

        if reference in current_index:
            current_index.remove(reference)

    def list_indices(self) -> Sequence[int]:
        return tuple(self.value_index.keys())


class ValueTieCounter(Counter):
    """
    Custom Counter class that takes ties into account in the `most_common`
    method. Other than that, this should be a drop-in replacement for
    collections.Counter.
    
    Note that the reference implementation for this is the Counter class in
    CPython 3.7; 3.8 introduces syntactic changes that are not
    backwards-compatible to 3.7.

    ACHTUNG! The idea is to keep this class as similar in behavior to
    collections.Counter as much as possible, to the extent that it is a
    drop-in replacement except for when behavior really differs as documented.
    However, in practice, we implement just enough for it to be useable in
    Wherewholf.
    """

    # NOTE The reference implementation does not declare a `self` parameter but
    # splits `*args` via `self, *args = args` before `self` is even ever used.
    # I would've done the same except that it feels wrong.
    def __init__(self, *args: Any, **kwds: Any) -> None:
        logger.debug("initialized new ValueTieCounter")
        self.internal_counter: Counter = Counter()
        self.internal_counter.update(*args, **kwds)
        self.value_tie_index: ValueIndex = ValueIndex()

        for k, v in self.internal_counter.items():
            self.value_tie_index.update_index(v, k)

        super(ValueTieCounter, self).__init__()

    def __str__(self) -> str:
        return str(self.internal_counter)

    def __getitem__(self, key: Any) -> int:
        return self.internal_counter[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        logger.debug("set %s to value %s" % (key, value))
        self.__update_single(key, value)

    def __bool__(self) -> bool:
        return bool(self.internal_counter)

    def elements(self) -> Iterator[Any]:
        return self.internal_counter.elements()

    def subtract(self, counts: Optional[Union[Mapping[Any, int], Iterable[Any]]], /, **kwds) -> None: # type: ignore[override]
        temp_counter: Counter = Counter(counts)

        for k, v in temp_counter.items():
            old_count = self.internal_counter[k]
            self.internal_counter[k] -= v
            self.value_tie_index.remove_reference(old_count, k)
            self.value_tie_index.update_index(
                self.internal_counter[k], k
            )

    def __index_counts(self) -> None:
        for elem, count in self.internal_counter.items():
            self.value_tie_index.update_index(count, elem)
    
    def __update_single(self, key: Any, value: Any) -> None:
        old_count = self.internal_counter[key]
        self.internal_counter[key] = value
        self.value_tie_index.remove_reference(old_count, key)
        self.value_tie_index.update_index(
            self.internal_counter[key], key
        )

    def update(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 1: 
            raise TypeError("expected at most 1 arguments, got %d" % len(args))
        
        possible_iterable = args[0] if args else None
        if possible_iterable is not None:
            if isinstance(possible_iterable, _collections_abc.Mapping):
                # The reference implementation makes use of an optimization
                # where if the Counter is empty to begin with, we basically just
                # copy the whole thing. If done here, it would result in two
                # linear loops: one for copying the Counter and another for
                # rebuilding the index (via __index_counts). So using this
                # "integrated" loop regardless of case is marginally faster.
                for elem, count in possible_iterable.items():
                    old_count = self.internal_counter[elem]
                    self.internal_counter[elem] += count
                    self.value_tie_index.remove_reference(old_count, elem)
                    self.value_tie_index.update_index(
                        self.internal_counter[elem], elem
                    )
            else:
                # Now we are sure it is an iterable
                for elem in possible_iterable:
                    old_count = self.internal_counter.get(elem, 0)
                    self.internal_counter[elem] = old_count + 1
                    self.value_tie_index.remove_reference(old_count, elem)
                
                # Invariant: After the loop, all the items in possible_iterable
                # have been removed from value_tie_index. Thus, it is safe to
                # just reindex everything.
                self.__index_counts()
        
        if kwargs:
            self.update(kwargs)

    def most_common(self, n: Optional[int]=None) -> List[Tuple[Any, int]]:
        """
        Returns all items with the top `n` highest frequency, ties taken into
        account. Whereas the original `most_common` method assures us that

            len(c.most_common(n)) == n

        the assuurance we have here, on the other hand, is

            len(set([x[1] for x in c.most_common(n)]) == n
        """
        most_common: List[Tuple[Any, int]] = []
        index_keys: Sequence[int] = self.value_tie_index.list_indices()
        top = len(index_keys) if n is None else n
        counts_present: Iterable[int] = sorted(index_keys, reverse=True)[0:top]
        
        for index in counts_present:
            entries: Tuple[Any, ...] = tuple(self.value_tie_index[index])
            most_common.extend([(e, index) for e in entries])

        logger.debug("the most_commmon %s %s" % (n, most_common))
        return most_common

class MarkovChain(object):
    """
    This class allows you to keep a record of the empirical probability that a
    given cause results to some effect.

    Module usage: Players want to keep track of how sound the nominations/
    judgement of their fellow players are, which could influence how much they
    trust that player in the future. We keep track of that via a Markov Chain.
    """

    def __init__(self):
        self.causes: Dict[str, t_Counter[str]] = {}
        # Invariant: 
        #   __
        #   \      causes[s][t]
        #    > ------------------- = 1
        #   /_ cause_occurences[s]
        #    t
        self.cause_occurences: t_Counter[str] = Counter()

    def add_event(self, cause: str, effect: str) -> None:
        cause_matrix: Optional[t_Counter[str]] = self.causes.get(cause)
        if cause_matrix is None:
            self.causes[cause] = Counter()

        self.causes[cause].update([effect])
        self.cause_occurences.update([cause])

    def running_probability(self, cause: str, effect: str) -> float:
        if self.causes.get(cause) is None:
            raise IndexError("No event with the cause '%s' yet." % cause)

        return self.causes[cause][effect] / self.cause_occurences[cause]

class NominationTracker(object):

    def __init__(self, recency: int):
        self.recency: int = recency
        self.tracking: Dict["SanitizedPlayer", List[int]] = {}

    def notemination(self, nominated_by: "SanitizedPlayer", turn: int) -> None:
        track = self.tracking.get(nominated_by)
        
        if track is None:
            self.tracking[nominated_by] = [turn]
        else:
            self.tracking[nominated_by].append(turn)

            if len(self.tracking[nominated_by]) > self.recency:
                self.tracking[nominated_by].pop(0)

            assert len(self.tracking[nominated_by]) <= self.recency

    def get_recent_turns_nomination_made(self, player: "SanitizedPlayer") -> List[int]:
        """
        Get the last n turns when the given player made a nomination, where n
        is the recency parameter given to this NominationTracker.
        """
        return self.tracking.get(player, [])
