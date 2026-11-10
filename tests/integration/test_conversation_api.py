"""
Integration tests for the Chat REST API endpoints.

Covers Conversation CRUD, cursor pagination, message history retrieval,
feedback upsert, validation, and multi-tenant user isolation.
"""
from uuid import UUID, uuid4

import httpx
import pytest

from api.dependencies import DEV_USER_ID
from tests.conftest import OTHER_USER_ID


@pytest.mark.asyncio
async def test_conversation_api_crud(client: httpx.AsyncClient):
    """Verify conversation creation, retrieval, listing, updating, and soft deletion."""
    # 1. Create conversation with custom title
    create_res = await client.post("/conversations", json={"title": "Q3 Sales Review"})
    assert create_res.status_code == 201
    data = create_res.json()
    conv_id = data["id"]
    assert data["title"] == "Q3 Sales Review"
    assert data["title_source"] == "user"
    assert data["status"] == "active"
    assert data["is_pinned"] is False
    assert data["generation_status"] == "idle"

    # 2. Get conversation
    get_res = await client.get(f"/conversations/{conv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == conv_id

    # 3. Update conversation (pin and rename)
    patch_res = await client.patch(
        f"/conversations/{conv_id}",
        json={"title": "Q3 Sales & Financials", "is_pinned": True},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Q3 Sales & Financials"
    assert patch_res.json()["is_pinned"] is True

    # 4. List conversations
    list_res = await client.get("/conversations", params={"limit": 10})
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(c["id"] == conv_id for c in items)

    # 5. Delete conversation
    del_res = await client.delete(f"/conversations/{conv_id}")
    assert del_res.status_code == 204

    # 6. Verify 404 after soft-delete
    get_deleted = await client.get(f"/conversations/{conv_id}")
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_conversation_user_isolation(client: httpx.AsyncClient):
    """Verify that User A cannot view or manipulate User B's conversations."""
    # Create conversation as DEV_USER_ID
    create_res = await client.post("/conversations", json={"title": "Private Notes"})
    assert create_res.status_code == 201
    conv_id = create_res.json()["id"]

    # Attempt to read as OTHER_USER_ID
    other_headers = {"X-User-ID": str(OTHER_USER_ID)}
    get_res = await client.get(f"/conversations/{conv_id}", headers=other_headers)
    assert get_res.status_code == 404

    # Attempt to patch as OTHER_USER_ID
    patch_res = await client.patch(
        f"/conversations/{conv_id}",
        json={"title": "Hacked"},
        headers=other_headers,
    )
    assert patch_res.status_code == 404

    # Attempt to delete as OTHER_USER_ID
    del_res = await client.delete(f"/conversations/{conv_id}", headers=other_headers)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_message_history_cursor_pagination(client: httpx.AsyncClient):
    """Verify cursor pagination of message history."""
    # Create conversation and stream two dialogue turns
    create_res = await client.post("/conversations", json={"title": "Dialogue History"})
    conv_id = create_res.json()["id"]

    # Turn 1
    t1_res = await client.post(
        f"/conversations/{conv_id}/messages",
        json={"content": "Turn 1 question"},
    )
    assert t1_res.status_code == 200

    # Turn 2
    t2_res = await client.post(
        f"/conversations/{conv_id}/messages",
        json={"content": "Turn 2 question"},
    )
    assert t2_res.status_code == 200

    # Retrieve all messages (should have 4 messages: user1, asst1, user2, asst2)
    history_res = await client.get(f"/conversations/{conv_id}/messages", params={"limit": 10})
    assert history_res.status_code == 200
    all_msgs = history_res.json()["messages"]
    assert len(all_msgs) == 4
    assert [m["sequence_number"] for m in all_msgs] == [1, 2, 3, 4]

    # Cursor pagination: fetch with limit=2 (should get sequences 1 and 2, next_cursor=2)
    page1_res = await client.get(f"/conversations/{conv_id}/messages", params={"limit": 2})
    assert page1_res.status_code == 200
    p1_data = page1_res.json()
    assert len(p1_data["messages"]) == 2
    assert p1_data["has_more"] is True
    assert p1_data["next_cursor"] == 2

    # Fetch page 2 using cursor_sequence=2 (should get sequences 3 and 4)
    page2_res = await client.get(
        f"/conversations/{conv_id}/messages",
        params={"cursor_sequence": 2, "limit": 2},
    )
    assert page2_res.status_code == 200
    p2_data = page2_res.json()
    assert len(p2_data["messages"]) == 2
    assert [m["sequence_number"] for m in p2_data["messages"]] == [3, 4]


@pytest.mark.asyncio
async def test_feedback_api_submission_and_rules(client: httpx.AsyncClient):
    """Verify feedback submission, validation rules, and update semantics."""
    # Create conversation and turn
    conv_res = await client.post("/conversations", json={"title": "Feedback Test"})
    conv_id = conv_res.json()["id"]

    t_res = await client.post(
        f"/conversations/{conv_id}/messages",
        json={"content": "Query for feedback"},
    )
    assert t_res.status_code == 200

    # Get assistant message ID
    hist_res = await client.get(f"/conversations/{conv_id}/messages")
    messages = hist_res.json()["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    asst_msg = next(m for m in messages if m["role"] == "assistant")

    # 1. Feedback targeting user message is rejected (HTTP 400)
    user_target_res = await client.post(
        f"/conversations/{conv_id}/messages/{user_msg['id']}/feedback",
        json={
            "rating": 5,
        },
    )
    assert user_target_res.status_code == 400
    assert "assistant" in user_target_res.json()["detail"].lower()

    # 2. Feedback with invalid rating (e.g. 10) is rejected by schema (HTTP 422)
    invalid_rating_res = await client.post(
        f"/conversations/{conv_id}/messages/{asst_msg['id']}/feedback",
        json={
            "rating": 10,
        },
    )
    assert invalid_rating_res.status_code == 422

    # 3. Valid feedback submission (5 stars) succeeds
    fb_res = await client.post(
        f"/conversations/{conv_id}/messages/{asst_msg['id']}/feedback",
        json={
            "rating": 5,
            "comment": "Accurate response",
        },
    )
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["rating"] == 5
    assert fb_data["comment"] == "Accurate response"

    # 4. Upserting feedback to 3 stars updates the existing record
    update_fb_res = await client.post(
        f"/conversations/{conv_id}/messages/{asst_msg['id']}/feedback",
        json={
            "rating": 3,
            "comment": "Found an issue later",
        },
    )
    assert update_fb_res.status_code == 200
    updated_data = update_fb_res.json()
    assert updated_data["id"] == fb_data["id"]
    assert updated_data["rating"] == 3
    assert updated_data["comment"] == "Found an issue later"
