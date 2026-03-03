# Coaching Session Workflow Guide

**Version:** 3.0  
**Last Updated:** February 12, 2026  
**Status:** Active

[← Back to Backend Integration](./backend-integration-unified-ai.md)

---

## Purpose

This guide explains the coaching journey in human terms: how a session starts, pauses, resumes, and completes from a user experience perspective.

**Technical API and payload contracts live in one place only:**
- `docs/shared/Specifications/ai-user/backend-integration-unified-ai.md`
- `docs/shared/Specifications/eventbridge/async-coaching-message-events.md`

---

## Session Lifecycle

Coaching sessions move through these states:

- **ACTIVE**: User can continue messaging
- **PAUSED**: User paused or frontend treats an idle session as paused on reopen
- **COMPLETED**: Conversation is done and results are available
- **CANCELLED**: User cancelled the session
- **ABANDONED**: Older session replaced by a fresh start

The main lifecycle principle:
- **Start means new conversation**
- **Resume means continue existing conversation**

---

## User Journey

### 1) User opens coaching

The frontend checks if there is an existing session and whether there is a conflict with another user in the tenant.

- If no session exists, user starts fresh.
- If a resumable session exists, user chooses to resume or start new.
- If there is a conflict, the UI blocks entry and shows guidance.

### 2) User sends a message

Message handling is asynchronous:

- The API immediately accepts the request and returns a job identifier.
- The backend processes the message in the background.
- Frontend receives the result by WebSocket, or polling fallback.

This avoids request timeouts on long model responses and keeps the UI responsive.

### 3) Conversation continues or ends

Each completed message indicates whether the conversation is final:

- If not final, the user keeps chatting.
- If final, the UI presents extracted results and closes or transitions the session.

### 4) User pauses, resumes, or starts over

- **Pause** explicitly blocks additional messages until resume.
- **Resume** re-enters the existing session context.
- **Start new** creates a fresh session and retires the old one.

---

## Idle and Pause Behavior

Idle time is treated as a UX signal, not a hard failure for active work:

- A user who still has an active context can continue conversation flow.
- On re-entry, frontend can present the session as paused and offer resume/new options.

---

## Operational Notes

- Sessions have TTL-based cleanup.
- Async jobs are temporary and used for status tracking and delivery.
- Frontend should treat job completion events idempotently.

---

## Quick Checklist

- Frontend checks session status before opening coaching UI
- Frontend handles resume vs start-new explicitly
- Message send uses async job flow
- Completion handling uses finality flag + result payload
- Pause/resume actions are reflected in UI state
