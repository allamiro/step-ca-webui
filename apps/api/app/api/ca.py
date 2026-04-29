import re
import subprocess
import tempfile

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.rbac import require_roles

router = APIRouter(prefix="/ca", tags=["ca"])


class CaInitPlanRequest(BaseModel):
    name: str = Field(default="My PKI", min_length=1, max_length=255)
    dns_names: str = Field(default="step-ca,localhost", min_length=1, max_length=512)
    address: str = Field(default=":9000", min_length=1, max_length=128)
    provisioner: str = Field(default="admin", min_length=1, max_length=255)
    enable_acme: bool = True
    enable_remote_management: bool = True
    enable_ssh: bool = False


def _step_http() -> httpx.Client:
    return httpx.Client(verify=False, timeout=15.0, follow_redirects=True)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/summary")
def ca_summary(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor", "pki-user"))):
    base = settings.step_ca_url.rstrip("/")
    out: dict = {"reachable": False, "step_ca_url": base}
    try:
        with _step_http() as client:
            health = client.get(f"{base}/health")
            roots = client.get(f"{base}/roots.pem")
        out["reachable"] = health.is_success
        out["health_status"] = health.status_code
        if health.headers.get("content-type", "").startswith("application/json"):
            try:
                out["health"] = health.json()
            except Exception:
                out["health"] = {"raw": health.text[:500]}
        else:
            out["health"] = {"raw": health.text[:500]}

        out["roots_available"] = roots.is_success
        out["roots_bytes"] = len(roots.content) if roots.is_success else 0

        fingerprint = ""
        if roots.is_success and roots.text.strip():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as tmp:
                tmp.write(roots.text)
                tmp.flush()
                try:
                    proc = subprocess.run(
                        ["openssl", "x509", "-in", tmp.name, "-noout", "-fingerprint", "-sha256"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    if proc.returncode == 0:
                        fingerprint = proc.stdout.strip()
                except FileNotFoundError:
                    m = re.search(r"SHA256 Fingerprint=([0-9A-F:]+)", roots.text, re.I)
                    if m:
                        fingerprint = m.group(1)
        out["root_fingerprint_openssl"] = fingerprint

        intermediate_note = "Intermediate chain may be included in roots.pem or issued leaf chain; use step CLI for full export."
        out["intermediate_note"] = intermediate_note
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
    return out


@router.get("/roots.pem")
def download_roots(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor", "pki-user"))):
    base = settings.step_ca_url.rstrip("/")
    try:
        with _step_http() as client:
            roots = client.get(f"{base}/roots.pem")
        if not roots.is_success:
            raise HTTPException(status_code=502, detail=f"step-ca returned {roots.status_code} for roots.pem")
        return Response(
            content=roots.content,
            media_type="application/x-pem-file",
            headers={"Content-Disposition": 'attachment; filename="roots.pem"'},
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/intermediate.pem")
def download_intermediate(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor", "pki-user"))):
    """
    Tries common step-ca paths for intermediate CA PEM (varies by version/config).
    """
    base = settings.step_ca_url.rstrip("/")
    paths = ["/intermediate.pem", "/intermediate.crt", "/intermediate_ca.crt", "/1.0/intermediate"]
    last_err = ""
    try:
        with _step_http() as client:
            for path in paths:
                resp = client.get(f"{base}{path}")
                if resp.is_success and resp.content and b"BEGIN CERTIFICATE" in resp.content:
                    return Response(
                        content=resp.content,
                        media_type="application/x-pem-file",
                        headers={"Content-Disposition": 'attachment; filename="intermediate.pem"'},
                    )
                last_err = f"{path}: {resp.status_code}"
        return PlainTextResponse(
            f"No intermediate PEM found at tried paths ({last_err}). Download roots.pem or use the step CLI inside the worker.",
            status_code=404,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/bootstrap")
def bootstrap_info(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor", "pki-user"))):
    """
    Explains how the CA is initialized in Docker vs. production bring-your-own.
    """
    return {
        "docker_auto_init": False,
        "summary": (
            "This stack is configured for MANUAL CA initialization. "
            "Run `docker compose run --rm step-ca-init` (or your own step-ca init command) "
            "to generate /home/step/config/ca.json and PKI secrets on the stepca_data volume. "
            "Only after that, start step-ca with `docker compose up`. "
            "This lets you control all init parameters (name, DNS, address, provisioners, ACME, remote-management, passwords)."
        ),
        "manual_init_commands": [
            "docker compose run --rm step-ca-init",
            "docker compose up --build",
        ],
        "downloads": {
            "roots_pem": "/api/ca/roots.pem",
            "intermediate_pem": "/api/ca/intermediate.pem",
            "summary": "/api/ca/summary",
        },
        "external_urls": {
            "step_ca_health": f"{settings.step_ca_url.rstrip('/')}/health",
            "step_ca_roots": f"{settings.step_ca_url.rstrip('/')}/roots.pem",
        },
    }


@router.post("/init-plan")
def init_plan(
    payload: CaInitPlanRequest,
    _: dict = Depends(require_roles("pki-admin")),
):
    cmd = [
        "docker compose run --rm step-ca-init step ca init",
        f"--name '{payload.name}'",
        f"--dns '{payload.dns_names}'",
        f"--address '{payload.address}'",
        f"--provisioner '{payload.provisioner}'",
    ]
    if payload.enable_acme:
        cmd.append("--acme")
    if payload.enable_remote_management:
        cmd.append("--remote-management")
    if payload.enable_ssh:
        cmd.append("--ssh")
    command = " ".join(cmd)
    return {
        "command": command,
        "next_steps": [
            "Run the command from the infra directory.",
            "Set STEP_CA_PASSWORD to the password you entered during init.",
            "Start stack with: docker compose up --build",
        ],
        "worker_env_example": "export STEP_CA_PASSWORD='<your-step-ca-password>'",
    }
