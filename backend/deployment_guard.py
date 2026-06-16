"""
Deployment Guard Module
=======================
Prevents live vs preview deployment mismatches by:
1. Tracking build metadata (timestamps, hashes, revisions)
2. Validating deployed bundles against source files
3. Surfacing build info in /api/health
4. Warning when source files are newer than deployed bundle

Usage:
    from deployment_guard import get_build_info, validate_deployment, log_deployment_status
"""

import os
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Paths
FRONTEND_DIR = Path("/app/frontend")
BACKEND_DIR = Path("/app/backend")
WEB_DIST_DIR = BACKEND_DIR / "web_dist"  # Where backend serves from
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"  # Where expo exports to
COMPONENTS_DIR = FRONTEND_DIR / "components"

# ---------------------------------------------------------------------------
# Source-file tracking for staleness detection
# ---------------------------------------------------------------------------
# Two complementary mechanisms are used to detect a stale `backend/web_dist/`:
#
#   1. `CRITICAL_SOURCE_FILES` — a curated, individually-tracked list. Each
#      entry surfaces in `/api/health → build.source_files.tracked_files`
#      so individual files can be inspected (hash, mtime). Keep this list
#      focused on files whose individual identity matters operationally.
#
#   2. `SCANNED_FRONTEND_DIRS` — directories that are walked recursively;
#      the newest mtime across the walk is folded into the staleness check.
#      This is the safety net: ANY change anywhere under these dirs will
#      force a rebuild requirement, so a new component / route / service
#      that nobody remembered to add to the curated list still triggers
#      the guard. This is what would have prevented the June 14 vs June 16
#      `mel-rising-fix` slippage (the curated list had only 8 components,
#      none of which were touched by the fix).
#
# Both mechanisms feed into the same final `validate_deployment()` check.
CRITICAL_SOURCE_FILES = [
    # Curated list — kept small for explicit per-file reporting.
    # The dir scan below is the catch-all.
    "app/_layout.tsx",
    "app/index.tsx",
    "app/(tabs)/index.tsx",
    "app/(tabs)/lenses.tsx",
    "app/(tabs)/patterns.tsx",
    "app/(tabs)/reflect.tsx",
    "app/forums/[id].tsx",
    "services/api.ts",
    "components/MirrorChat.tsx",
    "components/ForumChatView.tsx",
    "components/NumerologySummaryV2.tsx",
    "components/NumerologyDeepDiveV2.tsx",
    "components/NumerologyLensView.tsx",
    "components/InsightCardFooter.tsx",
    "components/astrology/AstrologyTodayTab.tsx",
    "components/astrology/AstrologyDeepDiveTab.tsx",
    "app.json",
    "package.json",
]

# Directory roots that ship into the web bundle. Walked recursively, with
# the exclusion set below applied. Anything modified under these roots is
# considered "newer than the bundle" if its mtime > index.html mtime.
SCANNED_FRONTEND_DIRS = [
    "app",
    "components",
    "services",
    "hooks",
    "utils",
    "store",
    "contexts",
    "constants",
    "types",
]

# File suffixes whose mtimes participate in staleness detection.
# (Other files — fixtures, READMEs, sample data — are intentionally ignored
# so editing a Markdown doc doesn't force a needless rebuild.)
SCANNED_FILE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".json")

# Directory / pattern fragments to skip during the walk. These NEVER ship
# into the bundle so a change inside them must not flip is_current → False.
SCAN_EXCLUDE_FRAGMENTS = (
    "node_modules", "/.expo", "/dist", "/.git", "/__pycache__", "/.cache",
    "/.next", "/.turbo", "/.vercel",
)


def get_file_mtime(filepath: Path) -> Optional[datetime]:
    """Get file modification time as datetime."""
    try:
        if filepath.exists():
            return datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
    except Exception:
        pass
    return None


def get_file_hash(filepath: Path, first_n_bytes: int = 8192) -> Optional[str]:
    """Get SHA256 hash of first N bytes of a file."""
    try:
        if filepath.exists():
            with open(filepath, 'rb') as f:
                content = f.read(first_n_bytes)
                return hashlib.sha256(content).hexdigest()[:12]
    except Exception:
        pass
    return None


