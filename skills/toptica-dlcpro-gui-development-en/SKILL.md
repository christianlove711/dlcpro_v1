---
name: toptica-dlcpro-gui-development-en
description: Develop, modify, review, or plan a PySide6-based custom control application for TOPTICA DLC pro. Use when working on DLC pro serial or network connection handling, parameter access, laser control, status monitoring, scan control, bilingual GUI interactions, or when validating implementation details against the official SDK and Manual.md. Use the official Python SDK as the authority for programming interfaces and Manual.md as the authority for device behavior, safety, wiring, and operating procedures.
---

# TOPTICA DLC pro GUI Development

Build a custom DLC pro control application with `PySide6` and the official TOPTICA Python SDK, with the goal of implementing full Python-side control of DLC pro functions rather than replacing only a single page from the official GUI.

Read [source-map.md](references/source-map.md) first to locate the official SDK and manual files in this repository.

## Goal

- Control DLC pro through the official SDK
- Build a custom GUI with PySide6
- Provide both Chinese and English in the GUI
- Follow `Manual.md` for device behavior, safety, wiring, and operating procedures
- Gradually implement DLC pro control capabilities in Python across the application

## Source Priority

Check sources in this order:

1. Official SDK documentation and official examples
2. Official device manual `Manual.md`
3. Existing project code
4. General inference

Only use inference when the first three do not answer the question, and clearly label it as inference rather than documented behavior.

## Source Responsibilities

Use the SDK as the authority for:

- Python imports
- Connection setup
- Parameter access patterns
- Read/write behavior
- Sync and async API behavior
- Official example control flows
- Confirmed interfaces and behavior for DLC pro version 3.3.3

Use `Manual.md` as the authority for:

- Safety constraints
- Emission and interlock behavior
- Wiring and hardware setup
- Module responsibilities
- Operating sequences
- Capability limits and upgrade-dependent behavior

Use existing project code as a reference for:

- Local application structure
- GUI/controller/service layering
- Existing integration patterns
- Project-local naming conventions

## Workflow

For each feature, follow this order:

1. Define the feature clearly.
   Examples: connect to device, read current, toggle emission, control scan, show status, plot signals, replace a page from the official GUI.
2. Check the SDK first to confirm the official interface and usage pattern.
3. Check `Manual.md` next to confirm device behavior, limits, and safety requirements.
4. Inspect the current project code last to determine how to integrate the feature locally.
5. If official sources and project code conflict, state the conflict and align the implementation with the official sources.
6. In the final explanation, state whether the implementation basis is SDK, manual, or project-local structure.

Before editing GUI structure, explicitly confirm one product-level decision from the user request or existing code:

- Is the feature meant to appear inside the main stacked page area, or in a separate popup `QMainWindow`?
- Is the task asking for a new function, a visual restyle, or both?
- Is the requested layout supposed to match the main window structurally, or only match its colors and controls?

Do not change the interaction model from popup window to stacked page, or the reverse, unless the user explicitly asks for that.

## Connection Module Requirements

- Treat serial and network connectivity as two distinct paths in the connection module.
- Serial communication depends on `pyserial`; include port discovery, connection failure handling, and serial-specific error paths in the design.
- Network connectivity depends on `ifaddr`; include local interface discovery, address selection, and network reachability concerns in the design.
- Keep connection logic out of the widget layer and prefer a dedicated connection or service layer.
- If the SDK already defines the correct connection abstraction, follow the SDK model instead of bypassing it with direct protocol handling.

## Hard Rules

- Do not invent APIs, parameter names, command names, return fields, or state names.
- Do not assume units, limits, defaults, enum values, or timing behavior.
- Do not treat an existing project parameter name as correct unless it is backed by official sources.
- If the SDK conflicts with the current implementation, call out the conflict and follow the SDK for programming behavior.
- If the manual and SDK cover different concerns, use the SDK for code-level interfaces and the manual for device behavior, safety, wiring, and operating procedures.
- If the official sources do not confirm a behavior, say so explicitly before making any minimal assumption.
- For emission, interlock, high-voltage, module wiring, or power-up/power-down behavior, consult the manual before implementing.

