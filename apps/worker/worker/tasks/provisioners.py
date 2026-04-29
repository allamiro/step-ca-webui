import os
import subprocess
import tempfile
from pathlib import Path

import httpx

from worker.celery_app import celery_app


@celery_app.task(name="worker.tasks.provisioners.list_provisioners")
def list_provisioners() -> dict:
    """
    Lists provisioners via step-ca admin API using a short-lived admin token.
    Requires STEP_CA_PASSWORD (same as DOCKER_STEPCA_INIT_PASSWORD in compose).
    """
    ca_url = os.getenv("STEP_CA_URL", "https://step-ca:9000").rstrip("/")
    password = (os.getenv("STEP_CA_PASSWORD") or "").strip()
    if not password:
        return {
            "items": [],
            "error": "STEP_CA_PASSWORD is not set on the worker (set to the same value as step-ca init password).",
        }

    try:
        with httpx.Client(verify=False, timeout=30.0, follow_redirects=True) as client:
            roots_resp = client.get(f"{ca_url}/roots.pem")
            if not roots_resp.is_success:
                return {"items": [], "error": f"Failed to fetch roots.pem: HTTP {roots_resp.status_code}"}
            roots_pem = roots_resp.text

        roots_path = Path("/tmp/pki-step-roots.pem")
        roots_path.write_text(roots_pem, encoding="utf-8")
        pw_path = Path("/tmp/pki-step-ca-password")
        pw_path.write_text(password + "\n", encoding="utf-8")
        pw_path.chmod(0o600)

        tok = subprocess.run(
            [
                "step",
                "ca",
                "token",
                "admin",
                "--ca-url",
                ca_url,
                "--roots",
                str(roots_path),
                "--password-file",
                str(pw_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        token = ""
        for line in reversed(tok.stdout.strip().splitlines()):
            line = line.strip()
            if line.count(".") == 2 and len(line) > 40:
                token = line
                break
        if not token:
            return {"items": [], "error": tok.stderr or tok.stdout or "empty admin token"}

        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client(verify=False, timeout=30.0, follow_redirects=True) as client:
            for path in ("/provisioners", "/1.0/provisioners", "/admin/provisioners"):
                resp = client.get(f"{ca_url}{path}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        return {"items": data, "source_path": path}
                    if isinstance(data, dict) and "provisioners" in data:
                        return {"items": data.get("provisioners", []), "source_path": path}
                    return {"items": [data] if data else [], "source_path": path}
            return {
                "items": [],
                "error": "Could not find provisioners admin endpoint (tried /provisioners, /1.0/provisioners, /admin/provisioners).",
            }
    except subprocess.CalledProcessError as exc:
        return {"items": [], "error": (exc.stderr or exc.stdout or str(exc)).strip()}
    except Exception as exc:  # noqa: BLE001
        return {"items": [], "error": str(exc)}