def get_git_revision() -> Optional[str]:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd='/app',
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_dirty() -> bool:
    """Check if there are uncommitted changes."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd='/app',
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def find_entry_bundle() -> Optional[Path]:
    """Find the main entry bundle in web_dist."""
    js_dir = WEB_DIST_DIR / "_expo" / "static" / "js" / "web"
    if js_dir.exists():
        for f in js_dir.glob("entry-*.js"):
            return f
    return None


def get_deployed_bundle_info() -> Dict[str, Any]:
    """Get info about the currently deployed web bundle."""
    info = {
        "deployed": False,
        "index_html_mtime": None,
        "bundle_hash": None,
        "bundle_name": None,
        "bundle_size_kb": None,
    }
    
    # Check index.html
    index_html = WEB_DIST_DIR / "index.html"
    if index_html.exists():
        info["deployed"] = True
        info["index_html_mtime"] = get_file_mtime(index_html)
    
    # Find entry bundle
    entry_bundle = find_entry_bundle()
    if entry_bundle:
        info["bundle_name"] = entry_bundle.name
        info["bundle_hash"] = get_file_hash(entry_bundle)
        info["bundle_size_kb"] = round(entry_bundle.stat().st_size / 1024, 1)
    
    return info


def get_source_files_info() -> Dict[str, Any]:
    """Get info about critical source files.

    Returns the curated `CRITICAL_SOURCE_FILES` per-file detail PLUS the
    newest mtime / file path discovered by walking `SCANNED_FRONTEND_DIRS`
    (the safety net). The `newest_source_mtime` / `newest_source_file`
    fields are the MAX across BOTH sources, so a brand-new component or
    route that nobody remembered to add to the curated list still
    participates in staleness detection."""
    info: Dict[str, Any] = {
        "newest_source_mtime": None,
        "newest_source_file": None,
        "tracked_files": {},
        "scanned_dirs": {
            "roots":        list(SCANNED_FRONTEND_DIRS),
            "file_count":   0,
            "newest_mtime": None,
            "newest_file":  None,
        },
    }

    newest_mtime: Optional[datetime] = None
    newest_file: Optional[str] = None

    # (1) Curated list — explicit per-file tracking.
    for rel_path in CRITICAL_SOURCE_FILES:
        full_path = FRONTEND_DIR / rel_path
        mtime = get_file_mtime(full_path)
        if mtime:
            info["tracked_files"][rel_path] = {
                "mtime": mtime.isoformat(),
                "hash": get_file_hash(full_path),
            }
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime
                newest_file = rel_path

    # (2) Directory walk — safety net. Walk SCANNED_FRONTEND_DIRS and find
    # the newest .ts/.tsx/.js/.jsx/.json modification.
    scan_newest: Optional[datetime] = None
    scan_newest_path: Optional[str] = None
    scan_count = 0
    for root_name in SCANNED_FRONTEND_DIRS:
        root = FRONTEND_DIR / root_name
        if not root.exists():
            continue
        try:
            for path in root.rglob("*"):
                # Skip excluded fragments.
                s = str(path)
                if any(frag in s for frag in SCAN_EXCLUDE_FRAGMENTS):
                    continue
                if not path.is_file():
                    continue
                if path.suffix not in SCANNED_FILE_SUFFIXES:
                    continue
                scan_count += 1
                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                except Exception:
                    continue
                if scan_newest is None or mtime > scan_newest:
                    scan_newest = mtime
                    scan_newest_path = str(path.relative_to(FRONTEND_DIR))
        except Exception:  # pragma: no cover — defensive on filesystem oddities
            continue

    info["scanned_dirs"]["file_count"]   = scan_count
    info["scanned_dirs"]["newest_mtime"] = scan_newest.isoformat() if scan_newest else None
    info["scanned_dirs"]["newest_file"]  = scan_newest_path

    # (3) Roll up the max across BOTH sources.
    if scan_newest and (newest_mtime is None or scan_newest > newest_mtime):
        newest_mtime = scan_newest
        newest_file = scan_newest_path

    # Also check top-level Expo config files that are NOT inside the
    # SCANNED_FRONTEND_DIRS roots — these are bundled-relevant.
    for top_level in ("app.json", "package.json", "metro.config.js"):
        p = FRONTEND_DIR / top_level
        if not p.exists():
            continue
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        except Exception:
            continue
        if newest_mtime is None or mtime > newest_mtime:
            newest_mtime = mtime
            newest_file = top_level

    info["newest_source_mtime"] = newest_mtime
    info["newest_source_file"] = newest_file

    return info


def validate_deployment() -> Dict[str, Any]:
    """
    Validate that deployed bundle is up-to-date with source files.
    Returns validation result with warnings/errors.
    """
    result = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "stale_files": [],
    }
    
    bundle_info = get_deployed_bundle_info()
    source_info = get_source_files_info()
    
    # Check if bundle exists
    if not bundle_info["deployed"]:
        result["valid"] = False
        result["errors"].append("No deployed web bundle found in web_dist/")
        return result
    
    # Check if source is newer than deployed bundle
    if bundle_info["index_html_mtime"] and source_info["newest_source_mtime"]:
        if source_info["newest_source_mtime"] > bundle_info["index_html_mtime"]:
            result["valid"] = False
            result["errors"].append(
                f"STALE DEPLOYMENT: Source file '{source_info['newest_source_file']}' "
                f"({source_info['newest_source_mtime'].strftime('%Y-%m-%d %H:%M:%S')}) "
                f"is newer than deployed bundle ({bundle_info['index_html_mtime'].strftime('%Y-%m-%d %H:%M:%S')})"
            )

            # Curated-list stale files
            seen: set = set()
            for rel_path, file_info in source_info["tracked_files"].items():
                file_mtime = datetime.fromisoformat(file_info["mtime"])
                if file_mtime > bundle_info["index_html_mtime"]:
                    result["stale_files"].append({
                        "file": rel_path,
                        "modified": file_info["mtime"],
                        "source": "curated",
                    })
                    seen.add(rel_path)

            # Safety-net stale file from the dir scan — always attribute the
            # newest_file even if it wasn't on the curated list. Without this,
            # a newly-added component would silently trigger an error
            # message but leave `stale_files` empty.
            scan_newest = source_info.get("scanned_dirs", {}).get("newest_file")
            scan_mtime  = source_info.get("scanned_dirs", {}).get("newest_mtime")
            if scan_newest and scan_newest not in seen and scan_mtime:
                try:
                    scan_dt = datetime.fromisoformat(scan_mtime)
                    if scan_dt > bundle_info["index_html_mtime"]:
                        result["stale_files"].append({
                            "file": scan_newest,
                            "modified": scan_mtime,
                            "source": "dir-scan",
                        })
                except Exception:
                    pass
    
    # Check for uncommitted changes
    if get_git_dirty():
        result["warnings"].append("Uncommitted git changes detected")
    
    return result


def get_build_info() -> Dict[str, Any]:
    """
    Get comprehensive build information for /api/health and debugging.
    """
    bundle_info = get_deployed_bundle_info()
    source_info = get_source_files_info()
    validation = validate_deployment()
    
    # Format timestamps for display
    bundle_mtime_str = None
    source_mtime_str = None
    
    if bundle_info["index_html_mtime"]:
        bundle_mtime_str = bundle_info["index_html_mtime"].strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if source_info["newest_source_mtime"]:
        source_mtime_str = source_info["newest_source_mtime"].strftime("%Y-%m-%d %H:%M:%S UTC")
    
    return {
        "git_revision": get_git_revision(),
        "git_dirty": get_git_dirty(),
        "deployed_bundle": {
            "timestamp": bundle_mtime_str,
            "hash": bundle_info["bundle_hash"],
            "name": bundle_info["bundle_name"],
            "size_kb": bundle_info["bundle_size_kb"],
        },
        "source_files": {
            "newest_modified": source_mtime_str,
            "newest_file": source_info["newest_source_file"],
            "tracked_count": len(source_info["tracked_files"]),
            # Surface the dir-scan stats so `/api/health` consumers can see
            # both detection mechanisms at a glance.
            "scanned_dirs": source_info.get("scanned_dirs", {}),
        },
        "validation": {
            "is_current": validation["valid"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
            "stale_files_count": len(validation["stale_files"]),
        },
        "env_build_id": os.environ.get("EXPO_PUBLIC_BUILD_ID", "unknown"),
    }


# =============================================================================
# Prepublish CLI — exit 1 if the deployed bundle would be stale.
# =============================================================================
# Usage:
#     python /app/backend/deployment_guard.py prepublish [--json] [--force]
#
# Behaviour:
#   * Walks `SCANNED_FRONTEND_DIRS` + the curated `CRITICAL_SOURCE_FILES` and
#     compares the newest mtime against `backend/web_dist/index.html`.
#   * Exits 0 if `web_dist/` is at least as fresh as every relevant source.
#   * Exits 1 (with a human-readable + JSON report) if any tracked source
#     is newer than the deployed bundle. The reported `stale_files` list
#     names every file the operator must commit-into-the-bundle before
#     Publishing.
#   * `--force` flag returns exit 0 even if stale (escape hatch for the
#     rare case where the operator is intentionally publishing without
#     a rebuild). It is logged loudly.
#   * `--json` flag emits machine-readable JSON instead of the default
#     coloured human report.
#
# Designed to be invoked from `/app/prepublish.sh` (the wrapper) before
# the user clicks Publish in the Emergent dashboard.
def prepublish_cli(argv: Optional[List[str]] = None) -> int:
    """CLI entry. Returns the exit code (do not raise SystemExit here so
    tests can call directly)."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="deployment_guard prepublish",
        description=(
            "Verify that /app/backend/web_dist/ is at least as fresh as "
            "the relevant /app/frontend/ sources. Exits 1 if a rebuild "
            "is required before Publish."
        ),
    )
    parser.add_argument("subcommand", choices=["prepublish"],
                        help="Reserved for future subcommands.")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of a human-readable report.")
    parser.add_argument("--force", action="store_true",
                        help="Return exit 0 even if stale (logged loudly).")
    args = parser.parse_args(argv)

    bundle_info = get_deployed_bundle_info()
    source_info = get_source_files_info()
    validation = validate_deployment()

    bundle_mtime = bundle_info["index_html_mtime"]
    newest_mtime = source_info["newest_source_mtime"]

    payload = {
        "ok": validation["valid"],
        "forced": bool(args.force),
        "bundle": {
            "present":    bundle_info["deployed"],
            "name":       bundle_info["bundle_name"],
            "hash":       bundle_info["bundle_hash"],
            "size_kb":    bundle_info["bundle_size_kb"],
            "mtime":      bundle_mtime.isoformat() if bundle_mtime else None,
        },
        "source": {
            "newest_file":  source_info["newest_source_file"],
            "newest_mtime": newest_mtime.isoformat() if newest_mtime else None,
            "tracked_count": len(source_info["tracked_files"]),
            "scanned_dirs":  source_info.get("scanned_dirs", {}),
        },
        "stale_files": validation["stale_files"],
        "errors":      validation["errors"],
        "warnings":    validation["warnings"],
        "rebuild_command": "cd /app/frontend && yarn build:deploy",
    }

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        # Human-readable, terminal-friendly report.
        OK = "\033[32m"
        FAIL = "\033[31m"
        WARN = "\033[33m"
        DIM = "\033[2m"
        RST = "\033[0m"
        verdict = f"{OK}PASS{RST}" if validation["valid"] else f"{FAIL}FAIL{RST}"
        print("=== DeploymentGuard Prepublish Check ===")
        print(f"  Verdict        : {verdict}")
        print(f"  Bundle file    : {bundle_info['bundle_name']}")
        print(f"  Bundle mtime   : {bundle_mtime}")
        print(f"  Newest source  : {source_info['newest_source_file']}")
        print(f"  Newest mtime   : {newest_mtime}")
        sd = source_info.get("scanned_dirs", {})
        print(f"  Dir-scan stats : {sd.get('file_count', 0)} files across "
              f"{len(sd.get('roots', []))} roots; "
              f"newest={sd.get('newest_file')} @ {sd.get('newest_mtime')}")
        if validation["errors"]:
            print(f"\n{FAIL}ERRORS:{RST}")
            for e in validation["errors"]:
                print(f"  ❌ {e}")
        if validation["warnings"]:
            print(f"\n{WARN}WARNINGS:{RST}")
            for w in validation["warnings"]:
                print(f"  ⚠️  {w}")
        if validation["stale_files"]:
            print(f"\n{WARN}STALE FILES (newer than bundle):{RST}")
            for sf in validation["stale_files"][:25]:
                print(f"  - {sf['file']}  ({sf['modified']})")
            if len(validation["stale_files"]) > 25:
                print(f"  ... and {len(validation['stale_files']) - 25} more")
            print(f"\n{DIM}To rebuild:  cd /app/frontend && yarn build:deploy{RST}")

    if validation["valid"]:
        return 0
    if args.force:
        # Loudly logged force-override
        logger.warning("[DeploymentGuard.prepublish] STALE bundle accepted via --force")
        return 0
    return 1


