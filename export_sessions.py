#!/usr/bin/env python3
"""
Daily session export + push to GitHub.
Exports new Hermes sessions to markdown, sorts into sessions/YYYY-MM/ folders,
commits, and pushes to repo.
"""
import os
import sys
import subprocess
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Config
REPO_DIR = Path.home() / "projects" / "hermes-notes"
SESSIONS_DIR = REPO_DIR / "sessions"
STATE_FILE = REPO_DIR / ".exported_sessions.json"
HERMES_SESSIONS_DB = Path.home() / ".hermes" / "state.db"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_URL = "https://github.com/Sopandii/hermes-notes.git"

# GitHub PAT patterns: ghp_, gho_, ghu_, ghs_, ghr_ followed by 30+ alphanumeric chars
GITHUB_PAT_RE = re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')

def run(cmd, cwd=None, check=True):
    """Run shell command, return (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}", file=sys.stderr)
        print(f"stderr: {result.stderr}", file=sys.stderr)
        return result.stdout, result.stderr, result.returncode
    return result.stdout, result.stderr, result.returncode

def get_exported_session_ids():
    """Load set of already-exported session IDs from state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            data = json.load(f)
            return set(data.get("exported", []))
    return set()

def mark_exported(session_id):
    """Add session ID to state file."""
    exported = get_exported_session_ids()
    exported.add(session_id)
    with open(STATE_FILE, "w") as f:
        json.dump({"exported": sorted(exported), "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)

def _scrub_pat_tokens(filepath):
    """Redact GitHub Personal Access Tokens from exported session markdown."""
    try:
        content = Path(filepath).read_text()
        if not content:
            return
        scrubbed = GITHUB_PAT_RE.sub('[REDACTED]', content)
        if scrubbed != content:
            Path(filepath).write_text(scrubbed)
            print(f"    ⚠️  Scrubbed GitHub PAT from {filepath.name}")
    except Exception as e:
        print(f"    Warning: failed to scrub {filepath}: {e}", file=sys.stderr)

def _get_month_folder(session_id):
    """Derive YYYY-MM folder from session ID (format: YYYYMMDD_HHMMSS_hash)."""
    m = re.match(r'(\d{4})(\d{2})\d{2}_\d{6}_', session_id)
    if m:
        year, month = m.group(1), m.group(2)
        return SESSIONS_DIR / f"{year}-{month}"
    return SESSIONS_DIR  # fallback

def export_session(session_id):
    """Export a single session to markdown via hermes CLI, sorted into month folder."""
    print(f"Exporting session {session_id}...")
    
    # Run hermes sessions export
    stdout, stderr, rc = run(
        f"hermes sessions export --session-id {session_id} --format md",
        check=False
    )
    
    if rc != 0:
        print(f"Export failed for {session_id}: {stderr}", file=sys.stderr)
        return None
    
    # Parse exported path from stdout
    match = re.search(r'to\s+(/\S+\.md)', stdout)
    if not match:
        print(f"  Could not determine export path from: {stdout[:200]}", file=sys.stderr)
        return None
    
    src_path = Path(match.group(1))
    if not src_path.exists():
        print(f"  Exported file not found: {src_path}", file=sys.stderr)
        return None
    
    # Determine target folder (YYYY-MM)
    month_folder = _get_month_folder(session_id)
    month_folder.mkdir(parents=True, exist_ok=True)
    
    # Build safe filename
    safe_name = session_id.replace("/", "_").replace(" ", "-")
    out_path = month_folder / f"{safe_name}.md"
    
    # Copy to sessions/YYYY-MM/ folder
    shutil.copy2(src_path, out_path)
    print(f"  -> {out_path} (in {month_folder.name}/)")
    
    # Scrub GitHub PATs from the exported content before committing
    _scrub_pat_tokens(out_path)
    return str(out_path)

def commit_and_push():
    """Git add, commit, push new files."""
    print("Committing and pushing...")
    
    # Configure git identity for cron (use env or defaults)
    run(f"git config user.email 'cron@hermes-notes.local'", cwd=REPO_DIR)
    run(f"git config user.name 'Hermes Session Exporter'", cwd=REPO_DIR)
    
    # Add new/changed files (sessions/ + skills/)
    stdout, _, rc = run("git add sessions/ skills/", cwd=REPO_DIR, check=False)
    
    # Check if there's anything to commit
    stdout, _, rc = run("git diff --cached --quiet", cwd=REPO_DIR, check=False)
    if rc == 0:
        print("  No changes to commit.")
        return
    
    # Commit
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    run(f'git commit -m "auto-export: sessions as of {timestamp}"', cwd=REPO_DIR)
    
    # Push (use token in URL if available)
    if GITHUB_TOKEN:
        remote_url = f"https://{GITHUB_TOKEN}@github.com/Sopandii/hermes-notes.git"
        run(f"git push {remote_url} main", cwd=REPO_DIR)
    else:
        run("git push origin main", cwd=REPO_DIR)
    
    print("  Push complete.")

def main():
    print(f"=== Session Export Cron ({datetime.now(timezone.utc).isoformat()}) ===")
    
    # Ensure sessions dir exists
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load already-exported session IDs
    exported = get_exported_session_ids()
    print(f"Already exported: {len(exported)} sessions")
    
    # Get all session IDs from state.db (SQLite)
    try:
        import sqlite3
        conn = sqlite3.connect(HERMES_SESSIONS_DB)
        cursor = conn.execute(
            "SELECT id FROM sessions ORDER BY started_at DESC"
        )
        all_session_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"Total sessions in DB: {len(all_session_ids)}")
    except Exception as e:
        print(f"Failed to query sessions DB: {e}", file=sys.stderr)
        # Fallback: use hermes CLI to list sessions
        stdout, _, _ = run("hermes sessions list --limit 100")
        # Parse session IDs from the table output (last column)
        session_ids = []
        for line in stdout.split('\n'):
            match = re.search(r'\b(\d{8}_\d{6}_\w{6})\b', line)
            if match:
                session_ids.append(match.group(1))
        all_session_ids = session_ids
        print(f"Fallback: found {len(all_session_ids)} sessions via CLI")
    
    # Find new sessions
    new_sessions = [sid for sid in all_session_ids if sid not in exported]
    print(f"New sessions to export: {len(new_sessions)}")
    
    if not new_sessions:
        print("No new sessions. Done.")
        return
    
    # Export each new session
    exported_count = 0
    for session_id in new_sessions:
        result = export_session(session_id)
        if result:
            mark_exported(session_id)
            exported_count += 1
    
    print(f"Exported {exported_count} new sessions.")
    
    # Commit and push
    commit_and_push()
    
    print("=== Done ===")

if __name__ == "__main__":
    main()
