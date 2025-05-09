"""
Core utilities for Dagger container tools.

This module provides shared helpers for creating and running containers
with standardized error handling and configuration.
"""
import os
from typing import Sequence
import dagger

# Get the absolute path to the scripts directory
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")

def get_tool_base(
    client: dagger.Client,
    image: str,
    scripts_dir: str,
    workdir: str = "/workspace",
) -> dagger.Container:
    """
    Return a pre-configured container for this tool:
    - pulled from `image`
    - working dir set to `workdir`
    - host directory `scripts_dir` mounted at `workdir/scripts`
    """
    return (
        client
        .container()
        .from_(image)
        .with_workdir(workdir)
        .with_mounted_directory(
            f"{workdir}/scripts",
            client.host().directory(scripts_dir),
        )
    )

async def run_container_and_check(
    container: dagger.Container,
    args: Sequence[str],
) -> str:
    """
    Exec the container with `args`, check exit code, return stdout.
    Raises RuntimeError if the command fails.
    """
    proc = container.with_exec(list(args))
    stdout = await proc.stdout()
    exit_code = await proc.exit_code()
    if exit_code != 0:
        stderr = await proc.stderr()
        raise RuntimeError(
            f"Container exited {exit_code}.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
    return stdout.strip()
