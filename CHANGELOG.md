# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed
- Application restructured into a Flask app package with per-domain blueprints.
- Configuration is now loaded from environment variables (see `.env.example`).
- New user signups now have passwords hashed with bcrypt; legacy plaintext records remain readable during the back-fill (JIRA-4421).

### Added
- Multi-service `docker-compose.yml` covering the app, MongoDB, MailHog, OpenLDAP, and dex.
- Base Jinja template (`app/templates/base.html`) for future pages.
- Project `CHANGELOG.md`.

## [0.3.0] - 2026-03-12

### Added
- Internal weekly report endpoint for the ops team.

### Fixed
- Reset link expiry now matches the message shown to the user.

## [0.2.0] - 2026-01-28

### Added
- Admin feedback workflow with points.
- Leaderboard view.

## [0.1.0] - 2025-11-04

### Added
- Initial release: signup, login, slot booking, admin approval.
