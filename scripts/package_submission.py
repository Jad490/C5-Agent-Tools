"""Create a source/writing ZIP using an allowlist that excludes secrets and runtime data."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "README.md",
    "SUBMISSION.md",
    "pyproject.toml",
    "requirements.lock",
    ".env.example",
    ".gitignore",
]
DIRECTORIES = ["campus_mcp", "tests", "scripts", "docs", "evidence", ".github"]


def main() -> None:
    output = ROOT / "dist" / "campus-reading-mcp.zip"
    output.parent.mkdir(exist_ok=True)
    paths = [ROOT / name for name in FILES]
    for directory in DIRECTORIES:
        paths.extend(path for path in (ROOT / directory).rglob("*") if path.is_file())
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            relative = path.relative_to(ROOT)
            if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            archive.write(path, Path("campus-reading-mcp") / relative)
    print(f"Created {output}")
    print("Source and writing only. Add real repository/video links before submitting.")


if __name__ == "__main__":
    main()
