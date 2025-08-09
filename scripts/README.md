# Backward Compatibility Scripts Directory

⚠️ **DEPRECATED**: This directory contains temporary backward compatibility symlinks.

## Migration Notice

Scripts have been reorganized into the `/tools/` directory for better organization:

- **Build tools**: `./tools/build/`
- **Testing tools**: `./tools/testing/`
- **Release tools**: `./tools/release/`
- **Analysis tools**: `./tools/analysis/`
- **Maintenance tools**: `./tools/maintenance/`

## New Paths

| Old Path | New Path |
|----------|----------|
| `./scripts/run_all_tests.sh` | `./tools/testing/run_all_tests.sh` |
| `./scripts/release_to_pypi.sh` | `./tools/release/release_to_pypi.sh` |
| `./scripts/dead-code-analysis.py` | `./tools/analysis/dead-code-analysis.py` |
| `./scripts/clear_all_caches.sh` | `./tools/maintenance/clear_all_caches.sh` |

## Action Required

Please update your workflows and scripts to use the new paths. This compatibility directory will be removed in a future release.

**Updated CLAUDE.md** already contains the correct paths for all development commands.