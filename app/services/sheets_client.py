import asyncio
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings
from app.utils.logger import setup_logger

logger = setup_logger("sheets_client")


class GoogleSheetsClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            self.credentials = Credentials.from_service_account_file(  # type: ignore[reportUnknownMemberType]
                self.settings.google_application_credentials, scopes=scopes
            )
            self.client = gspread.authorize(self.credentials)
            self.sheet = self.client.open_by_key(self.settings.google_sheets_id)
            logger.info(f"Connected to Google Sheets ID: {self.settings.google_sheets_id}")
        except Exception as e:
            logger.critical(f"Google Sheets Auth Failed. Check credentials.json and ID: {e}")
            raise RuntimeError("Database initialization failed") from e

    async def get_pending_contacts(self, sheet_name: str = "Contacts") -> list[dict[str, Any]]:
        """Отримує всі контакти зі статусом Pending."""

        def _fetch() -> list[dict[str, Any]]:
            worksheet = self.sheet.worksheet(sheet_name)
            records: list[dict[str, Any]] = worksheet.get_all_records()

            # gspread row index починається з 2 (через header)
            pending: list[dict[str, Any]] = []
            for i, row in enumerate(records):
                if str(row.get("Status", "")).strip().lower() == "pending":
                    row_data = dict(row)
                    row_data["_row_index"] = i + 2
                    pending.append(row_data)
            return pending

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"Error fetching pending contacts: {e}")
            return []

    async def update_contact_status(
        self, row_index: int, status: str, timestamp: str, sheet_name: str = "Contacts"
    ) -> bool:
        """Оновлює статус та час відправки для конкретного рядка."""

        def _update() -> None:
            worksheet = self.sheet.worksheet(sheet_name)
            headers = worksheet.row_values(1)

            try:
                status_col = headers.index("Status") + 1
                time_col = headers.index("Sent Timestamp") + 1
            except ValueError as e:
                raise ValueError("Required columns ('Status' or 'Sent Timestamp') not found") from e

            # Батч-оновлення для мінімізації API квот
            worksheet.update_cells(
                [
                    gspread.Cell(row=row_index, col=status_col, value=status),
                    gspread.Cell(row=row_index, col=time_col, value=timestamp),
                ]
            )

        try:
            await asyncio.to_thread(_update)
            logger.info(f"Row {row_index} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update status for row {row_index}: {e}")
            return False

    async def get_sent_contacts(self, sheet_name: str = "Contacts") -> list[dict[str, Any]]:
        """Отримує всі контакти зі статусом Sent (для трекінгу відповідей)."""

        def _fetch() -> list[dict[str, Any]]:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()

            sent: list[dict[str, Any]] = []
            for i, row in enumerate(records):
                if str(row.get("Status", "")).strip().lower() == "sent":
                    row_data = dict(row)
                    row_data["_row_index"] = i + 2
                    sent.append(row_data)
            return sent

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"Error fetching sent contacts: {e}")
            return []

    async def add_reply_data(
        self,
        row_index: int,
        reply_text: str,
        tag: str,
        reply_timestamp: str,
        sheet_name: str = "Contacts",
    ) -> bool:
        """Додавання даних про відповідь до рядка контакту."""

        def _update() -> None:
            worksheet = self.sheet.worksheet(sheet_name)
            headers = worksheet.row_values(1)

            try:
                text_col = headers.index("Reply Text") + 1
                tag_col = headers.index("Tag") + 1
                time_col = headers.index("Reply Timestamp") + 1
                status_col = headers.index("Status") + 1
            except ValueError as e:
                raise ValueError("Required reply columns not found in Sheets header") from e

            # Батч-оновлення
            worksheet.update_cells(
                [
                    gspread.Cell(row=row_index, col=status_col, value="Replied"),
                    gspread.Cell(row=row_index, col=text_col, value=reply_text),
                    gspread.Cell(row=row_index, col=tag_col, value=tag),
                    gspread.Cell(row=row_index, col=time_col, value=reply_timestamp),
                ]
            )

        try:
            await asyncio.to_thread(_update)
            logger.info(f"Row {row_index} updated with reply data (Tag: {tag})")
            return True
        except Exception as e:
            logger.error(f"Failed to add reply data for row {row_index}: {e}")
            return False

    async def get_all_contacts(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sheet_name: str = "Contacts",
    ) -> list[dict[str, Any]]:
        """Отримує список всіх лідів з можливістю фільтрації за статусом."""

        def _fetch() -> list[dict[str, Any]]:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            result: list[dict[str, Any]] = []

            for i, row in enumerate(records):
                if status and str(row.get("Status", "")).strip().lower() != status.lower():
                    continue
                row_data = dict(row)
                row_data["_row_index"] = i + 2
                result.append(row_data)

            return result[offset : offset + limit]

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            return []

    async def update_contact_tag(
        self, lead_id: str, tag: str, sheet_name: str = "Contacts"
    ) -> dict[str, Any] | None:
        """Оновлює тег для конкретного ліда (за Instagram User ID або Row ID)."""

        def _update() -> dict[str, Any] | None:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            headers = worksheet.row_values(1)

            try:
                tag_col = headers.index("Tag") + 1
            except ValueError as e:
                raise ValueError("Required column 'Tag' not found") from e

            row_index = None
            target_row = None
            for i, row in enumerate(records):
                # Підтримуємо пошук як за Instagram User ID, так і за Row ID (якщо він там є)
                if (
                    str(row.get("Instagram User ID", "")) == lead_id
                    or str(row.get("_row_index", "")) == lead_id
                    or str(i + 2) == lead_id
                ):
                    row_index = i + 2
                    target_row = dict(row)
                    target_row["_row_index"] = row_index
                    break

            if not row_index or not target_row:
                return None

            worksheet.update_cells([gspread.Cell(row=row_index, col=tag_col, value=tag)])
            target_row["Tag"] = tag
            return target_row

        try:
            updated = await asyncio.to_thread(_update)
            if updated:
                logger.info(f"Updated tag to {tag} for lead {lead_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update tag for lead {lead_id}: {e}")
            return None
