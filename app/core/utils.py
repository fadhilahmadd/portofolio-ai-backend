import urllib.parse

def create_mailto_link(email: str, subject: str, body: str) -> str:
    """
    Creates a URL-encoded mailto link.
    """
    return f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
