from abc import ABC, abstractmethod
from collections import Counter
from typing import List, Dict


class Subscriber(ABC):

    @abstractmethod
    def recv_message(self, message_topic: str, message: str):
        pass

class StatSubscriber(Subscriber):

    def  __init__(self):
        self.event_tally: Counter = Counter()

    def recv_message(self, message_topic: str, message):
        self.event_tally.update([message_topic])

class PubSubBroker(object):

    def __init__(self):
        self.subscribers: List["Subscriber"] = []
    
    def broadcast_message(self, message_topic: str, message: str):
        for subscriber in self.subscribers:
            subscriber.recv_message(message_topic, message)
