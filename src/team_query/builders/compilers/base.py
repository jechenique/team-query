"""Base compiler module with common functionality."""

import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from team_query.log import vprint
from team_query.models import QueriesFile, Query, SQLConfig

# Must stay in sync with the /* IF param */ pattern used by the generated
# runtimes (process_conditional_blocks / processConditionalBlocks) so that
# compile-time expansion produces the exact same segments.
CONDITIONAL_BLOCK_RE = re.compile(r"/\* IF (\w+) \*/(.*?)/\* END IF \*/", re.DOTALL)


class BaseCompiler:
    """Base compiler class with common functionality."""

    def __init__(self):
        """Initialize the base compiler."""
        self.query_files = []
        self.output_dir = ""
        self.config = None
        self.options: Dict[str, Any] = {}

    @staticmethod
    def split_conditional_segments(sql: str) -> List[Tuple[str, ...]]:
        """Split SQL into static and conditional segments.

        Returns a list of ("static", text) and ("block", param_name, content)
        tuples, always starting and ending with a static segment (possibly
        empty). Concatenating the static segments plus the block contents of
        truthy params reproduces exactly what the generated runtime's
        process_conditional_blocks would return.

        Raises ValueError if any segment still contains block markers, which
        means the markers are nested or unbalanced - the runtime regex would
        silently mishandle those, so compile-time expansion rejects them.
        """
        segments: List[Tuple[str, ...]] = []
        last_end = 0
        for match in CONDITIONAL_BLOCK_RE.finditer(sql):
            segments.append(("static", sql[last_end : match.start()]))
            segments.append(("block", match.group(1), match.group(2)))
            last_end = match.end()
        segments.append(("static", sql[last_end:]))

        for segment in segments:
            text = segment[-1]
            if "/* IF " in text or "/* END IF */" in text:
                raise ValueError(
                    "Nested or unbalanced /* IF */ ... /* END IF */ markers"
                )
        return segments

    def create_output_dir(self, output_dir: str) -> None:
        """Create the output directory if it doesn't exist."""
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir

    def clean_output_directory(self, output_dir: str) -> None:
        """Clean the output directory by removing all files and subdirectories."""
        if os.path.exists(output_dir):
            vprint(f"Cleaning output directory: {output_dir}")
            try:
                # Remove all files and subdirectories
                for item in os.listdir(output_dir):
                    item_path = os.path.join(output_dir, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                vprint(f"Output directory cleaned: {output_dir}")
            except (FileNotFoundError, PermissionError) as e:
                # Handle the case where the directory exists but can't be accessed
                vprint(f"Warning: Could not clean directory {output_dir}: {str(e)}")
                # Create it anyway
                os.makedirs(output_dir, exist_ok=True)
        else:
            vprint(f"Output directory does not exist, will be created: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)

    def sanitize_name(self, name: str) -> str:
        """Sanitize a name to be used as a function or variable name."""
        # Replace non-alphanumeric characters with underscores
        sanitized = "".join(c if c.isalnum() else "_" for c in name)
        # Ensure the name starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "f_" + sanitized
        return sanitized

    def compile(
        self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
    ) -> None:
        """Compile queries to code."""
        self.query_files = queries_files
        self.config = config
        self.clean_output_directory(output_dir)
        self.create_output_dir(output_dir)
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement compile method")
