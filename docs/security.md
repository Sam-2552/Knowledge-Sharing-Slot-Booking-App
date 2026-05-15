# Security Policy

This document captures the high-level security posture for the Knowledge
Sharing Portal. It complements the company-wide infosec handbook and is
intended as a quick reference for engineers working on this codebase.

## Authentication

The portal supports three authentication paths:

- **Corporate SSO** via the central OIDC provider. Preferred for staff.
- **Password login** for legacy automation accounts that pre-date SSO.
- **Magic links** for occasional external presenters and contractors.

All sessions are represented by a signed JWT cookie. Tokens expire after
24 hours and have to be re-issued by signing in again.

## Authorisation

Role assignment lives on the `users` table. Two roles are recognised:

| Role | Description |
|---|---|
| `user` | Default. Can book and edit their own slots, comment, and view the leaderboard. |
| `admin` | Can approve/reject bookings, leave feedback, import schedules, run the health console. |

There is no fine-grained ACL beyond the two roles. Audit logging for
admin actions is captured in the standard application log only.

## Network

In production the app sits behind nginx, which terminates TLS and
forwards `X-Forwarded-For`, `X-Forwarded-Host` and `X-Forwarded-Proto`
to the upstream. Outbound traffic from the app cluster is restricted by
the platform team's egress policy.

## Data handling

The portal stores user profile data, slot bookings, free-form feedback,
and comments. Materials uploaded by presenters live on a dedicated EFS
volume bind-mounted at `/app/uploads`.

Personal information is limited to the user's display name, email, and
optional bio. We do not store demographic data or payment information.

## Reporting

If you find a security issue, contact the platform team directly. Do
not file a public ticket. Confirmed issues are tracked in JIRA under
the SEC- key with restricted visibility.
