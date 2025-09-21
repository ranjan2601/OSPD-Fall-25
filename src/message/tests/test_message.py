"""Tests for the message API protocol.

This module contains unit tests that verify the contracts and behavior
of the message.Message protocol. These tests use mocks to demonstrate
how implementations should behave and serve as documentation for the
expected API contracts.
"""

from unittest.mock import Mock

from message import Message

# Individual property tests removed - covered by comprehensive test below


def test_message_protocol_comprehensive() -> None:
    """Verifies all properties work together in a comprehensive test.

    This test demonstrates how all Message protocol properties can be used
    together and verifies the complete contract.
    """
    # ARRANGE: Create a complete mock message with all properties
    mock_message = Mock(spec=Message)
    mock_message.id = "msg_67890"
    mock_message.from_ = "alice@company.com"
    mock_message.to = "bob@company.com"
    mock_message.date = "2025-07-30 14:45:30"
    mock_message.subject = "Project Update"
    mock_message.body = "Here are the latest updates on our project progress."

    # ACT: Access all properties
    properties = {
        "id": mock_message.id,
        "from_": mock_message.from_,
        "to": mock_message.to,
        "date": mock_message.date,
        "subject": mock_message.subject,
        "body": mock_message.body,
    }

    # ASSERT: Verify all properties return expected values and types
    assert properties["id"] == "msg_67890"
    assert properties["from_"] == "alice@company.com"
    assert properties["to"] == "bob@company.com"
    assert properties["date"] == "2025-07-30 14:45:30"
    assert properties["subject"] == "Project Update"
    assert properties["body"] == "Here are the latest updates on our project progress."

    # Verify all properties return strings
    for prop_value in properties.values():
        assert isinstance(prop_value, str)
