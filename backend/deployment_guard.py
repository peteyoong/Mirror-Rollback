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
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Paths
FRONTEND_DIR = Path("/app/frontend")
BACKEND_DIR = Path("/app/backend")
WEB_DIST_DIR = BACKEND_DIR / "web_dist"  # Where backend serves from
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"  # Where expo exports to
COMPONENTS_DIR = FRONTEND_DIR / "components"

# Critical source files to track for staleness detection
CRITICAL_SOURCE_FILES = [
    "components/NumerologySummaryV2.tsx",
    "components/NumerologyDeepDiveV2.tsx",
    "components/NumerologyLensView.tsx",
    "components/InsightCardFooter.tsx",
    "components/astrology/AstrologyTodayTab.tsx",
    "components/astrology/AstrologyDeepDiveTab.tsx",
    "app/(tabs)/lenses.tsx",
    "app/(tabs)/index.tsx",
]


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
    """Get info about critical source files."""
    info = {
        "newest_source_mtime": None,
        "newest_source_file": None,
        "tracked_files": {},
    }
    
    newest_mtime = None
    newest_file = None
    
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
            
            # Find all stale files
            for rel_path, file_info in source_info["tracked_files"].items():
                file_mtime = datetime.fromisoformat(file_info["mtime"])
                if file_mtime > bundle_info["index_html_mtime"]:
                    result["stale_files"].append({
                        "file": rel_path,
                        "modified": file_info["mtime"],
                    })
    
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
        },
        "validation": {
            "is_current": validation["valid"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
            "stale_files_count": len(validation["stale_files"]),
        },
        "env_build_id": os.environ.get("EXPO_PUBLIC_BUILD_ID", "unknown"),
    }


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
]