def log_deployment_status():
    """
    Log deployment status at startup.
    Called during server initialization.
    """
    build_info = get_build_info()
    validation = validate_deployment()
    
    logger.info("=" * 60)
    logger.info("[DeploymentGuard] BUILD STATUS")
    logger.info("=" * 60)
    logger.info(f"  Git Revision: {build_info['git_revision']}{'*' if build_info['git_dirty'] else ''}")
    logger.info(f"  Deployed Bundle: {build_info['deployed_bundle']['name']}")
    logger.info(f"  Bundle Hash: {build_info['deployed_bundle']['hash']}")
    logger.info(f"  Bundle Timestamp: {build_info['deployed_bundle']['timestamp']}")
    logger.info(f"  Newest Source: {build_info['source_files']['newest_file']}")
    logger.info(f"  Source Timestamp: {build_info['source_files']['newest_modified']}")
    logger.info(f"  Deployment Valid: {'YES' if validation['valid'] else 'NO'}")
    
    if validation["errors"]:
        logger.error("-" * 60)
        logger.error("[DeploymentGuard] DEPLOYMENT ERRORS:")
        for error in validation["errors"]:
            logger.error(f"  ❌ {error}")
        logger.error("-" * 60)
    
    if validation["warnings"]:
        logger.warning("[DeploymentGuard] Warnings:")
        for warning in validation["warnings"]:
            logger.warning(f"  ⚠️ {warning}")
    
    if validation["stale_files"]:
        logger.warning(f"[DeploymentGuard] {len(validation['stale_files'])} files modified since last deploy:")
        for sf in validation["stale_files"][:5]:  # Show first 5
            logger.warning(f"  - {sf['file']}")
        if len(validation["stale_files"]) > 5:
            logger.warning(f"  ... and {len(validation['stale_files']) - 5} more")
    
    logger.info("=" * 60)
    
    return validation["valid"]


def get_build_stamp() -> str:
    """
    Get a short build stamp for display in app footer.
    Format: "v{git_rev}-{bundle_hash}"
    """
    git_rev = get_git_revision() or "unknown"
    bundle_info = get_deployed_bundle_info()
    bundle_hash = bundle_info["bundle_hash"] or "unknown"
    
    return f"v{git_rev}-{bundle_hash[:6]}"


# Export for use in health endpoint
__all__ = [
    'get_build_info',
    'validate_deployment',
    'log_deployment_status',
    'get_build_stamp',
    'prepublish_cli',
    'CRITICAL_SOURCE_FILES',
    'SCANNED_FRONTEND_DIRS',
]


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(prepublish_cli(_sys.argv[1:]))
