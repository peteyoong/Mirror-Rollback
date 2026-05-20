"""
Backend route modules.

Build marker: server-router-refactor-v1

Each module here exposes a `register(api_router, db, logger)` function
that the main `server.py` calls to attach its routes onto the shared
`api_router`.  This keeps the migration risk-free:

    * No new prefixes or paths.
    * No new dependency-injection plumbing.
    * No circular imports — modules receive `db` + `logger` as args.
    * Existing endpoints can be migrated one at a time; the originals
      are removed from `server.py` in the SAME commit they are
      registered from a router module.

When all routes have moved here we can promote this to a real
package-of-routers with `Depends(get_db)` etc.  For now this is the
incremental, behavior-preserving step.
"""
