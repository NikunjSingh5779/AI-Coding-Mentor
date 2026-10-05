# ADR 0001 — Screen Source and Automatic Code Discovery

**Date:** 2026-10-04

**Status:** Accepted for planning; implementation still blocked by Q2–Q7.

## Context

The product needs a screen-monitoring mode in addition to the in-browser editor. The desired learner experience is a floating AI mentor that can watch a permitted screen, find the code without repeated manual region selection, identify affected lines, and provide progressive hints. The existing plan already requires explicit screen consent, no raw frame persistence, OCR confidence gating and a read-back view.

## Decision

Q1 is decided as **both editor and screen source**, with the editor built first and screen mode second. Screen mode uses **automatic code-region discovery and tracking as the default workflow**. Manual region selection is a fallback/override when confidence is low, when the detector loses the editor, or when the learner explicitly wants to constrain the region.

The floating mentor is a presentation layer available in both editor and screen modes. In screen mode it receives detected region geometry and positions itself near the affected code without obstructing it. It never decides whether code is wrong; only verified diagnostics enter the mentor engine.

## Design consequences

- Add FR-27 for automatic code-region discovery/tracking.
- Add FR-28 for the floating mentor overlay.
- Add `backend/app/vision/code_region_detect.py` and `backend/app/vision/region_tracking.py`.
- Add `frontend/src/features/mentor/FloatingMentor.tsx` and `overlayPosition.ts`.
- Evaluate region precision/recall, intersection-over-union, false-region rate, reacquisition and latency before considering a dedicated vision model.
- Low-confidence region detection produces no diagnostics and exposes the manual fallback.
- The existing OCR bake-off remains necessary because a correct region can still produce incorrect OCR.
- Screen capture remains permissioned through the browser; raw frames are not stored and screen/code content is not logged.

## Alternatives considered

1. **Manual region selection only.** Rejected as the normal workflow because it does not meet the desired hands-off mentor experience; retained only as fallback.
2. **LLM/vision model reads the entire screen and decides where code is.** Rejected as the primary architecture because region selection needs deterministic measurement, privacy minimisation and predictable latency; a model can be evaluated later as a candidate detector.
3. **VS Code extension first.** Deferred. It gives exact code positions but would not satisfy the web-based screen-monitoring requirement by itself.

## Safety and privacy

The learner explicitly permits the capture surface. The detector is not allowed to bypass browser capture controls. Raw frames are not persisted. Region and OCR outputs are treated as data, not instructions, and low-confidence states must not create learner diagnostics.
