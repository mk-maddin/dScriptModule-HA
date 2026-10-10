"""Fixtures for dscriptmodule tests."""
import asyncio
import socket

import pytest

from custom_components.dscriptmodule.const import DEFAULT_PORT

BOARD_IP = "127.0.0.2"  # boards and the integrated dScriptServer need different IPs (both use port 17123)
BOARD_IP_NEW = "127.0.0.4"  # same board after an IP change
NO_BOARD_IP = "127.0.0.3"  # nothing listens here
STATUS = bytes([34, 4, 13, 3, 8, 120, 1, 11])                # dS2824, FW 4.13, App 3.8
CONFIG = bytes([0, 1, 2, 0xAB, 4, 5, 24, 2, 1, 1, 1, 1])     # 24 relays, 2 lights, 1 shutter, 1 socket, 1 motion, 1 button


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


def free_port(ip="127.0.0.1"):
    with socket.socket() as s:
        s.bind((ip, 0))
        return s.getsockname()[1]


class FakeBoard:
    """Emulates a dS2824 running dScriptRoomControl (one request per TCP connection)."""

    def __init__(self, ip=BOARD_IP):
        self.ip = ip
        self.requests = []
        self.lights = {1: 0, 2: 0}
        self.server = None

    def response(self, data):
        cmd = data[0]
        if cmd == 0x30: return STATUS
        if cmd == 0x50: return CONFIG
        if cmd == 0x40:
            self.lights[data[1]] = data[2]
            return bytes([0])
        if cmd == 0x51: return bytes([self.lights.get(data[1], 0)])
        if cmd == 0x52: return bytes([100, 0])
        if cmd == 0x53: return bytes([0])
        if cmd in (0x54, 0x55): return bytes([0])
        return bytes([0])

    async def handle(self, reader, writer):
        try:
            data = await reader.read(100)
            if data:
                self.requests.append(bytes(data))
                writer.write(self.response(data))
                await writer.drain()
        finally:
            writer.close()

    async def start(self):
        self.server = await asyncio.start_server(self.handle, self.ip, DEFAULT_PORT)
        return self

    async def stop(self):
        self.server.close()
        await self.server.wait_closed()

    async def trigger(self, server_port, payload):
        """Send a status trigger to the integrated dScriptServer like the firmware does."""
        reader, writer = await asyncio.open_connection("127.0.0.1", server_port, local_addr=(self.ip, 0))
        writer.write(payload)
        await writer.drain()
        await reader.read(10)
        writer.close()


@pytest.fixture
async def fake_board():
    board = await FakeBoard().start()
    yield board
    await board.stop()
