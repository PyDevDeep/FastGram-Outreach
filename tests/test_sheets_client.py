"""Tests for sheets_client module."""

import asyncio
from unittest.mock import MagicMock, patch

import gspread
import pytest

from app.services.sheets_client import GoogleSheetsClient

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.google_application_credentials = "/fake/credentials.json"
    settings.google_sheets_id = "fake_sheet_id_123"
    return settings


@pytest.fixture
def mock_gspread_worksheet():
    """Mocks a gspread Worksheet with default headers and data."""
    worksheet = MagicMock()

    # За замовчуванням повертаємо заголовки
    worksheet.row_values.return_value = [
        "Instagram Username",
        "Instagram User ID",
        "Message Template",
        "Status",
        "Sent Timestamp",
        "Reply Text",
        "Tag",
        "Reply Timestamp",
    ]

    # За замовчуванням порожні записи
    worksheet.get_all_records.return_value = []

    return worksheet


@pytest.fixture
def mock_gspread_client(mock_gspread_worksheet):
    """Mocks gspread.Client."""
    client = MagicMock()

    # Mocking spreadsheet
    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = mock_gspread_worksheet

    client.open_by_key.return_value = spreadsheet
    return client


@pytest.fixture
def sheets_client(mock_settings, mock_gspread_client):
    """GoogleSheetsClient instance with fully mocked dependencies."""
    with (
        patch("app.services.sheets_client.get_settings", return_value=mock_settings),
        patch("app.services.sheets_client.Credentials.from_service_account_file"),
        patch("app.services.sheets_client.gspread.authorize", return_value=mock_gspread_client),
    ):
        client = GoogleSheetsClient()
        yield client


# ==========================================
# TESTS: Initialization
# ==========================================


