# SPDX-License-Identifier: Apache-2.0
"""Best-effort inventory of CPU, memory, and visible accelerator resources."""

import csv
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _host_memory_bytes() -> int | None:
    contents = _read_text("/proc/meminfo")
    if contents:
        match = re.search(r"^MemTotal:\s+(\d+)\s+kB", contents, re.MULTILINE)
        if match:
            return int(match.group(1)) * 1024
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None


def _container_memory_limit() -> int | None:
    for path in (
        "/sys/fs/cgroup/memory.max",
        "/sys/fs/cgroup/memory/memory.limit_in_bytes",
    ):
        value = _read_text(path)
        if not value or value == "max":
            continue
        try:
            limit = int(value)
        except ValueError:
            continue
        if 0 < limit < 2**60:
            return limit
    return None


def _effective_cpu_count() -> float:
    count = float(os.cpu_count() or 1)
    try:
        count = min(count, float(len(os.sched_getaffinity(0))))
    except (AttributeError, OSError):
        pass

    quota = _read_text("/sys/fs/cgroup/cpu.max")
    if quota:
        parts = quota.split()
        if len(parts) == 2 and parts[0] != "max":
            try:
                count = min(count, max(0.01, int(parts[0]) / int(parts[1])))
            except (ValueError, ZeroDivisionError):
                pass
    else:
        quota_us = _read_text("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
        period_us = _read_text("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
        if quota_us and period_us:
            try:
                if int(quota_us) > 0 and int(period_us) > 0:
                    count = min(count, int(quota_us) / int(period_us))
            except ValueError:
                pass
    return round(count, 2)


def _detect_nvidia() -> list[dict[str, object]]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return []
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    devices: list[dict[str, object]] = []
    for row in csv.reader(result.stdout.splitlines()):
        values = [value.strip() for value in row]
        if not values or not values[0]:
            continue
        memory_mb = None
        if len(values) > 1:
            try:
                memory_mb = int(float(values[1]))
            except ValueError:
                pass
        devices.append(
            {
                "vendor": "NVIDIA",
                "name": values[0],
                "memory_bytes": memory_mb * 1024 * 1024 if memory_mb is not None else None,
                "driver_version": values[2] if len(values) > 2 else None,
                "compute_capability": values[3] if len(values) > 3 else None,
                "detection": "nvidia-smi",
                "runtime_verified": False,
            }
        )
    return devices


def _detect_amd() -> list[dict[str, object]]:
    executable = shutil.which("rocminfo")
    if not executable:
        return []
    try:
        result = subprocess.run(
            [executable],
            capture_output=True,
            check=False,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    architecture_pattern = r"^\s*Name:\s*(gfx[0-9a-z]+)\s*$"
    architectures = sorted(
        set(re.findall(architecture_pattern, result.stdout, re.MULTILINE))
    )
    return [
        {
            "vendor": "AMD",
            "name": "AMD accelerator",
            "architecture": architecture,
            "memory_bytes": None,
            "detection": "rocminfo",
            "runtime_verified": False,
        }
        for architecture in architectures
    ]


def _detect_accelerators() -> list[dict[str, object]]:
    devices = _detect_nvidia()
    if devices:
        return devices
    devices = _detect_amd()
    if devices:
        return devices

    if platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}:
        return [
            {
                "vendor": "Apple",
                "name": "Apple Silicon integrated GPU candidate",
                "memory_bytes": None,
                "detection": "platform",
                "runtime_verified": False,
            }
        ]

    render_nodes = sorted(Path("/dev/dri").glob("renderD*")) if Path("/dev/dri").is_dir() else []
    if render_nodes:
        return [
            {
                "vendor": "Unknown",
                "name": "GPU device node visible",
                "device_count": len(render_nodes),
                "memory_bytes": None,
                "detection": "device-node",
                "runtime_verified": False,
            }
        ]
    return []


def collect_capabilities() -> dict[str, object]:
    """Return conservative host/container inventory, never inferred performance claims."""
    return {
        "scope": "API worker host visible to this process",
        "inventory_only": True,
        "cpu": {
            "architecture": platform.machine() or "unknown",
            "processor": platform.processor() or "unknown",
            "logical_cores": os.cpu_count() or 1,
            "effective_cores": _effective_cpu_count(),
        },
        "memory": {
            "host_total_bytes": _host_memory_bytes(),
            "container_limit_bytes": _container_memory_limit(),
        },
        "accelerators": _detect_accelerators(),
        "notes": [
            (
                "A visible device is not proof that a compatible inference or training "
                "runtime is installed."
            ),
            "This reports the API worker host, not the phone or browser controlling it.",
            "GPU allocation, benchmarks, and model compatibility checks are separate operations.",
        ],
    }
