"""Fix E2E test paths to use /api/v1/ instead of /api/."""

from pathlib import Path


def fix_paths():
    """Replace /api/ with /api/v1/ in E2E test files."""
    e2e_dir = Path("coaching/tests/e2e")
    
    for test_file in e2e_dir.glob("test_*.py"):
        content = test_file.read_text(encoding="utf-8")
        original = content
        
        # Replace all occurrences of "/api/ with "/api/v1/
        content = content.replace('"/api/', '"/api/v1/')
        
        if content != original:
            test_file.write_text(content, encoding="utf-8")
            print(f"✓ Fixed: {test_file}")
        else:
            print(f"- Skipped: {test_file} (no changes needed)")


if __name__ == "__main__":
    fix_paths()
    print("\n✅ E2E test paths updated!")