class TestGoogleSheetsClientInit:
    def test_init_success(self, mock_settings, mock_gspread_client):
        """Should initialize credentials and authorize client."""
        with (
            patch("app.services.sheets_client.get_settings", return_value=mock_settings),
            patch("app.services.sheets_client.Credentials.from_service_account_file") as mock_creds,
            patch(
                "app.services.sheets_client.gspread.authorize", return_value=mock_gspread_client
            ) as mock_auth,
        ):
            client = GoogleSheetsClient()

            mock_creds.assert_called_once_with(
                "/fake/credentials.json",
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
            mock_auth.assert_called_once()
            assert client.sheet == mock_gspread_client.open_by_key.return_value

    def test_init_failure_raises_runtime_error(self, mock_settings):
        """Should catch exceptions during auth and raise RuntimeError."""
        with (
            patch("app.services.sheets_client.get_settings", return_value=mock_settings),
            patch(
                "app.services.sheets_client.Credentials.from_service_account_file",
                side_effect=Exception("Auth error"),
            ),
            pytest.raises(RuntimeError, match="Database initialization failed"),
        ):
            GoogleSheetsClient()


# ==========================================
# TESTS: Fetching Contacts
# ==========================================


class TestGoogleSheetsClientFetch:
    @pytest.mark.asyncio
    async def test_get_pending_contacts(self, sheets_client, mock_gspread_worksheet):
        """Should return only contacts with 'Pending' status and add _row_index."""
        mock_gspread_worksheet.get_all_records.return_value = [
            {"Instagram Username": "u1", "Status": "Pending"},
            {"Instagram Username": "u2", "Status": "Sent"},
            {"Instagram Username": "u3", "Status": "pending "},  # Should handle case/spaces
            {"Instagram Username": "u4", "Status": ""},
        ]

        result = await sheets_client.get_pending_contacts()

        assert len(result) == 2
        assert result[0]["Instagram Username"] == "u1"
        assert result[0]["_row_index"] == 2  # Row 1 is header, index 0 is row 2

        assert result[1]["Instagram Username"] == "u3"
        assert result[1]["_row_index"] == 4

    @pytest.mark.asyncio
    async def test_get_sent_contacts(self, sheets_client, mock_gspread_worksheet):
        """Should return only contacts with 'Sent' status."""
        mock_gspread_worksheet.get_all_records.return_value = [
            {"Instagram Username": "u1", "Status": "Sent"},
            {"Instagram Username": "u2", "Status": "Pending"},
        ]

        result = await sheets_client.get_sent_contacts()

        assert len(result) == 1
        assert result[0]["_row_index"] == 2

    @pytest.mark.asyncio
    async def test_get_all_contacts_pagination(self, sheets_client, mock_gspread_worksheet):
        """Should apply limit and offset correctly."""
        records = [{"id": i, "Status": "Pending"} for i in range(10)]
        mock_gspread_worksheet.get_all_records.return_value = records

        result = await sheets_client.get_all_contacts(limit=3, offset=2)

        assert len(result) == 3
        assert result[0]["id"] == 2
        assert result[2]["id"] == 4

    @pytest.mark.asyncio
    async def test_get_all_contacts_with_status_filter(self, sheets_client, mock_gspread_worksheet):
        """Should filter by status before applying pagination."""
        mock_gspread_worksheet.get_all_records.return_value = [
            {"id": 1, "Status": "Sent"},
            {"id": 2, "Status": "Failed"},
            {"id": 3, "Status": "Sent"},
        ]

        result = await sheets_client.get_all_contacts(status="sent")
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 3


# ==========================================
# TESTS: Updating Contacts
# ==========================================


class TestGoogleSheetsClientUpdate:
    @pytest.mark.asyncio
    async def test_update_contact_status_success(self, sheets_client, mock_gspread_worksheet):
        """Should call update_cells with correct coordinates and values."""
        success = await sheets_client.update_contact_status(
            row_index=5, status="Sent", timestamp="2023-01-01"
        )

        assert success is True
        mock_gspread_worksheet.update_cells.assert_called_once()

        # Перевіряємо аргументи виклику update_cells
        args = mock_gspread_worksheet.update_cells.call_args[0][0]
        assert len(args) == 2

        # Headers: ["Instagram Username", "Instagram User ID", "Message Template", "Status", "Sent Timestamp", ...]
        # Status = col 4, Sent Timestamp = col 5
        assert args[0].row == 5
        assert args[0].col == 4
        assert args[0].value == "Sent"

        assert args[1].row == 5
        assert args[1].col == 5
        assert args[1].value == "2023-01-01"

    @pytest.mark.asyncio
    async def test_update_contact_status_missing_columns(
        self, sheets_client, mock_gspread_worksheet
    ):
        """Should fail if required columns are not found in headers."""
        mock_gspread_worksheet.row_values.return_value = ["Wrong", "Headers"]

        success = await sheets_client.update_contact_status(
            row_index=5, status="Sent", timestamp="Time"
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_add_reply_data_success(self, sheets_client, mock_gspread_worksheet):
        """Should update 4 cells for reply data."""
        success = await sheets_client.add_reply_data(
            row_index=3, reply_text="Yes", tag="Positive", reply_timestamp="time"
        )

        assert success is True
        args = mock_gspread_worksheet.update_cells.call_args[0][0]
        assert len(args) == 4
        # Перевірка що статус змінився на "Replied" (Status is col 4)
        assert any(cell.col == 4 and cell.value == "Replied" for cell in args)
        # Tag is col 7
        assert any(cell.col == 7 and cell.value == "Positive" for cell in args)

    @pytest.mark.asyncio
    async def test_update_contact_tag_by_row_id(self, sheets_client, mock_gspread_worksheet):
        """Should locate row by index and update Tag."""
        mock_gspread_worksheet.get_all_records.return_value = [
            {"Instagram User ID": "u1"},
            {"Instagram User ID": "u2"},
        ]

        # lead_id = "3" implies row_index = 3 (second item)
        result = await sheets_client.update_contact_tag(lead_id="3", tag="Hot")

        assert result is not None
        assert result["Tag"] == "Hot"
        assert result["_row_index"] == 3

        args = mock_gspread_worksheet.update_cells.call_args[0][0]
        assert len(args) == 1
        assert args[0].row == 3
        assert args[0].value == "Hot"

    @pytest.mark.asyncio
    async def test_update_contact_tag_not_found(self, sheets_client, mock_gspread_worksheet):
        """Should return None if lead_id doesn't match any user."""
        mock_gspread_worksheet.get_all_records.return_value = [
            {"Instagram User ID": "u1"},
        ]

        result = await sheets_client.update_contact_tag(lead_id="nonexistent", tag="Hot")
        assert result is None
        mock_gspread_worksheet.update_cells.assert_not_called()
