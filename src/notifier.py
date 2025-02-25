import os
import random
import smtplib
import ssl
from typing import TYPE_CHECKING
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTPRecipientsRefused
from textwrap import dedent

import yaml

from src.sender import Sender
from src.type import Type
from src.utils import get_logger
if TYPE_CHECKING:
    from src.gamer import Gamer


DEF_RECIPIENT_EMAIL = "trance.energy666@gmail.com"
DEF_RECIPIENT_NAME = random.choice([
    "Alice", "Bob", "Charlie", "David", "Emma",
    "Fiona", "George", "Hannah", "Isaac", "Julia",
    "Kevin", "Liam", "Mia", "Noah", "Olivia",
    "Peter", "Quinn", "Rachel", "Samuel", "Taylor"
])
CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.absolute(), "vault", "config.yaml")
logger = get_logger('config')


class Notifier:
    def __init__(self, config_path: str = CONFIG_FILE_PATH):
        self.config_path: str = config_path
        self.sender: Sender = self.parse_config()
        logger.info("Created notifier: %s", self.__repr__())

    def parse_config(self) -> Sender:
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f.read())
            return Sender(
                smtp_server=config_data.get("smtp_server"),
                port=int(config_data.get("port")),
                sender_email=config_data.get("sender_email"),
                password=config_data.get("password")
            )

    def notify(self, market_id: str, type_obj: Type, recipient: "Gamer") -> None:
        logger.info(f"Notifying user with email {recipient.email_address} about low price of item..")

        text_subtype = 'plain'
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host=self.sender.smtp_server, port=self.sender.port, context=context) as server:
                logger.info("Making a new connection to the Sender's email")
                server.login(self.sender.sender_email, self.sender.password)
                recipient_email = recipient.email_address
                try:
                    logger.info("Verifying recipient's email..")
                    server.verify(recipient.email_address)
                except smtplib.SMTPServerDisconnected:
                    logger.debug(
                        f"Connection unexpectedly closed during email validation for {recipient.email_address}")
                # TODO: change the name in the actual message, using random name now
                message_body = dedent(f"""
Hi {recipient.name},

We want to let you know that the current price for item/type {type_obj.name} with ID {type_obj.id} and market_id {market_id} is currently 30% below average. 
You may want to head online and stock up!

Best regards,
The Eve Online Team

P.S. This is an automated email. Please do not reply.
                    """.strip())
                msg = MIMEText(message_body, text_subtype)
                msg['Subject'] = 'Eve Online price drop'
                msg['From'] = self.sender.sender_email
                msg['To'] = recipient.email_address
                try:
                    logger.info(
                        f"Sending an email to {recipient.name} with email {recipient.email_address} ")
                    server.sendmail(from_addr=self.sender.sender_email,
                                    to_addrs=recipient.email_address,
                                    msg=msg.as_string())  # TODO: UNCOMMENT TO SEND EMAILS

                    logger.info("Email sent successfully.")
                except smtplib.SMTPException as err:
                    logger.error(
                        f"SMTP error #{err.errno}: unable to send email to user {recipient.name}, "
                        f"email {recipient.email_address} about type {type.name} with ID {type.id} "
                        f"and market_id {market_id}. Error: {err}")
                except Exception as err:
                    logger.error(
                        f"Unknown exception occurred, preventing the sending of email to user {recipient.name}, "
                        f"email {recipient.email_address} about type {type.name} with ID {type.id} "
                        f"and market_id {market_id}. Error: {err}")
        except ConnectionRefusedError as err:
            logger.info(f"Error while trying to connect via SMTP: {err}")

    def __repr__(self):
        return repr(
            f'Notifier({self.sender})')
