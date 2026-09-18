import pytest
from meraki.core.response import Response

@pytest.mark.asyncio
async def test_response_send():
    """Verify Response objects properly construct and send ASGI messages."""
    res = Response(body=b"test body", status_code=201, headers=[(b"custom", b"header")])
    
    messages = []
    
    async def mock_send(msg):
        messages.append(msg)
        
    await res.send(mock_send)
    
    assert len(messages) == 2
    
    start_msg = messages[0]
    assert start_msg["type"] == "http.response.start"
    assert start_msg["status"] == 201
    assert start_msg["headers"] == [(b"custom", b"header")]
    
    body_msg = messages[1]
    assert body_msg["type"] == "http.response.body"
    assert body_msg["body"] == b"test body"

@pytest.mark.asyncio
async def test_response_default_headers():
    """Verify Response objects correctly guess length and content-type if headers are not explicitly provided."""
    res = Response(body=b"123", status_code=200)
    
    messages = []
    
    async def mock_send(msg):
        messages.append(msg)
        
    await res.send(mock_send)
    
    start_msg = messages[0]
    
    assert start_msg["headers"] == [
        (b"content-type", b"text/plain"),
        (b"content-length", b"3")
    ]