## PySide6 Guidance

- Keep device communication separate from widget code.
- Prefer controller/service layers for SDK calls instead of scattering SDK access directly across UI widgets.
- Keep all user-facing GUI text, labels, prompts, and status messages available in both Chinese and English.
- Build bilingual support into the GUI architecture instead of hardcoding mixed-language strings in business logic.
- Keep GUI state synchronized with live device state.
- For polling, connection retries, long-running operations, and refresh loops, use appropriate threading, timers, or async patterns so the GUI remains responsive.
- Error reporting should distinguish between connection failure, missing parameter, device rejection, and safety-related restrictions.
- If the app polls device state in the background, avoid repeated modal error storms after a cable pull or device loss. Detect poll-path failures, stop or reset the connection state, and notify the user once rather than on every timer tick.
- Add an explicit close confirmation for the main application window when the product expects desktop-style operator confirmation before exit.
- When refactoring a growing GUI, first split popup windows into `windows/`, then split large feature sections such as `CC`, `TC`, and `PC` into dedicated `QWidget` panels under `widgets/`.
- After widget split, move feature-specific rendering, state sync, and business-flow glue into a `controllers/` layer only when that logic is becoming cross-widget or sequence-heavy.
- Avoid introducing a controller layer as empty ceremony. A controller should own real flow logic such as multi-step writes, render/update orchestration, polling coordination, or cross-module state handling.
- For reusable GUI patterns that will appear across multiple modules, extract shared widgets early instead of copy-pasting. Typical candidates include toggle buttons, step-button rows, and numeric-input rows with explicit step-target buttons.
- Add concise Chinese comments in non-obvious code paths when they help future maintenance. Comments should explain why a structure exists or what coordination rule it enforces, not restate obvious assignments.

## Popup Window Guidance

- If a page such as `Laser`, `Scan&Lock`, `Relock`, or `Stabilization` is intended to open as a separate `QMainWindow`, preserve that navigation model.
- Do not assume that matching the main-window style only means copying inner panel colors. Match the outer shell too: margins, group containers, title hierarchy, spacing rhythm, and visible framing.
- Check whether styles are applied only to the main window instance. A popup `QMainWindow` will often not inherit `self.setStyleSheet(...)` from another top-level window. Prefer application-level styling or explicitly style the popup as well.
- When a popup is supposed to appear after clicking a navigation button, verify that it is actually shown, raised, activated, and not hidden behind the main window.

## Bilingual UI Guidance

- For any touched page, review the entire visible text set after edits. Do not stop after wiring new strings.
- Avoid mixed-language headings such as English section titles combined with Chinese field labels unless the user explicitly wants that style.
- Preserve necessary technical abbreviations like `CC`, `TC`, `ARC`, units, and verified product naming, but localize the surrounding descriptive text consistently.
- Prefer one dominant language per active UI language mode. In Chinese mode, default to Chinese-first phrasing; in English mode, use fully natural English.

## Styling Pitfalls

- Be careful with broad selectors such as `QWidget { background: ... }`. They can unintentionally give plain text labels an ugly dark backing in popup windows and nested panels.
- If static text should sit cleanly on top of a panel, explicitly check whether `QLabel` needs `background: transparent`.
- Keep special visual treatments only for widgets that genuinely need them, such as status badges, readback fields, or framed value displays.
- If a popup window creates its own `QComboBox` instances instead of reusing those owned by the main window, do not assume main-window width helpers will affect them. Popup-local combos often need their own width/popup-sizing helper in the popup class itself.
- When matching an official dark industrial GUI, do not stop at group titles and borders. Small status lamps, button clustering, readback-field framing, and spacing rhythm are part of the operator-facing visual language too.

## Numeric Step Controls

