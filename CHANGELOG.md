# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version 2.2.3 (2025-03-30)
### Enhancements
 * Moved to `uv` for dependency management and `ruff` for formatting / styling / linting

## Verson 2.2.2 (2021-02-04)

### Enhancements
 * Added a MANIFEST.in so the source distribution can retain necessary requirements.txt file

## Verson 2.2.1 (2020-05-02)

### Enhancements
 * update tests without unittest only pytest (#62)
 * added additional docs to `Node` to reduce confusion noted in #73

### Bug Fixes
 * Fixed unexpected type conversion in buckets (#77)
 * Fixed issue with load_state not awaiting bootstrap (#78)
 * Fixed `KBucket.replacement_nodes` is never pruned (#79)

## Verson 2.2 (2019-02-04)
minor version update to handle long_description_content_type for pypi

## Verson 2.1 (2019-02-04)

### Bug Fixes
 * `KBucket.remove_node` removes nodes in replacement_nodes. (#66)
 * Improve `KBucket.split` (#65)
 * refacto(storage): use '@abstractmethod' instead of 'raise NotImplementedError' in Storage Interface (#61)
 * Asynchronous Server listening (#58) (#60)

## Version 2.0 (2019-01-09)

### Bug Fixes
 * Removed unused imports

### Deprecations
 * Removed all camelcase naming
