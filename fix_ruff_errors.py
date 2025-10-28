#!/usr/bin/env python3
"""Systematically fix remaining ruff errors."""
import re
import subprocess
from pathlib import Path

def get_arg002_errors():
    """Get all ARG002 errors."""
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "coaching/src/", "shared/", "--select", "ARG002", "--output-format=json"],
        capture_output=True,
        text=True
    )
    import json
    return json.loads(result.stdout)

def fix_arg002():
    """Prefix unused args with underscore."""
    errors = get_arg002_errors()
    files_to_fix = {}
    
    for error in errors:
        file_path = error['filename']
        line_num = error['location']['row']
        arg_name = error['message'].split('`')[1]
        
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append((line_num, arg_name))
    
    for file_path, fixes in files_to_fix.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort by line number descending to avoid offset issues
        for line_num, arg_name in sorted(fixes, reverse=True):
            line = lines[line_num - 1]
            # Replace arg_name with _arg_name
            new_line = re.sub(rf'\b{arg_name}\b(?=\s*:)', f'_{arg_name}', line)
            lines[line_num - 1] = new_line
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    print(f"Fixed ARG002 in {len(files_to_fix)} files")

if __name__ == "__main__":
    fix_arg002()
