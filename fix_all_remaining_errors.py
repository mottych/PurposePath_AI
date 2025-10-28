#!/usr/bin/env python3
"""Fix ALL remaining ruff errors systematically."""
import re
import subprocess
from pathlib import Path

def get_errors_by_type():
    """Get all errors grouped by type."""
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "coaching/src/", "shared/", "--output-format=json"],
        capture_output=True,
        text=True
    )
    import json
    errors = json.loads(result.stdout)
    
    by_type = {}
    for error in errors:
        code = error['code']
        if code not in by_type:
            by_type[code] = []
        by_type[code].append(error)
    
    return by_type

def fix_arg002_errors(errors):
    """Prefix unused args with underscore."""
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
        
        # Sort by line number descending
        for line_num, arg_name in sorted(fixes, reverse=True):
            line = lines[line_num - 1]
            # Replace arg_name: with _arg_name:
            new_line = re.sub(rf'\b{arg_name}\s*:', f'_{arg_name}:', line)
            lines[line_num - 1] = new_line
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    print(f"Fixed ARG002 in {len(files_to_fix)} files")

def fix_b904_errors(errors):
    """Add exception chaining."""
    files_to_fix = {}
    
    for error in errors:
        file_path = error['filename']
        line_num = error['location']['row']
        
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(line_num)
    
    for file_path, line_nums in files_to_fix.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort descending
        for line_num in sorted(line_nums, reverse=True):
            line = lines[line_num - 1]
            # Add 'from e' or 'from None' to raise statements
            if 'raise' in line and 'from' not in line:
                # Check if there's an except clause with 'as e'
                found_e = False
                for i in range(max(0, line_num - 5), line_num):
                    if 'except' in lines[i] and ' as e' in lines[i]:
                        found_e = True
                        break
                
                if found_e:
                    lines[line_num - 1] = line.rstrip() + ' from e\n'
                else:
                    lines[line_num - 1] = line.rstrip() + ' from None\n'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    print(f"Fixed B904 in {len(files_to_fix)} files")

def fix_ruf012_errors(errors):
    """Add ClassVar annotations."""
    from typing import ClassVar
    
    files_to_fix = {}
    
    for error in errors:
        file_path = error['filename']
        line_num = error['location']['row']
        
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(line_num)
    
    for file_path, line_nums in files_to_fix.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add ClassVar import if not present
        if 'from typing import' in content and 'ClassVar' not in content:
            content = content.replace('from typing import', 'from typing import ClassVar,', 1)
        elif 'import typing' not in content and 'from typing' not in content:
            # Add at top after other imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from') or line.startswith('import'):
                    continue
                else:
                    lines.insert(i, 'from typing import ClassVar')
                    content = '\n'.join(lines)
                    break
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Now add ClassVar to the actual fields
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num in sorted(line_nums, reverse=True):
            line = lines[line_num - 1]
            # Add ClassVar[] wrapper
            if ' = {' in line or ' = [' in line:
                # Find the type annotation
                match = re.search(r'(\w+)\s*:\s*([^=]+)\s*=', line)
                if match:
                    var_name = match.group(1)
                    type_annotation = match.group(2).strip()
                    new_line = line.replace(f'{var_name}: {type_annotation} =', 
                                          f'{var_name}: ClassVar[{type_annotation}] =')
                    lines[line_num - 1] = new_line
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    print(f"Fixed RUF012 in {len(files_to_fix)} files")

def fix_sim102_errors(errors):
    """Collapse nested if statements."""
    # This requires manual review, but we can add # noqa as last resort
    # Actually, let's properly combine them
    print(f"⚠ SIM102: {len(errors)} nested ifs need manual review")

if __name__ == "__main__":
    print("Analyzing errors...")
    errors_by_type = get_errors_by_type()
    
    for code, errors in errors_by_type.items():
        print(f"  {code}: {len(errors)} errors")
    
    print("\nFixing errors...")
    
    if 'ARG002' in errors_by_type:
        fix_arg002_errors(errors_by_type['ARG002'])
    
    if 'B904' in errors_by_type:
        fix_b904_errors(errors_by_type['B904'])
    
    if 'RUF012' in errors_by_type:
        fix_ruf012_errors(errors_by_type['RUF012'])
    
    if 'SIM102' in errors_by_type:
        fix_sim102_errors(errors_by_type['SIM102'])
    
    print("\n✓ Done! Running ruff check...")
    subprocess.run(["python", "-m", "ruff", "check", "coaching/", "shared/", "--statistics"])
