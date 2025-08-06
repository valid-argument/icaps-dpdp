# https://docs.python.org/3/library/heapq.html

from heapq import heappush, heappop
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any=field(compare=False)

class PriorityQueue():
    def __init__(self):
        self.heap:list[PrioritizedItem] = []
    def push(self, priority, item):
        heappush(self.heap, PrioritizedItem(priority, item))
    def pop(self) -> PrioritizedItem:
        return heappop(self.heap)
    def is_empty(self):
        return 0 if self.heap else 1
    

# test
if __name__ == "__main__":
    my_queue = PriorityQueue()

    WISH = 'WISH'
    MUST = "MUST_HAVE"
    item1 = ('write code', {WISH: '2025-04-01', MUST: '2025-05-01'})
    prio1 = 5
    item2 = ('release product', {MUST: '2025-07-01'})
    prio2 = 7
    item3 = ('write spec', {MUST: '2025-01-01'})
    prio3 = 1
    item4 = ('create tests', {WISH: '2025-02-01', MUST: '2025-03-01'})
    prio4 = 1

    my_queue.push(prio1, item1)
    my_queue.push(prio2, item2)
    my_queue.push(prio3, item3)
    my_queue.push(prio4, item4)

    while not my_queue.is_empty():
        popped = my_queue.pop()
        print(popped.priority, popped.item)

    # expected result
    """     1 ('write spec', {'MUST_HAVE': '2025-01-01'})
            1 ('create tests', {'WISH': '2025-02-01', 'MUST_HAVE': '2025-03-01'})
            5 ('write code', {'WISH': '2025-04-01', 'MUST_HAVE': '2025-05-01'})  
            7 ('release product', {'MUST_HAVE': '2025-07-01'})                      """