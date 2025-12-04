"""Fix all coaching.src imports to src imports for Lambda compatibility."""

from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Replace coaching.src with src in a Python file.

    Returns True if changes were made.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Replace all variations
        content = content.replace("from coaching.src", "from src")
        content = content.replace("import coaching.src", "import src")

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            print(f"✓ Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Fix all Python files in coaching/src directory."""
    coaching_src = Path("coaching/src")

    if not coaching_src.exists():
        print(f"Error: {coaching_src} not found")
        return

    print("Fixing imports in coaching/src...")
    print("-" * 60)

    fixed_count = 0
    total_count = 0

    for py_file in coaching_src.rglob("*.py"):
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1

    print("-" * 60)
    print(f"\n✅ Fixed {fixed_count} of {total_count} files")


if __name__ == "__main__":
    main()
