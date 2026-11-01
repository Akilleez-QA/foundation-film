import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "SOURCE-MANIFEST.json").read_text())
    actual = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.relative_to(ROOT).parts
        and path.suffix != ".pyc" and path.name != "SOURCE-MANIFEST.json"
    }
    if actual != manifest["files"]:
        raise SystemExit("Source manifest does not match shipped files")
    print(f"Verified {len(actual)} source files against SOURCE-MANIFEST.json")


if __name__ == "__main__":
    main()
