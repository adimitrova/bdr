from dataclasses import dataclass


@dataclass
class Sender:
    port: int
    smtp_server: str
    sender_email: str
    password: str

    def __repr__(self):
        return f"Sender(smtp_server={self.smtp_server}, sender_email={self.sender_email}, port={self.port})"
