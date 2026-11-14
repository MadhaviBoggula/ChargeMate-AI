
"""Knowledge-base ingestion CLI (Member 4, lane D).

Scans knowledge_base/owner and knowledge_base/driver under backend/ and
ingests supported documents (PDF/DOCX/TXT/MD) into pgvector, role-tagged.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\ingest_docs.py            # new/changed only
    .venv\\Scripts\\python.exe scripts\\ingest_docs.py --reindex  # rebuild all
    .venv\\Scripts\\python.exe scripts\\ingest_docs.py --file ..\\knowledge_base\\driver\\faq.txt --role driver
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.rag.ingest import SUPPORTED_EXTENSIONS, ingest_document  # noqa: E402


def _collect_files(role_dir: Path) -> list[Path]:
    if not role_dir.exists():
        return []
    return sorted(
        p
        for p in role_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
        and not p.name.startswith("~$")
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest knowledge-base documents"
    )
    parser.add_argument(
        "--reindex", action="store_true", help="Rebuild all documents"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Ingest a single file instead of scanning folders",
    )
    parser.add_argument(
        "--role",
        choices=["owner", "driver"],
        help="Role when using --file",
    )
    args = parser.parse_args()

    jobs: list[tuple[Path, str]] = []

    if args.file:
        role = args.role
        if not role:
            parent = args.file.parent.name.lower()
            role = (
                parent
                if parent in {"owner", "driver"}
                else None
            )
        if role is None:
            parser.error(
                "--file requires --role owner|driver "
                "(or a parent folder named owner|driver)"
            )
        jobs.append((args.file, role))
    else:
        jobs.extend(
            (p, "owner") for p in _collect_files(settings.owner_knowledge_dir)
        )
        jobs.extend(
            (p, "driver")
            for p in _collect_files(settings.driver_knowledge_dir)
        )

    if not jobs:
        print(
            f"No supported documents found under {settings.knowledge_base_dir}"
        )
        return 0

    failures = 0

    for path, role in jobs:
        result = ingest_document(path, role, force=args.reindex)
        status = result["status"]
        detail = result.get("error") or ""
        print(
            f"[{status:>7}] role={role:<6} {path.name:<40} "
            f"chunks={result['chunks']} {detail}"
        )
        if status == "failed":
            failures += 1

    print(f"\nDone: {len(jobs)} documents, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
