import os

os.environ.pop("PYSIGMA_API_KEY", None)

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def sigma_rule():
    return r'''title: Suspicious Whoami Privileges
id: 11111111-1111-4111-8111-111111111111
status: experimental
description: Test rule
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\\whoami.exe'
    CommandLine|contains: '/priv'
  condition: selection
falsepositives:
  - Administrative activity
level: medium
'''
