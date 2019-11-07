from unittest import TestCase
import responses
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from nextcode import config, Client
from nextcode.exceptions import InvalidToken, InvalidProfile
from nextcode.utils import decode_token

REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjVjOTEyNjI4LTU0ZGQtNDcxNy04NGY2LTg0MzdlNzIwMjIzNCJ9.eyJqdGkiOiIyMjcyZGI2MC1kMDVmLTQ1MmItYWE4OC0wNzQ2YTZjYTI0ZTIiLCJleHAiOjAsIm5iZiI6MCwiaWF0IjoxNTcxMzEyODg0LCJpc3MiOiJodHRwczovL3Rlc3Qud3V4aW5leHRjb2RlLmNvbS9hdXRoL3JlYWxtcy93dXhpbmV4dGNvZGUuY29tIiwiYXVkIjoiaHR0cHM6Ly90ZXN0Lnd1eGluZXh0Y29kZS5jb20vYXV0aC9yZWFsbXMvd3V4aW5leHRjb2RlLmNvbSIsInN1YiI6IjVmMmUwNDc5LTM5YmItNDk2Mi1hN2U5LTM5ODhjZWJmZmFlZSIsInR5cCI6Ik9mZmxpbmUiLCJhenAiOiJhcGkta2V5LWNsaWVudCIsIm5vbmNlIjoiM2MxN2Y1MDEtYTEyNi00YjlmLThiZGYtYjg5ZTA0YTRhMjk1IiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiNjg5MDhiNmQtZWRmNS00NGYxLWJjMzAtMGM1YzVlMGFlNTgyIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYXBpLWtleS1jbGllbnQiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfcHJvdGVjdGlvbiJdfSwibmV4dGNvZGUiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfcHJvdGVjdGlvbiJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgb2ZmbGluZV9hY2Nlc3MifQ.k__XhfETIyRfIbw-Om7mH8uMXiEcCB7Jf0RvN63dfpo"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjJFRU42VUhzbEJLZHRGZU1BY2dWbzNqWVZlT0dWTGI0aVplR1JxZktJOVkifQ.eyJqdGkiOiJjMjUyM2UwNS1iZjcyLTRlNjQtOWE3MS0xMjE0NTcxOTYxMzQiLCJleHAiOjE1NzE5MTc2ODQsIm5iZiI6MCwiaWF0IjoxNTcxMzEyODg0LCJpc3MiOiJodHRwczovL3Rlc3Qud3V4aW5leHRjb2RlLmNvbS9hdXRoL3JlYWxtcy93dXhpbmV4dGNvZGUuY29tIiwiYXVkIjpbIm5leHRjb2RlIiwiYWNjb3VudCJdLCJzdWIiOiI1ZjJlMDQ3OS0zOWJiLTQ5NjItYTdlOS0zOTg4Y2ViZmZhZWUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhcGkta2V5LWNsaWVudCIsIm5vbmNlIjoiM2MxN2Y1MDEtYTEyNi00YjlmLThiZGYtYjg5ZTA0YTRhMjk1IiwiYXV0aF90aW1lIjoxNTcxMTM1NjMwLCJzZXNzaW9uX3N0YXRlIjoiNjg5MDhiNmQtZWRmNS00NGYxLWJjMzAtMGM1YzVlMGFlNTgyIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYXBpLWtleS1jbGllbnQiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfcHJvdGVjdGlvbiJdfSwibmV4dGNvZGUiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfcHJvdGVjdGlvbiJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgb2ZmbGluZV9hY2Nlc3MiLCJuYW1lIjoiVGVzdCBVc2VyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdEB3dXhpbmV4dGNvZGUuY29tIiwiZ2l2ZW5fbmFtZSI6IlRlc3QiLCJmYW1pbHlfbmFtZSI6IlVzZXIiLCJlbWFpbCI6InRlc3RAd3V4aW5leHRjb2RlLmNvbSJ9.CouyRBgeXoxNC5HGl0otWUJuOAr5mIjg0InZccHaekk"

AUTH_URL = "https://test.wuxinextcode.com/auth/realms/wuxinextcode.com/protocol/openid-connect/token"
AUTH_RESP = {"access_token": ACCESS_TOKEN}

import logging

logging.basicConfig(level=logging.DEBUG)

cfg = config.Config()


class BaseTestCase(TestCase):

    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        config.root_config_folder = Path(self.temp_dir)
        config._init_config()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
