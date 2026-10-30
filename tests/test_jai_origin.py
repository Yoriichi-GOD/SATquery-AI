import unittest

from jai_extension.server import ExtensionOrigin


class OriginTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, origin):
        result, sent = {}, []
        async def inner(scope, receive, send):
            result["origin"] = dict(scope["headers"]).get(b"origin")
        async def receive():
            return {"type": "http.request", "body": b""}
        async def send(message):
            sent.append(message)
        headers = [] if origin is None else [(b"origin", origin)]
        await ExtensionOrigin(inner, 8768)({"type": "http", "headers": headers}, receive, send)
        return result, sent

    async def test_same_origin_adapted_to_baseline(self):
        result, sent = await self.invoke(b"http://127.0.0.1:8768")
        self.assertEqual(result["origin"], b"http://127.0.0.1:8767")
        self.assertEqual(sent, [])

    async def test_other_origin_rejected(self):
        result, sent = await self.invoke(b"https://evil.example")
        self.assertEqual(result, {})
        self.assertEqual(sent[0]["status"], 403)

    async def test_missing_origin_preserved(self):
        result, sent = await self.invoke(None)
        self.assertIsNone(result["origin"])
