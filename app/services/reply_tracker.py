from typing import Any

from app.services.instagram_client import InstagramClient
from app.services.sheets_client import GoogleSheetsClient
from app.utils.logger import setup_logger

logger = setup_logger("reply_tracker")


class ReplyTracker:
    def __init__(
        self,
        instagram_client: InstagramClient,
        sheets_client: GoogleSheetsClient,
    ) -> None:
        self.ig_client = instagram_client
        self.sheets_client = sheets_client

        self.positive_keywords = [
            "yes",
            "interested",
            "tell me more",
            "sure",
            "send",
            "link",
            "how much",
            "ok",
            "okay",
        ]
        self.negative_keywords = [
            "no",
            "not interested",
            "stop",
            "unsubscribe",
            "remove",
            "don't",
            "do not",
        ]

    def classify_reply(self, message_text: str) -> str:
        """Визначення тегу на основі ключових слів."""
        if not message_text:
            return "Unclear"

        text = message_text.lower()
        is_pos = any(kw in text for kw in self.positive_keywords)
        is_neg = any(kw in text for kw in self.negative_keywords)

        if is_pos and not is_neg:
            return "Interested"
        if is_neg and not is_pos:
            return "NotInterested"

        return "Unclear"

    async def check_replies(self) -> list[dict[str, Any]]:
        """Перевіряє inbox на нові відповіді від контактів зі статусом Sent."""
        sent_contacts = await self.sheets_client.get_sent_contacts()
        if not sent_contacts:
            logger.info("No sent contacts found. Skipping reply check.")
            return []

        sent_map = {
            str(c.get("Instagram User ID")): c for c in sent_contacts if c.get("Instagram User ID")
        }

        # Кастуємо клієнт до Any, щоб Pylance Strict Mode ігнорував перевірку його атрибутів
        ig_any: Any = self.ig_client
        threads: list[Any] = await ig_any.get_direct_inbox(limit=20)
        new_replies: list[dict[str, Any]] = []

        client_api: Any = ig_any.client
        bot_id = str(getattr(client_api, "user_id", ""))

        for t in threads:
            # Явне приведення елемента ітерації до Any вирішує reportUnknownArgumentType
            thread: Any = t
            messages: list[Any] = getattr(thread, "messages", [])
            if not messages:
                continue

            last_msg: Any = messages[0]
            sender_id = str(getattr(last_msg, "user_id", ""))

            if sender_id == bot_id:
                continue

            if sender_id in sent_map:
                contact = sent_map[sender_id]
                new_replies.append(
                    {
                        "row_index": contact["_row_index"],
                        "user_id": sender_id,
                        "username": str(contact.get("Instagram Username", "Unknown")),
                        "message_text": str(getattr(last_msg, "text", "")),
                        "timestamp": str(getattr(last_msg, "timestamp", "")),
                    }
                )

        return new_replies

    async def process_and_tag(self) -> dict[str, int]:
        """Оркестрація перевірки та запису результатів у Sheets."""
        logger.info("Starting reply polling cycle")
        replies = await self.check_replies()

        stats = {"processed": len(replies), "interested": 0, "not_interested": 0, "unclear": 0}

        for reply in replies:
            tag = self.classify_reply(reply["message_text"])
            username = reply["username"]

            logger.info(f"Classified reply from {username} as {tag}")

            success = await self.sheets_client.add_reply_data(
                row_index=reply["row_index"],
                reply_text=reply["message_text"],
                tag=tag,
                reply_timestamp=reply["timestamp"],
            )

            if success:
                if tag == "Interested":
                    stats["interested"] += 1
                elif tag == "NotInterested":
                    stats["not_interested"] += 1
                else:
                    stats["unclear"] += 1

        logger.info(f"Reply polling cycle complete. Stats: {stats}")
        return stats
