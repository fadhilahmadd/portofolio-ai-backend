import urllib.parse
import re

def create_mailto_link(email: str, subject: str, body: str) -> str:
    """
    Creates a URL-encoded mailto link.
    """
    return f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

def remove_markdown(text: str) -> str:
    """
    Removes markdown characters from text to make it clean for TTS.
    - Removes bold, italics, headers, and list markers.
    """
    # Remove bold and italics
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Remove headers
    text = re.sub(r'#+\s', '', text)
    # Remove list item markers
    text = re.sub(r'[\*\-]\s', '', text)
    # Remove code blocks
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
    # Remove links
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text