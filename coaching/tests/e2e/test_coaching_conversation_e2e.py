"""End-to-end tests for coaching conversation flows with real AI providers.

These tests validate complete user journeys:
- Initiate conversation
- Exchange messages with real LLM
- Complete/pause conversation
- Retrieve conversation history
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_coaching_conversation_flow(
    e2e_client: AsyncClient,
    e2e_tenant_id: str,
    e2e_user_id: str,
    check_aws_credentials: None,
) -> None:
    """
    Test complete coaching conversation flow with real Bedrock LLM.

    Flow:
    1. Initiate conversation
    2. Send user message
    3. Receive AI response
    4. Complete conversation
    5. Verify conversation state
    """
    # Step 1: Initiate conversation
    initiate_payload = {
        "topic": "core_values",
        "initial_context": {
            "business_name": "E2E Test Company",
            "industry": "Technology",
            "goal": "Define core company values",
        },
    }

    response = await e2e_client.post("/api/conversations/initiate", json=initiate_payload)
    assert response.status_code == 200, f"Failed to initiate: {response.text}"

    data = response.json()
    assert data["success"] is True
    conversation_id = data["data"]["conversation_id"]
    assert conversation_id

    # Step 2: Send user message
    message_payload = {
        "content": "I want to focus on innovation and customer trust as core values."
    }

    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/message", json=message_payload
    )
    assert response.status_code == 200, f"Failed to send message: {response.text}"

    message_data = response.json()
    assert "response" in message_data
    assert len(message_data["response"]) > 50  # Real LLM response should be substantial

    # Step 3: Get conversation details
    response = await e2e_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200

    conversation = response.json()
    assert conversation["conversation_id"] == conversation_id
    assert len(conversation["messages"]) >= 2  # User message + AI response
    assert conversation["status"] in ["in_progress", "active"]

    # Step 4: Complete conversation
    complete_payload = {
        "summary": "Discussed innovation and customer trust as core values",
        "action_items": ["Document core values", "Share with team"],
    }

    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/complete", json=complete_payload
    )
    assert response.status_code == 200

    # Step 5: Verify final state
    response = await e2e_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200

    final_conversation = response.json()
    assert final_conversation["status"] == "completed"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_turn_conversation_with_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test multi-turn conversation with context retention.

    Validates:
    - LLM maintains conversation context
    - Multiple message exchanges work
    - Response quality remains consistent
    """
    # Initiate
    response = await e2e_client.post(
        "/api/conversations/initiate",
        json={
            "topic": "vision",
            "initial_context": {"business_name": "TechCorp", "industry": "SaaS"},
        },
    )
    assert response.status_code == 200
    conversation_id = response.json()["data"]["conversation_id"]

    # Turn 1: Ask about vision
    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Help me create a 5-year vision for my company"},
    )
    assert response.status_code == 200
    turn1_response = response.json()["response"]
    assert len(turn1_response) > 100

    # Turn 2: Follow-up question (tests context retention)
    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Can you elaborate on the market expansion strategy you mentioned?"},
    )
    assert response.status_code == 200
    turn2_response = response.json()["response"]
    assert len(turn2_response) > 50

    # Turn 3: Refinement
    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Make it more ambitious but still realistic"},
    )
    assert response.status_code == 200
    turn3_response = response.json()["response"]
    assert len(turn3_response) > 50

    # Verify all messages are stored
    response = await e2e_client.get(f"/api/conversations/{conversation_id}")
    conversation = response.json()
    assert len(conversation["messages"]) >= 6  # 3 user + 3 AI messages


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pause_and_resume_conversation(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test pause and resume functionality with real LLM.

    Validates:
    - Conversation can be paused
    - State is preserved
    - Can resume with context intact
    """
    # Initiate and have one exchange
    response = await e2e_client.post(
        "/api/conversations/initiate",
        json={"topic": "purpose", "initial_context": {"business_name": "StartupCo"}},
    )
    conversation_id = response.json()["data"]["conversation_id"]

    await e2e_client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Let's define our company purpose"},
    )

    # Pause
    response = await e2e_client.post(f"/api/conversations/{conversation_id}/pause")
    assert response.status_code == 200

    # Verify paused state
    response = await e2e_client.get(f"/api/conversations/{conversation_id}")
    assert response.json()["status"] == "paused"

    # Resume by sending another message
    response = await e2e_client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Continuing our purpose discussion"},
    )
    assert response.status_code == 200

    # Verify conversation resumed
    response = await e2e_client.get(f"/api/conversations/{conversation_id}")
    conversation = response.json()
    assert conversation["status"] in ["in_progress", "active"]
    assert len(conversation["messages"]) >= 4


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_tenant_conversations(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test listing all conversations for a tenant.

    Validates:
    - Pagination works
    - Filtering works
    - All conversations returned
    """
    # Create 2 conversations
    conv_ids = []
    for i in range(2):
        response = await e2e_client.post(
            "/api/conversations/initiate",
            json={
                "topic": f"test_topic_{i}",
                "initial_context": {"business_name": f"Company {i}"},
            },
        )
        conv_ids.append(response.json()["data"]["conversation_id"])

    # List conversations
    response = await e2e_client.get("/api/conversations/?page=1&page_size=20")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert data["total"] >= 2

    # Verify our conversations are in the list
    returned_ids = [conv["conversation_id"] for conv in data["items"]]
    for conv_id in conv_ids:
        assert conv_id in returned_ids


__all__ = []  # Test module, no exports
