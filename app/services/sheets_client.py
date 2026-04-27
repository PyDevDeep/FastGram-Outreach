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
