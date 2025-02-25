from uuid import uuid4
from src.notifier import Notifier
from src.type import Type


class Gamer:
    def __init__(self, name: str, email_address: str, notifier: Notifier):
        self.id: uuid.UUID = uuid4()
        self.name: str = name
        self.email_address: str = email_address
        self.notifier: Notifier = notifier

    def notify(self, market_id: str, type_obj: Type) -> None:
        self.notifier.notify(market_id=market_id, type_obj=type_obj, recipient=self)
s