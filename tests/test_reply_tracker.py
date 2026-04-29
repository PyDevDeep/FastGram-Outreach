"""Tests for reply_tracker module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.reply_tracker import ReplyTracker


@pytest.fixture
def mock_ig_client():
    client = MagicMock()
    client.get_direct_inbox = AsyncMock()
    client.client.user_id = "bot123"
    return client


@pytest.fixture
def mock_sheets_client():
    client = MagicMock()
    client.get_sent_contacts = AsyncMock()
    client.add_reply_data = AsyncMock(return_value=True)
    return client


@pytest.fixture
def reply_tracker(mock_ig_client, mock_sheets_client):
    return ReplyTracker(instagram_client=mock_ig_client, sheets_client=mock_sheets_client)


class TestReplyTracker:
    def test_classify_reply(self, reply_tracker):
        # Positive
        assert reply_tracker.classify_reply("yes please tell me more") == "Interested"
        assert reply_tracker.classify_reply("sure send it") == "Interested"

        # Negative
        assert reply_tracker.classify_reply("no stop") == "NotInterested"
        assert reply_tracker.classify_reply("not interested") == "NotInterested"

        # Mixed (Negative takes priority now)
        assert reply_tracker.classify_reply("no but yes") == "NotInterested"

        # Unclear
        assert reply_tracker.classify_reply("what?") == "Unclear"
        assert reply_tracker.classify_reply("") == "Unclear"

    @pytest.mark.asyncio
    async def test_check_replies_no_sent_contacts(self, reply_tracker):
        reply_tracker.sheets_client.get_sent_contacts.return_value = []
        replies = await reply_tracker.check_replies()
        assert replies == []
        reply_tracker.ig_client.get_direct_inbox.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_replies_finds_match(self, reply_tracker):
        reply_tracker.sheets_client.get_sent_contacts.return_value = [
            {"Instagram User ID": "user1", "_row_index": 2, "Instagram Username": "john"}
        ]

        # Mock thread and message
        mock_msg = MagicMock()
        mock_msg.user_id = "user1"
        mock_msg.text = "Yes, interested"
        mock_msg.timestamp = "2023-10-01"

        mock_thread = MagicMock()
        mock_thread.messages = [mock_msg]

        reply_tracker.ig_client.get_direct_inbox.return_value = [mock_thread]

        replies = await reply_tracker.check_replies()

        assert len(replies) == 1
        assert replies[0]["user_id"] == "user1"
        assert replies[0]["message_text"] == "Yes, interested"
        assert replies[0]["row_index"] == 2

    @pytest.mark.asyncio
    async def test_check_replies_ignores_bot_messages(self, reply_tracker):
        reply_tracker.sheets_client.get_sent_contacts.return_value = [
            {"Instagram User ID": "user1", "_row_index": 2}
        ]

        # Message sent by bot itself
        mock_msg = MagicMock()
        mock_msg.user_id = "bot123"
        mock_thread = MagicMock()
        mock_thread.messages = [mock_msg]

        reply_tracker.ig_client.get_direct_inbox.return_value = [mock_thread]

        replies = await reply_tracker.check_replies()
        assert len(replies) == 0

    @pytest.mark.asyncio
    async def test_process_and_tag(self, reply_tracker):
        reply_tracker.check_replies = AsyncMock(
            return_value=[
                {"row_index": 2, "message_text": "yes", "username": "u1", "timestamp": "t1"},
                {"row_index": 3, "message_text": "no", "username": "u2", "timestamp": "t2"},
                {"row_index": 4, "message_text": "maybe", "username": "u3", "timestamp": "t3"},
            ]
        )

        stats = await reply_tracker.process_and_tag()

        assert stats["processed"] == 3
        assert stats["interested"] == 1
        assert stats["not_interested"] == 1
        assert stats["unclear"] == 1

        assert reply_tracker.sheets_client.add_reply_data.call_count == 3
