from src.market import Market
from src.type import Type
from src.utils import get_a_spark_session

from src.gamer import Gamer
from src.notifier import Notifier


def test_run():
    ...


def run():
    region_id = 10000002        # The Forge
    sc = get_a_spark_session()
    notifier = Notifier()
    the_drama_llama = Gamer(name="Drama Llama", email_address="trance.energy666@gmail.com", notifier=notifier)
    less_drama_llama = Gamer(name="Less Drama Llama", email_address="trance.energy666@gmail.com", notifier=notifier)
    jakob = Gamer(name="Jakob", email_address="trance.energy666@gmail.com", notifier=notifier)
    market = Market(region_id=region_id, spark_context=sc, num_of_types_to_fetch=50)
    market.add_trader(the_drama_llama)
    market.add_trader(less_drama_llama)
    market.add_trader(jakob)
    market.track_item_prices()
