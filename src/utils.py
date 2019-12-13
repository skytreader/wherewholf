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

    def __init__(self, items: Mapping[Any, int]):
        self.internal_counter = Counter(items)
        self.value_tie_index: ValueIndex = ValueIndex()

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
