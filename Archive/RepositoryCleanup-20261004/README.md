# Retained cleanup material

`root-scratch/` contains fork-only one-shot probes, outputs and redundant trace
wrappers removed from the root. Scripts may contain absolute paths, stale
timestamps or mutations; **do not run them as supported tools**. They remain
available for inspecting old decisions. `before-docs/` preserves the exact
README, START-HERE, AGENTS and dirty ignore rules seen before cleanup.

The move list and SHA256 hashes are in
`Diagnostics/RepositoryCleanup-20261004/archive-manifest.csv`. Restore by
copying the named archive file to its original root path after checking that
the destination does not already contain newer work. No file bytes were deleted.

Existing dated Diagnostics runs and Historical-Handoffs remain in place because
their paths are linked or pinned. They are a logical evidence archive; they
are not supported startup entry points or current instructions.
