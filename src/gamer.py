from uuid import uuid4
from src.notifier import Notifier
from src.type import Type


class Gamer:
    def __init__(self, name: str, email_address: str, notifier: Notifier):
        self.id = uuid4()
        self.name = name
        self.email_address = email_address
        self.notifier = notifier

    def notify(self, market_id: str, type_obj: Type):
        self.notifier.notify(market_id=market_id, type_obj=type_obj, recipient=self)
