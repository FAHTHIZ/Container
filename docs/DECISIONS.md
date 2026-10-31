<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Architecture Decisions

## ADR-001 — Local-first, free, on-device

**Decision:** The primary Container deployment is free and runs locally or
on-device. Local model runtimes and local storage are the default path. Paid
managed services are never required and never the default. Any future managed
compute option must be explicitly opt-in and clearly labelled.

**Rationale:** The project has no budget for paid services. The product must
remain useful on a phone or laptop without subscriptions, billing, expiring
free tiers, or a required payment method.

**Date:** 2026-10-31.
