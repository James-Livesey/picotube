import urllib.request
import json
from app import config

def fetch_private_api(endpoint, method="GET", body=None):
    request = urllib.request.Request("http://0.0.0.0:8000/" + endpoint, method=method)

    request.add_header("Authorization", "Bearer " + config.private_api_secret)

    data = None

    if body is not None:
        data = json.dumps(body).encode()

        request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request, data=data) as response:
        return json.loads(response.read().decode())