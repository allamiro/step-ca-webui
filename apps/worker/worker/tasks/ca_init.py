import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from worker.celery_app import celery_app


def _db_engine():
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://pki:pki@postgres:5432/pki")
    return create_engine(database_url, future=True)


def _set_job_status(celery_id: str, status: str, error: str | None = None, output_json: dict | None = None):
    engine = _db_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE jobs SET status=:status, error=:error, output_json=:output_json, updated_at=:updated_at "
                "WHERE celery_id=:celery_id"
            ),
            {
                "status": status,
                "error": error,
                "output_json": json.dumps(output_json) if output_json else None,
                "updated_at": datetime.utcnow(),
                "celery_id": celery_id,
            },
        )


@celery_app.task(name="worker.tasks.ca_init.initialize_ca")
def initialize_ca(
    *,
    name: str,
    dns_names: str,
    address: str,
    provisioner: str,
    enable_acme: bool,
    enable_remote_management: bool,
    enable_ssh: bool,
    ca_password: str,
    provisioner_password: str,
):
    _set_job_status(initialize_ca.request.id, "running")
    step_path = Path(os.getenv("STEPPATH", "/home/step"))
    config_path = step_path / "config" / "ca.json"
    if config_path.exists():
        _set_job_status(
            initialize_ca.request.id,
            "failed",
            error=f"CA already initialized at {config_path}. Remove existing volume to re-init.",
        )
        return

    pw_file = step_path / "secrets" / ".ca_password"
    prov_pw_file = step_path / "secrets" / ".provisioner_password"
    pw_file.parent.mkdir(parents=True, exist_ok=True)
    pw_file.write_text(ca_password + "\n", encoding="utf-8")
    prov_pw_file.write_text(provisioner_password + "\n", encoding="utf-8")
    pw_file.chmod(0o600)
    prov_pw_file.chmod(0o600)

    cmd = [
        "step",
        "ca",
        "init",
        "--deployment-type",
        "standalone",
        "--name",
        name,
        "--dns",
        dns_names,
        "--address",
        address,
        "--provisioner",
        provisioner,
        "--password-file",
        str(pw_file),
        "--provisioner-password-file",
        str(prov_pw_file),
    ]
    if enable_acme:
        cmd.append("--acme")
    if enable_remote_management:
        cmd.append("--remote-management")
    if enable_ssh:
        cmd.append("--ssh")

    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        output = {
            "message": "CA initialized successfully",
            "config_path": str(config_path),
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-1000:],
            "step_path": str(step_path),
        }
        _set_job_status(initialize_ca.request.id, "succeeded", output_json=output)
    except Exception as exc:  # noqa: BLE001
        _set_job_status(initialize_ca.request.id, "failed", error=str(exc))
        raise