- For modules such as `CC`, `TC`, and `PC`, prefer one shared step-control row per module rather than a separate step row for every numeric field.
- Do not rely only on focus-following behavior if the target field would be unclear to the operator.
- A strong pattern is: keep one module-level step row, and add a small explicit target-selection button next to each editable numeric field, such as `Current Target`.
- The selected target button should have a visible pressed/checked state so the operator can immediately tell which field the module step buttons control.
- Keep the default step target stable for each module, but allow the user to rebind the module step row to another field in that module with one click.

## Scaling Structure

- If a popup window grows beyond a few hundred lines of layout code, treat that as a signal to split it into dedicated panel widgets.
- Prefer this progression:
  1. `app.py` keeps only global shell, navigation, connection widgets, and task orchestration
  2. `windows/` owns popup window shells and page composition
  3. `widgets/` owns reusable controls and feature panels such as `CcPanel`, `TcPanel`, and `PcPanel`
  4. `controllers/` owns feature flow, render coordination, and multi-step behavior when needed
- During refactors, preserve existing user behavior first, then improve internal structure. Do not mix large behavior changes with large file moves unless the user asked for both.

## Multi-Page Shared-Parameter Guidance

- If two pages talk to the same SDK parameter group, share the service-layer read/write methods and the verified SDK interface, but do not assume they should share the same page widget, exported widget attribute names, or page-specific controller.
- Separate "same device capability" from "same UI ownership". A parameter group such as `laser1.scan` may be valid in multiple product pages, but each page should still own its own widget tree, page composition, and rendering glue unless the user explicitly wants one shared UI implementation.
- When splitting one capability across `Laser`, `Scan&Lock`, `Relock`, or `Stabilization`, first decide whether the pages are alternate entry points to the same function or distinct operator workflows built on the same underlying SDK nodes. Reuse the SDK-backed service methods first; reuse the page widget/controller only when the operator workflow is truly the same.
- If a feature is expected to grow into multiple windows over time, prefer page-local widget folders such as `widgets/laser/` and `widgets/scan_lock/` early, even when the initial UI looks similar. This avoids coupling future development to one page's control names and layout assumptions.

## Preset-Value Guidance

- Some DLC pro / FALC SDK nodes expose integer preset values while the manual only documents the human meaning, such as "preset corner frequencies", without publishing the full mapping table.
- In that case, keep the raw device integer as the source of truth for reads/writes, and treat any human-readable `Hz / kHz / MHz` label as a display layer on top of that raw value.
- If the full mapping cannot be confirmed from SDK docs, examples, or the manual, do not pretend the mapping is verified. Label it as inference in code comments or explanations and keep a safe raw-value fallback in the UI.
- For preset-style controls, it is acceptable to ship an operator-friendly formatted display first and tighten the mapping later using real device readback values, as long as the write path still uses the verified raw integer.

## FALC Window Guidance

- Treat `FALC` as its own popup workflow rather than as a cosmetic extension of `Laser`. Its widget tree, render logic, and page-specific state handling should stay page-local even though the same service layer can back both pages.
- For `FALC Main` and `FALC Unlim`, prefer one snapshot subtree per branch in the service layer. This keeps `render_snapshot()` simpler and avoids scattering `board.main.*` and `board.unlim.*` access details across the UI layer.
- For `Unlim` specifically, keep the read-only gain display distinct from editable fields like `input_offset`, `output_range`, and `slew_rate`; the manual describes that gain as a resulting indication, not an operator-entered value.

## Preview-vs-Write Guidance

- Do not treat every editable-looking control as "requires device connection" by default. For selector-style controls such as combo boxes, option checkboxes, or mode pickers, first decide whether the operator benefits from previewing or staging a choice before connection.
- A good rule is: if a control mainly chooses among documented modes or channels and the disconnected action should not write hardware state, keep it enabled for local preview and guard the write path in the event handler with connection checks.
- Keep true hardware-write controls such as output enables, numeric setpoints, and safety-relevant toggles disabled when disconnected unless the product explicitly wants offline staging behavior.
- When this split exists, implement it centrally in the window state/update layer instead of scattering `setEnabled(...)` overrides across individual widgets.

