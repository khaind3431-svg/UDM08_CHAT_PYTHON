"""Shared TCP protocol implementation for client/server communication.

The protocol uses JSON payloads with a required action field.
Messages are sent over TCP with a 4-byte big-endian length prefix.

Example payload:
{
    "action": "chat_message",
    "data": {
        "from": "alice",
        "text": "Hello"
    }
}
"""

from __future__ import annotations

import json
import struct
from typing import Any, Dict, List, Tuple

Message = Dict[str, Any]
HEADER_SIZE = 4
HEADER_FORMAT = ">I"  # 4-byte unsigned int, big-endian

# Standard action names used by client/server messages.
# Clients and servers should agree on these names.
ACTION = {
    "ping": "ping",
    "pong": "pong",
    "auth_request": "auth_request",
    "auth_response": "auth_response",
    "chat_message": "chat_message",
    "command": "command",
    "command_result": "command_result",
    "error": "error",
    "chat": "CHAT",
    "forward": "FORWARD",
}


def make_message(action: str, data: Any = None, metadata: Dict[str, Any] | None = None) -> Message:
    """Create a protocol message payload.

    The returned dictionary is ready for JSON serialization.
    """
    if not isinstance(action, str) or not action:
        raise ValueError("action must be a non-empty string")

    message: Message = {"action": action}
    if data is not None:
        message["data"] = data
    if metadata is not None:
        message["metadata"] = metadata
    return message


def encode_message(message: Message) -> bytes:
    """Encode a protocol message into bytes with a length prefix."""
    if "action" not in message:
        raise ValueError("message must contain an 'action' field")

    payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
    encoded = payload.encode("utf-8")
    length_prefix = struct.pack(HEADER_FORMAT, len(encoded))
    return length_prefix + encoded


def decode_messages(buffer: bytes) -> Tuple[List[Message], bytes]:
    """Decode all complete messages from a buffer.

    Returns a tuple of (messages, remaining_buffer).
    The remaining buffer contains incomplete bytes for the next read.
    """
    messages: List[Message] = []
    offset = 0
    buffer_length = len(buffer)

    while offset + HEADER_SIZE <= buffer_length:
        length = struct.unpack_from(HEADER_FORMAT, buffer, offset)[0]
        message_start = offset + HEADER_SIZE
        message_end = message_start + length
        if message_end > buffer_length:
            break

        chunk = buffer[message_start:message_end]
        try:
            message = json.loads(chunk.decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid JSON message payload") from exc

        if not isinstance(message, dict) or "action" not in message:
            raise ValueError("Decoded message must be a JSON object containing 'action'")

        messages.append(message)
        offset = message_end

    remaining = buffer[offset:]
    return messages, remaining


def create_error(message: str, code: int | None = None) -> Message:
    """Create a standardized error response."""
    payload = {"message": message}
    if code is not None:
        payload["code"] = code
    return make_message(ACTION["error"], payload)


def create_ping() -> Message:
    return make_message(ACTION["ping"])


def create_pong() -> Message:
    return make_message(ACTION["pong"])


def create_auth_request(username: str, token: str) -> Message:
    return make_message(ACTION["auth_request"], {"username": username, "token": token})


def create_auth_response(success: bool, reason: str | None = None) -> Message:
    payload: Dict[str, Any] = {"success": success}
    if reason is not None:
        payload["reason"] = reason
    return make_message(ACTION["auth_response"], payload)


def create_command(command_name: str, params: Any = None) -> Message:
    return make_message(ACTION["command"], {"name": command_name, "params": params})


def create_command_result(command_name: str, result: Any = None, success: bool = True) -> Message:
    return make_message(
        ACTION["command_result"],
        {"name": command_name, "success": success, "result": result},
    )


class Protocol:
    @staticmethod
    def create_chat_message(sender_id: str, receiver_id: str, content: str, reply_to_id: str | None = None) -> Message:
        """Create a chat or reply message payload."""
        data: Dict[str, Any] = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "reply_to_id": reply_to_id,
        }
        return make_message(ACTION["chat"], data)

    @staticmethod
    def create_forward_message(sender_id: str, receiver_id: str, original_msg_content: str) -> Message:
        """Create a forward message payload."""
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": original_msg_content,
        }
        return make_message(ACTION["forward"], data)

    @staticmethod
    def parse_message(raw_json_str: str) -> Message | None:
        """Parse a raw JSON string received from a socket."""
        try:
            message = json.loads(raw_json_str)
        except json.JSONDecodeError:
            return None

        if not isinstance(message, dict) or "action" not in message:
            return None

        return message
