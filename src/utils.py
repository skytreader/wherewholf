"""
Custom Counter class that takes ties into account in the `most_common` method.

Note that the reference implementation for this is the Counter class in CPython
3.7; 3.8 introduces syntactic changes that are not backwards-compatible to 3.7.
"""
from collections import Counter
from collections.abc import Iterable as IterableBaseClass

from typing import Any, Dict, Iterable, Iterator, Mapping, Set, Union


class ValueIndex(object):

    def __init__(self):
        self.value_index: Dict[int, List[Any]] = {}

    def update_index(self, value: int, reference: Any) -> None:
        if self.value_index.get(value):
            self.value_index[value].add(reference)
        else:
            self.value_index[value] = set((reference,))

    def remove_reference(self, index: int, reference: Any) -> None:
        # TODO Handle when reference does not exist in index.
        self.value_index[index].remove(reference)


class ValueTieCounter(Counter):

    # NOTE The reference implementation does not declare a `self` parameter but
    # splits `*args` via `self, *args = args` before `self` is even ever used.
    # I would've done the same except that it feels wrong.
    def __init__(self, *args, **kwds):
        self.internal_counter = Counter()
        self.internal_counter.update(*args, **kwds)
        self.value_tie_index: ValueIndex = ValueIndex()

        for k, v in self.internal_counter.items():
            self.value_tie_index.update_index(v, k)

        super(ValueTieCounter, self).__init__()

    def __getitem__(self, key: Any) -> int:
        return self.internal_counter[key]

    def elements(self) -> Iterator[Any]:
        return self.internal_counter.elements()

    def subtract(self, counts: Union[Dict, Iterable]) -> None:
        temp_counter: Counter = Counter(counts)

        for k, v in temp_counter.items():
            old_count = self.internal_counter[k]
            self.internal_counter[k] -= v
            self.value_tie_index.remove_reference(old_count, k)
            self.value_tie_index.update_index(
                self.internal_counter[k], k
            )
