# Database Repair Scripts

This directory contains maintenance scripts for the Togetherly database.

## repair_malformed_json.py

Repairs malformed JSON data in VoiceProfile fields.

### Purpose

VoiceProfile model stores several fields as JSON text columns (platforms, brand_keywords, goals, etc.). If this data becomes corrupted (due to database migration errors, manual edits, or encoding issues), it can cause API endpoints to return 500 errors.

This script:
1. Scans all VoiceProfile records
2. Identifies fields with malformed JSON
3. Normalizes them to valid JSON (returning safe defaults like `[]` or `{}`)
4. Reports what was fixed

### Usage

**Dry-run mode** (see what would be fixed without making changes):
```bash
python scripts/repair_malformed_json.py --dry-run
```

**Verbose mode** (show detailed information about each profile):
```bash
python scripts/repair_malformed_json.py --verbose
```

**Apply fixes** (actually repair the database):
```bash
python scripts/repair_malformed_json.py
```

**Combine options:**
```bash
python scripts/repair_malformed_json.py --dry-run --verbose
```

### Example Output

```
============================================================
VoiceProfile JSON Field Repair Script
============================================================
Running in DRY-RUN mode (no changes will be saved)
Found 3 profile(s) to check
Profile 1: Found 2 field(s) with malformed JSON
  - platforms:
      Original: [invalid json
      Repaired: []
  - brand_keywords:
      Original: {"not": "a list"}
      Repaired: []
Profile 1: Would repair (dry-run mode)
Profile 2: All JSON fields valid
Profile 3: All JSON fields valid

============================================================
Summary
============================================================
Total profiles checked: 3
Profiles with malformed JSON: 1
Total fields repaired: 2

Note: This was a dry-run. No changes were saved.
Run without --dry-run to apply fixes.
```

### When to Use

- After database migrations that may have corrupted data
- When logs show JSON decode errors from VoiceProfile fields
- As part of database maintenance/cleanup
- Before major releases to ensure data integrity

### Safety

- Always run with `--dry-run` first to preview changes
- The script uses the same safe parsing/serialization functions as the application code
- Malformed data is replaced with safe defaults (empty lists `[]` or empty dicts `{}`)
- Original data is logged before repair for audit purposes

### Prevention

The application now uses safe JSON serialization in all VoiceProfile setters:
- `safe_json_dumps_list()` - validates list data before storing
- `safe_json_dumps_dict()` - validates dict data before storing

This prevents new malformed JSON from being introduced through normal API usage.
