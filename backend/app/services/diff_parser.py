import re
from typing import Any

HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
NEW_FILE_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
BINARY_RE = re.compile(r"^Binary files .+ differ$")


def parse_diff(diff_text: str) -> list[dict[str, Any]]:
    """Parse a unified diff into a list of per-file dicts.

    Each file dict: path, old_path, status, additions, deletions,
    hunks (each with old_start, new_start, lines).
    """
    files: list[dict[str, Any]] = []
    current_file: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None
    old_line = new_line = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            match = NEW_FILE_RE.match(line)
            path = match.group(2) if match else line
            current_file = {
                "path": path,
                "old_path": match.group(1) if match else path,
                "status": "modified",
                "additions": 0,
                "deletions": 0,
                "is_binary": False,
                "hunks": [],
            }
            files.append(current_file)
            current_hunk = None
            continue

        if current_file is None:
            continue

        if line.startswith("new file mode"):
            current_file["status"] = "added"
            continue
        if line.startswith("deleted file mode"):
            current_file["status"] = "deleted"
            continue
        if line.startswith("rename from") or line.startswith("rename to"):
            current_file["status"] = "renamed"
            continue
        if line.startswith("Binary files") or line.startswith("GIT binary patch"):
            current_file["is_binary"] = True
            continue
        if line.startswith(("index ", "--- ", "+++ ", "similarity ", "dissimilarity ")):
            continue

        hunk_match = HUNK_HEADER_RE.match(line)
        if hunk_match:
            old_start = int(hunk_match.group(1))
            new_start = int(hunk_match.group(3))
            old_line, new_line = old_start, new_start
            current_hunk = {
                "old_start": old_start,
                "new_start": new_start,
                "lines": [],
            }
            current_file["hunks"].append(current_hunk)
            continue

        if current_hunk is None:
            continue

        if line.startswith("+"):
            current_file["additions"] += 1
            current_hunk["lines"].append(
                {"type": "add", "new_number": new_line, "old_number": None, "content": line[1:]}
            )
            new_line += 1
        elif line.startswith("-"):
            current_file["deletions"] += 1
            current_hunk["lines"].append(
                {"type": "del", "new_number": None, "old_number": old_line, "content": line[1:]}
            )
            old_line += 1
        elif line.startswith("\\"):  # "No newline at end of file"
            current_hunk["lines"].append(
                {"type": "meta", "new_number": None, "old_number": None, "content": line[1:]}
            )
        else:
            current_hunk["lines"].append(
                {
                    "type": "context",
                    "new_number": new_line,
                    "old_number": old_line,
                    "content": line[1:] if line.startswith(" ") else line,
                }
            )
            old_line += 1
            new_line += 1

    return files
