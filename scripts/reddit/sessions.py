from requests import Session

try:
    from .agents import get_agent
except ImportError:
    from agents import get_agent


class RandomUserAgentSession(Session):
    """Session class that uses a random user agent with each request."""

    def request(self, *args, **kwargs):
        self.headers.update({"User-Agent": get_agent()})
        return super().request(*args, **kwargs)