## Window-Lifecycle Guidance

- If popup pages are implemented as auxiliary top-level windows that normally hide on close, add an explicit shutdown path for application exit. Otherwise closing the main window may leave auxiliary windows alive and keep the process running.
- Distinguish between operator close behavior (`hide`) and application shutdown behavior (`accept and close`). This is best handled in the shared popup base window rather than repeated in every feature window.

## Unit-Derivation Guidance

- For PID, Lock-In, and similar scan/lock controls, the displayed engineering unit may depend on the selected output channel. When the manual states that the unit depends on the channel, derive the displayed suffix from the current verified channel value during render instead of hardcoding one static unit per field.
- If the SDK exposes the numeric value but not a dedicated unit node, prefer a render-layer unit mapping backed by the manual. Clearly separate the write value from the unit decoration so later hardware-specific refinements do not require changing the service-layer API.

## Live-Interaction Guidance

- Do not add confirmation dialogs to every numeric write just because a field is editable. Reserve confirmations for safety-relevant actions, hard limits, large destructive jumps, or explicit operator-risk boundaries such as current clip limits.
- For ordinary setpoint edits such as temperature set, piezo set, slew-rate tuning, or scan frequency/amplitude tweaks, the operator should normally be able to use spinbox arrows directly without a modal prompt on every change.
- If the application polls live state in the background, do not blindly overwrite widgets that the operator is currently interacting with. During render, skip spinbox value pushes when the spinbox has focus, and skip combo-box index sync while the popup list is open or the combo has focus.
- Treat poll refresh as different from a write action. A background poll should not freeze the whole page or disable local choice widgets the same way an in-flight write does.
- If a popup page is scrollable, preserve its scroll position across render/update passes. A value write or poll refresh should never yank the operator to the top or bottom of the page while they are adjusting a control.
- When a write task and a poll task share the same executor, guard against dropped auto-apply writes. If the UI defers current writes with a timer, re-arm that timer when a poll is already in flight instead of silently discarding the pending write.

## Implementation Strategy

Do not think in terms of replacing a single page from the official GUI. Implement DLC pro functionality in Python incrementally by module:

1. Device connection and identification
2. Basic status display
3. Core parameter read/write
4. Emission control and safety-related state
5. Main control pages such as current, temperature, piezo, and scan
6. Plotting, logging, and alarms
7. Continue filling the remaining device-control capabilities until the main operations are available through Python and the custom GUI

If a desired device capability cannot be confirmed in the SDK, do not fabricate it. Mark it clearly as not yet backed by a verified SDK interface.

## Output Requirements

- In explanations or code comments, prefer labeling non-obvious behavior as based on `SDK` or `Manual`.
- When a decision relies on a specific rule, point to the relevant document path or section clue.
- In code review, prioritize mismatches against official sources over style-only feedback.
- For connection work, state whether the implementation depends on `pyserial` or `ifaddr`, and whether the behavior comes from the SDK or the project-layer design.
- When UI behavior was ambiguous at first, explicitly state which interaction model was finally implemented, such as popup `QMainWindow` versus in-page stacked view.

## Final Checklist

- Every API name is backed by SDK docs, SDK examples, or verified usage
- Every device-behavior claim is backed by the manual or clearly labeled as inference
- No units, limits, or defaults are introduced without a source
- Safety, interlock, emission, and wiring logic have been checked against the manual
- Any conflict between official sources and project code has been surfaced explicitly
- The connection module accounts for both `pyserial` and `ifaddr`
- User-facing GUI text has been planned or implemented for both Chinese and English
- Popup windows, if used, have the intended interaction model and a verified style match with the main window
- The touched page has been checked for mixed-language leftovers and unwanted label backgrounds
