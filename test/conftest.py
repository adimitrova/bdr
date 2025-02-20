import subprocess
from collections import namedtuple
from unittest.mock import patch

from pytest import fixture
from src.notifier import Notifier
from src.sender import Sender


@fixture(scope='function')
def mock_sender():
    return Sender(
        smtp_server="smtp.google.com",
        port=465,
        sender_email="llama@gmail.com",
        password="llama_password"
    )


@fixture(scope='function')
def sample_api_sell_data():
    return {
        "duration": 90,
        "is_buy_order": False,
        "issued": "2025-02-09T19:44:14Z",
        "location_id": 60003760,
        "min_volume": 1,
        "order_id": 6983462286,
        "price": 5500000.0,
        "range": "region",
        "system_id": 30000142,
        "type_id": 17328,
        "volume_remain": 57,
        "volume_total": 101
    }
