"""Hashcat execution helpers for cracking phases."""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

_NO_DEVICE_ERRORS = (
    "no opencl",
    "no cuda",
    "no hip",
    "no devices found",
    "no devices available",
)


@dataclass
class HashcatResult:
    cracked: bool
    password: Optional[str]
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timeout: bool
    error_type: Optional[str] = None
    attempts: Optional[int] = None


def run_hashcat_attack(
    target_hash: str,
    hash_type_id: int,
    attack_mode: int,
    attack_args: Optional[List[str]],
    timeout: int,
    stdin_iter: Optional[Iterable[str]] = None,
) -> HashcatResult:
    """Run a hashcat attack with consistent handling and output parsing."""
    settings = get_settings()
    normalized_hash = target_hash.strip()
    timeout = max(1, int(timeout))
    start_time = time.time()
    attack_args = attack_args or []

    with TemporaryDirectory(prefix="hashcat_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        hash_file = _write_hash_file(tmp_path, normalized_hash)
        outfile = tmp_path / "hashcat.out"

        cmd = _build_hashcat_cmd(
            settings,
            hash_type_id,
            attack_mode,
            hash_file,
            attack_args,
            outfile,
            timeout,
            use_stdin=stdin_iter is not None,
        )

        if stdin_iter is None:
            stdout, stderr, exit_code, timeout_hit = _run_hashcat(cmd, timeout)
            attempts = None
        else:
            stdout, stderr, exit_code, timeout_hit, attempts = _run_hashcat_streaming(
                cmd,
                stdin_iter,
                timeout,
                start_time,
            )

        password = _read_outfile(outfile)
        duration = time.time() - start_time
        error_type = _detect_error_type(stderr)

        return HashcatResult(
            cracked=bool(password),
            password=password,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            timeout=timeout_hit,
            error_type=error_type,
            attempts=attempts,
        )


def _build_hashcat_cmd(
    settings,
    hash_type_id: int,
    attack_mode: int,
    hash_file: Path,
    attack_args: List[str],
    outfile: Path,
    timeout: int,
    use_stdin: bool,
) -> List[str]:
    cmd = [
        settings.hashcat_path,
        "-m",
        str(hash_type_id),
        "-a",
        str(attack_mode),
        str(hash_file),
    ]
    cmd.extend(attack_args)
    cmd.extend(_common_hashcat_args(settings, outfile, timeout, use_stdin))
    return cmd


def _common_hashcat_args(settings, outfile: Path, timeout: int, use_stdin: bool) -> List[str]:
    args = [
        "--runtime",
        str(max(1, int(timeout))),
        "--quiet",
        "--outfile",
        str(outfile),
        "--outfile-format",
        "2",
    ]

    if settings.hashcat_force:
        args.append("--force")
    if settings.hashcat_potfile_disable:
        args.append("--potfile-disable")
    if use_stdin:
        args.append("--stdin")

    return args


def _run_hashcat(cmd: List[str], timeout: int) -> tuple[str, str, int, bool]:
    timeout_hit = False
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        exit_code = -1
        timeout_hit = True

    return stdout, stderr, exit_code, timeout_hit


def _run_hashcat_streaming(
    cmd: List[str],
    stdin_iter: Iterable[str],
    timeout: int,
    start_time: float,
) -> tuple[str, str, int, bool, int]:
    timeout_hit = False
    attempts = 0

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    for candidate in stdin_iter:
        if time.time() - start_time >= timeout:
            timeout_hit = True
            break
        if proc.poll() is not None:
            break
        if not candidate:
            continue
        try:
            proc.stdin.write(candidate + "\n")
            attempts += 1
            if attempts % 1000 == 0:
                proc.stdin.flush()
        except BrokenPipeError:
            break

    if proc.stdin:
        try:
            proc.stdin.close()
        except Exception:
            pass

    remaining = max(0, timeout - (time.time() - start_time))
    try:
        stdout, stderr = proc.communicate(timeout=remaining)
    except subprocess.TimeoutExpired:
        timeout_hit = True
        proc.kill()
        stdout, stderr = proc.communicate()

    exit_code = proc.returncode if proc.returncode is not None else -1
    return stdout or "", stderr or "", exit_code, timeout_hit, attempts


def _write_hash_file(tmp_path: Path, target_hash: str) -> Path:
    hash_file = tmp_path / "hashes.txt"
    hash_file.write_text(target_hash.strip() + "\n", encoding="utf-8")
    return hash_file


def _read_outfile(outfile: Path) -> Optional[str]:
    try:
        if not outfile.exists():
            return None
        with outfile.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                return line.split(":", 1)[1].strip()
    except OSError as exc:
        logger.warning(f"Failed reading hashcat outfile: {exc}")
    return None


def _detect_error_type(stderr: str) -> Optional[str]:
    if not stderr:
        return None
    lowered = stderr.lower()
    if any(token in lowered for token in _NO_DEVICE_ERRORS):
        return "no_device"
    return None
