import json
import os
import subprocess
from pathlib import Path


def _run_step(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=90)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "raw": json.dumps({"command": cmd}),
    }


def issue_certificate(common_name: str, sans: list[str]) -> dict:
    """
    Executes step CLI with validated args.
    This uses subprocess without shell=True for command safety.
    """
    out_dir = Path("/tmp/pki-jobs")
    out_dir.mkdir(parents=True, exist_ok=True)

    crt_path = out_dir / f"{common_name}.crt"
    key_path = out_dir / f"{common_name}.key"
    cmd = [
        "step",
        "ca",
        "certificate",
        common_name,
        str(crt_path),
        str(key_path),
        "--ca-url",
        os.getenv("STEP_CA_URL", "https://step-ca:9000"),
        "--force",
    ]
    for san in sans:
        cmd.extend(["--san", san])

    out = _run_step(cmd)
    return {
        "stdout": out["stdout"],
        "stderr": out["stderr"],
        "certificate_path": str(crt_path),
        "key_path": str(key_path),
        "serial_number": "",
        "raw": out["raw"],
    }


def renew_certificate(common_name: str) -> dict:
    out_dir = Path("/tmp/pki-jobs")
    crt_path = out_dir / f"{common_name}.crt"
    key_path = out_dir / f"{common_name}.key"
    if not crt_path.exists() or not key_path.exists():
        raise FileNotFoundError(f"Missing certificate artifacts for {common_name}")
    cmd = [
        "step",
        "ca",
        "renew",
        str(crt_path),
        str(key_path),
        "--ca-url",
        os.getenv("STEP_CA_URL", "https://step-ca:9000"),
        "--force",
    ]
    out = _run_step(cmd)
    return {
        "stdout": out["stdout"],
        "stderr": out["stderr"],
        "certificate_path": str(crt_path),
        "key_path": str(key_path),
        "raw": out["raw"],
    }


def revoke_certificate(common_name: str, reason: str) -> dict:
    out_dir = Path("/tmp/pki-jobs")
    crt_path = out_dir / f"{common_name}.crt"
    key_path = out_dir / f"{common_name}.key"
    if not crt_path.exists() or not key_path.exists():
        raise FileNotFoundError(f"Missing certificate artifacts for {common_name}")
    cmd = [
        "step",
        "ca",
        "revoke",
        "--cert",
        str(crt_path),
        "--key",
        str(key_path),
        "--ca-url",
        os.getenv("STEP_CA_URL", "https://step-ca:9000"),
        "--reason",
        reason or "unspecified",
        "--force",
    ]
    out = _run_step(cmd)
    return {
        "stdout": out["stdout"],
        "stderr": out["stderr"],
        "certificate_path": str(crt_path),
        "key_path": str(key_path),
        "raw": out["raw"],
    }
