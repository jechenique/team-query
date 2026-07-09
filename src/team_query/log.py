"""Verbose output helper for the generator.

User-facing messages go through click.echo in the CLI; everything else is
diagnostic detail that is silent unless --verbose is passed.
"""

_verbose = False


def set_verbose(enabled: bool) -> None:
    """Enable or disable verbose diagnostic output."""
    global _verbose
    _verbose = enabled


def vprint(*args, **kwargs) -> None:
    """Print diagnostic output only when verbose mode is enabled."""
    if _verbose:
        print(*args, **kwargs)
