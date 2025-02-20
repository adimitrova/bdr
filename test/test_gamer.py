import pytest
from unittest.case import TestCase
from unittest.mock import patch, MagicMock, call, mock_open, create_autospec

from src.gamer import Gamer
from src.notifier import Notifier


@patch('src.notifier.Notifier')
def test_instantiate_gamer(mock_notifier):
    # arrange & act
    gamer = Gamer(name="Llama", email_address="llama@gmail.com", notifier=mock_notifier)

    # assert
    assert isinstance(gamer, Gamer)


@patch('src.notifier.Notifier.parse_config')
@patch('src.notifier.yaml.safe_load')
def test_notify(mock_yaml, mock_parse_config, mock_sender, caplog):
    # arrange & act

    sender = mock_sender
    mock_parse_config.return_value = sender
    open_mock = MagicMock()
    with patch('src.notifier.open',
               side_effect=mock_open(mock=open_mock)):
        n = Notifier()
        gamer = Gamer(name="Llama", email_address="llama@gmail.com", notifier=n)

    # assert
    print(caplog.text)
    assert True  # FIXME
