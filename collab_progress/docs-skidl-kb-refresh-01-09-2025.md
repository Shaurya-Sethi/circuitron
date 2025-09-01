# Docs: SKiDL Knowledge Base Refresh Guidance

## Summary
Added maintenance note to `SETUP.md` instructing users to periodically refresh the SKiDL knowledge bases after major SKiDL releases and to delete existing contents before repopulating.

## Files Changed
- SETUP.md

## Rationale
Keeping the SKiDL knowledge bases current prevents drift when upstream SKiDL introduces breaking changes, deprecations, or new features that Circuitron may leverage. Explicitly advising users to clear existing contents avoids mixing stale and new data.

## Verification
- Docs-only change; rendered Markdown locally. No code behavior modified. Test suite not impacted.

## Issues
- Exact Supabase table names and Neo4j labels vary by deployment; guidance remains intentionally high-level to avoid incorrect specifics.

## Next Steps
- If desired, add a small helper script to automate clearing SKiDL-related rows in Supabase and nodes/edges in Neo4j for a clean rebuild.
