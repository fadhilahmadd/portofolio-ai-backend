# tests/test_chat_service.py

import sys
import os
import pytest

# Add the project root to the Python path to resolve the ModuleNotFoundError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.chat_service import ChatService
from app.core.utils import create_mailto_link
from app.api.v1.schemas.chat import UserIntent

# Mark the test as an asyncio test
@pytest.mark.asyncio
async def test_get_user_intent_recruiter():
    """
    Tests if the _get_user_intent method correctly identifies a recruiter's message.
    """
    # Arrange
    chat_service = ChatService()
    recruiter_message = "I'm hiring for a software engineer role and came across Fadhil's profile."

    # Act
    intent = await chat_service._get_user_intent(recruiter_message)

    # Assert
    assert intent == UserIntent.RECRUITER

@pytest.mark.asyncio
async def test_get_user_intent_general_inquiry():
    """
    Tests if the _get_user_intent method correctly identifies a general inquiry.
    """
    # Arrange
    chat_service = ChatService()
    general_message = "Tell me about Fadhil's projects."

    # Act
    intent = await chat_service._get_user_intent(general_message)

    # Assert
    assert intent == UserIntent.GENERAL_INQUIRY

def test_create_mailto_link():
    """
    Tests if the create_mailto_link function generates a correct mailto link.
    """
    # Arrange
    email = "test@example.com"
    subject = "Job Opportunity"
    body = "Hello, I'd like to discuss a role."
    expected_link = "mailto:test@example.com?subject=Job%20Opportunity&body=Hello%2C%20I%27d%20like%20to%20discuss%20a%20role."

    # Act
    generated_link = create_mailto_link(email, subject, body)

    # Assert
    assert generated_link == expected_link
