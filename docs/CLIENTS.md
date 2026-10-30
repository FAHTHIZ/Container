<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Clients and Distribution

**Status:** target platform strategy. Native packaging choices require implementation spikes and platform testing.

## 1. One product on every device

Container should work on mobile, tablet, desktop, and browser. It must not become three different products with separate databases, workflows, or feature semantics.

All clients authenticate against the same service, use the same versioned APIs, and access the same personal facility, conversations, projects, models, agents, jobs, and artifacts. Client capability differences are explicit: a phone can control remote training even when it cannot run that training locally.

## 2. Browser

- Responsive browser application is the broadest-access entry point.
- Installable PWA behavior is a useful option where the browser supports it.
- Core chat and Core activity panel work at narrow and wide viewports.
- File uploads, camera/file pickers, clipboard paste, and drag-and-drop degrade gracefully by device.
- Browser offline behavior is limited to cached shell and unsent drafts; remote operations need a connection.

## 3. Android

- Provide a signed APK for direct installation where distribution policy permits.
- Use the appropriate Android App Bundle/store publishing route for Google Play distribution.
- Treat Android as a full conversation and facility-control client, not a training worker by default.
- Support secure credential storage, notifications, upload retry, resumable transfers where supported, background-safe status refresh, and accessibility.
- Keep high-volume downloads, model weights, and training off the phone unless a user explicitly chooses a supported local operation.
- Background work should respect Android lifecycle and battery/data policies; remote jobs continue on the server.

A native Android implementation or cross-platform shell must be selected through a prototype that tests secure storage, notifications, file access, deep links, streaming, background lifecycle, and release size.

## 4. Desktop

- Provide signed installers for Windows, macOS, and Linux.
- Offer the same chat-first experience and Core panel.
- Optionally pair the desktop with a local worker for supported local inference, preprocessing, or training workloads.
- Local worker operation is an explicit opt-in with resource caps and a visible indicator.
- The desktop app must not require users to expose a local service to the public internet.

A web-based shared UI in a desktop shell is a reasonable starting point, but the packaging/runtime choice should be validated against local worker integration, filesystem permissions, code signing, auto-update, and platform requirements.

## 5. Self-hosted/server

An optional server deployment is intended for advanced users and operators. It runs the control plane, storage integration, configured inference provider, and workers. It should expose the same browser UI and APIs.

Self-hosting is not the default onboarding route. The operator must provide secrets, database, object storage, inference backend, network policy, and backup/restore operations. A server install with no configured inference provider must clearly report that the built-in assistant is unavailable until setup is complete.

## 6. Shared experience contract

- One conversation model and consistent task states.
- One Core activity vocabulary and consistent approval semantics.
- Shared project, model, artifact, and job identifiers.
- Server-side authorization regardless of client.
- Client-specific capabilities advertised by the server.
- Responsive and accessible interaction; do not merely shrink a desktop dashboard.
- Versioned API compatibility and graceful client upgrade paths.

## 7. Distribution and release

- Reproducible signed artifacts.
- Automated dependency and license checks.
- Release notes, checksums, provenance, and rollback/previous-version guidance.
- Store policy and privacy disclosure review.
- No secrets, provider credentials, or private training datasets in client bundles.
- Test low-bandwidth uploads, interrupted sessions, reconnect, long-running remote tasks, and older supported devices.
