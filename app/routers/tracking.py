from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.dependencies import get_reply_tracker, get_sheets_client, verify_api_key
from app.services.reply_tracker import ReplyTracker
from app.services.sheets_client import GoogleSheetsClient

router = APIRouter(prefix="/tracking", tags=["Tracking"], dependencies=[Depends(verify_api_key)])


@router.get("/check-replies")
async def check_replies(tracker: ReplyTracker = Depends(get_reply_tracker)) -> dict[str, Any]:
    """
    Runs inbox check, classifies new replies
    and updates statuses in Google Sheets.
    """
    stats = await tracker.process_and_tag()
    return stats


@router.get("/leads")
async def get_leads(
    status: str | None = Query(
        None, description="Filter by status (Pending/Sent/Replied/Interested/NotInterested)"
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sheets: GoogleSheetsClient = Depends(get_sheets_client),
) -> list[dict[str, Any]]:
    """List of all leads with filters."""
    return await sheets.get_all_contacts(status=status, limit=limit, offset=offset)


@router.patch("/leads/{lead_id}/tag")
async def update_lead_tag(
    lead_id: str,
    tag: str = Body(..., embed=True),
    sheets: GoogleSheetsClient = Depends(get_sheets_client),
) -> dict[str, Any]:
    """Manual update of lead tag."""
    updated = await sheets.update_contact_tag(lead_id, tag)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated
