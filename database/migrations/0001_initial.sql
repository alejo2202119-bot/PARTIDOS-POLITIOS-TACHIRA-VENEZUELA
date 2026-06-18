-- ============================================================================
--  Migration 0001 — initial schema
--
--  For environments that use a migration runner instead of the docker-entrypoint
--  init scripts, apply the canonical schema and seed in order:
--
--      \i ../schema.sql
--      \i ../seed.sql
--
--  This file is intentionally a thin pointer so there is a single source of
--  truth (database/schema.sql). Subsequent migrations (0002_*, 0003_*) should
--  contain only incremental ALTERs.
-- ============================================================================

\echo 'Applying VPID initial schema...'
\i schema.sql
\echo 'Loading reference/seed data...'
\i seed.sql
\echo 'Migration 0001 complete.'
