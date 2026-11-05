# Codex Specification — Clustered OB + MSS + FVG Pine Indicator

## 1. Objective

Create a **standalone TradingView Pine Script indicator** that identifies and visually displays **only clusters where an Order Block (OB), Market Structure Shift (MSS), and Fair Value Gap (FVG) belong to the same price-delivery event**.

This indicator is **not part of the AI Futures Trading Lab**.

It must be completely independent:

- no imports from the Lab;
- no references to Lab code;
- no shared architecture;
- no dependency on external libraries;
- standalone Pine Script;
- suitable for direct use in TradingView.

The primary purpose is **structural visualization and historical validation**, not automated trading or Strategy Tester backtesting.

---

## 2. Core Concept

The indicator must **not independently draw every OB, every MSS, and every FVG**.

Instead, it should identify a **cluster**.

A cluster exists only when the three structural components are associated with the **same directional displacement event**.

Therefore:

> **If an OB exists without a corresponding MSS and FVG belonging to the same event, do not display it.**

Likewise:

> **If an MSS exists without the corresponding OB and FVG, do not display it.**

And:

> **If an FVG exists independently, do not display it.**

The visualizer should display the three components **only after the complete cluster has been established**.

---

## 3. Directional Clusters

Support both bullish and bearish clusters.

### Bullish cluster

```text
Bearish structure
       ↓
Liquidity / structure event
       ↓
Bullish displacement
       ↓
Bullish MSS
       ↓
Bullish FVG
       ↓
Bullish Order Block
       ↓
Bullish cluster
```

### Bearish cluster

```text
Bullish structure
       ↓
Liquidity / structure event
       ↓
Bearish displacement
       ↓
Bearish MSS
       ↓
Bearish FVG
       ↓
Bearish Order Block
       ↓
Bearish cluster
```

The exact ordering of the graphical objects should follow the actual price action and should **not be artificially reordered just to satisfy the visualization**.

---

## 4. MSS Detection

MSS detection must be based on configurable swing points.

Add an input:

```text
MSS Swing Length
```

Example:

```pine
input.int(3, "MSS Swing Length", minval=1)
```

Use confirmed swing highs and lows generated from that parameter.

The indicator must distinguish:

- bullish MSS;
- bearish MSS.

A bullish MSS occurs when price breaks a relevant confirmed swing high.

A bearish MSS occurs when price breaks a relevant confirmed swing low.

### Important

Do not use future information to confirm an MSS.

Swing points may only become available once Pine has confirmed them.

The script must therefore avoid introducing lookahead behavior.

Confirmation latency caused by the selected swing length is expected and must be respected during historical validation.

---

## 5. Order Block Detection

The indicator must identify the Order Block associated with the displacement that produces the MSS.

For a bullish cluster:

> Identify the relevant bearish candle / bearish price leg immediately preceding the bullish displacement responsible for the MSS.

For a bearish cluster:

> Identify the relevant bullish candle / bullish price leg immediately preceding the bearish displacement responsible for the MSS.

The OB should be represented by a rectangle using the high and low of the selected OB candle.

The implementation should encapsulate OB detection in its own function/module so that the detection logic is not mixed with rendering.

---

## 6. FVG Detection

Detect standard three-candle Fair Value Gaps.

### Bullish FVG

```text
candle 1 high < candle 3 low
```

The gap is:

```text
candle 1 high → candle 3 low
```

### Bearish FVG

```text
candle 1 low > candle 3 high
```

The gap is:

```text
candle 3 high → candle 1 low
```

The FVG must belong to the **same displacement leg that produced the MSS**.

Do not display unrelated FVGs.

---

## 7. Cluster Association Logic

This is the most important part of the specification.

The indicator must have an explicit concept of:

```text
Cluster
```

A cluster should contain at minimum:

```text
direction
MSS
Order Block
FVG
creation bar
OB boundaries
FVG boundaries
MSS level
mitigation state
```

A cluster becomes valid only when all three components have been associated:

```text
MSS + OB + FVG
```

### Association rules

The OB and FVG must be associated with the **same displacement event** that generated the MSS.

Do not simply search the entire chart for:

```text
nearest OB
+
nearest FVG
+
nearest MSS
```

That would generate false clusters.

Instead:

1. Detect the structural event.
2. Identify the displacement responsible for the break.
3. Identify the FVG created by that displacement.
4. Identify the OB preceding that displacement.
5. Validate that all three belong to the same directional move.
6. Create the cluster.
7. Render the cluster.

---

## 8. Temporal Association

The implementation must impose a finite association window so that an old OB or FVG cannot later become incorrectly associated with a new MSS.

Create an internal maximum structural association distance.

If a valid cluster cannot be established within that window:

```text
discard candidate
```

Do not render partial clusters.

The exact implementation value should be chosen conservatively and documented in the code.

Do **not** expose unnecessary parameters to the user unless they are required for reliable operation.

---

## 9. Cluster State Machine

Implement the detection logic as a state machine rather than independent plotting conditions.

Conceptually:

```text
NO_CLUSTER
    ↓
MSS_DETECTED
    ↓
DISPLACEMENT_IDENTIFIED
    ↓
FVG_IDENTIFIED
    ↓
OB_IDENTIFIED
    ↓
CLUSTER_CONFIRMED
    ↓
ACTIVE
    ↓
MITIGATED
```

A candidate should be discarded if the required components cannot be established.

This prevents the indicator from displaying incomplete structures.

---

## 10. Time Window Filter

Add an optional intraday time filter.

The user-facing parameters should be:

```text
Use Time Window
Start Time
End Time
Time Zone
```

For example:

```text
Use Time Window: ON
Start Time:      09:30
End Time:        10:30
Time Zone:       America/New_York
```

### Critical behavior

The time filter must be applied during **cluster qualification**, not merely during rendering.

The qualifying structural event/MSS must occur inside the configured window for the cluster to be created.

Therefore:

- cluster qualifying at 09:42 → valid;
- cluster qualifying at 10:17 → valid;
- cluster qualifying at 10:34 → invalid.

A cluster that qualifies at 10:25 may remain active after 10:30 and continue to obey the `Extend` and `Extend Until Mitigated` settings.

The script must **not**:

1. detect every historical cluster;
2. then simply hide clusters outside the time window.

Instead, the time filter must participate in the actual cluster qualification process.

### Timezone

The time filter must use the explicitly configured timezone.

It must correctly handle:

- historical bars;
- timezone conversion;
- US daylight-saving-time transitions.

---

## 11. Visualization

Once a cluster is confirmed, display:

### Order Block

Rectangle covering the high → low of the OB candle.

### FVG

Rectangle covering the FVG upper and lower boundaries.

### MSS

Clearly mark the MSS level/event.

Possible visualization:

```text
MSS
────────────────
```

or an appropriate label/line indicating:

```text
Bullish MSS
Bearish MSS
```

Keep the visual language clean and suitable for intraday futures analysis.

Do not add:

- entry signals;
- stop losses;
- targets;
- trade recommendations;
- unrelated indicators;
- automated trading logic.

---

## 12. User Inputs

Expose the following parameters.

### Colors

Provide independent colors for:

- Bullish Order Block
- Bearish Order Block
- Bullish FVG
- Bearish FVG
- Bullish MSS
- Bearish MSS

Use `input.color()`.

### MSS Swing Points

Provide:

```text
MSS Swing Length
```

Example:

```pine
input.int(
    3,
    "MSS Swing Length",
    minval=1
)
```

### Extend

Provide:

```text
Extend
```

Boolean:

```pine
input.bool(true, "Extend")
```

Behavior:

**Extend = OFF**

OB and FVG boxes terminate at their normal structural boundaries.

**Extend = ON**

Active OB/FVG boxes extend toward the right side of the chart.

### Extend Until Mitigated

Provide:

```text
Extend Until Mitigated
```

Boolean:

```pine
input.bool(false, "Extend Until Mitigated")
```

Behavior:

```text
cluster created
      ↓
zone extends right
      ↓
price mitigates zone
      ↓
extension stops
```

Interaction:

```text
Extend = false
    → no right extension

Extend = true
    → extend

Extend = true
AND
Extend Until Mitigated = true
    → extend until mitigation
```

`Extend Until Mitigated` must never cause extension when `Extend` is disabled.

---

## 13. Mitigation Definition

Use a deterministic definition.

For the initial implementation:

### Bullish OB

Consider the OB mitigated when price trades into the OB zone.

### Bearish OB

Same principle.

### FVG

Consider the FVG mitigated when price trades into the FVG zone.

The cluster should use the relevant zone state to stop extension.

Document the exact implementation in comments.

Do not introduce discretionary definitions such as "fully mitigated" unless explicitly required.

---

## 14. Historical Validation

This script is **not a trading strategy**.

It must use:

```pine
indicator(...)
```

and **must not use**:

```pine
strategy(...)
```

There is no requirement at this stage for:

- TradingView Strategy Tester;
- entries;
- exits;
- stop losses;
- profit targets;
- position sizing;
- P&L;
- trade statistics;
- automated execution.

The purpose is **historical structural validation**.

The indicator must load historical futures data and reconstruct clusters sequentially.

### Core requirement

> **A cluster must never be displayed using information that would not have been available at the point in historical time when the cluster became valid.**

Historical processing must therefore behave as if the chart were being processed one bar at a time.

---

## 15. Historical / Realtime Consistency

The same detection logic must be used for:

- Historical bars
- Realtime bars

Do not create one algorithm for historical processing and another for realtime processing.

The script must:

- process historical bars sequentially;
- process new realtime bars using the same logic;
- avoid retroactively combining structures;
- preserve confirmed cluster state.

Changing the visible chart range must not alter previously established cluster results.

---

## 16. Repainting Requirements

The indicator must be designed to minimize repainting.

Specifically:

- confirmed swing points only;
- no `lookahead_on`;
- no future-bar inspection;
- no retroactive cluster creation using information unavailable at the time;
- no retrospective association of old OBs/FVGs with later events;
- no artificial historical reconstruction that would not have been possible in realtime.

Because Pine swing functions inherently require confirmation bars, the resulting confirmation latency is expected.

Document this clearly.

---

## 17. Object Management

Pine has drawing-object limits.

The implementation must efficiently manage:

- `box` objects;
- `line` objects;
- `label` objects.

Do not create unlimited objects on every bar.

Use arrays/state where appropriate:

```text
array<box>
array<line>
array<label>
```

Maintain cluster objects as structured state where practical.

Implement cleanup when necessary to avoid exceeding TradingView limits.

Do not delete active clusters prematurely.

---

## 18. Architecture

Keep detection and rendering separate.

Recommended conceptual structure:

```text
Inputs
  │
  ▼
Swing Detection
  │
  ▼
MSS Detection
  │
  ▼
Displacement Detection
  │
  ├──────► FVG Detection
  │
  └──────► OB Detection
              │
              ▼
       Cluster Validation
              │
              ▼
        Time Validation
              │
              ▼
       Cluster State
              │
              ▼
        Mitigation
              │
              ▼
        Visualization
```

Suggested functions:

```text
detectSwingPoints()
detectMSS()
detectDisplacement()
detectFVG()
detectOrderBlock()
buildCluster()
validateCluster()
isWithinTimeWindow()
updateCluster()
checkMitigation()
renderCluster()
cleanupObjects()
```

Names may be adapted to idiomatic Pine.

---

## 19. Performance

Optimize for normal intraday futures charts.

The script should not:

- scan the entire historical dataset on every bar;
- repeatedly recreate all objects;
- maintain unnecessary historical state;
- use expensive loops where incremental state can be used.

Prefer incremental processing:

```text
new bar
   ↓
update current structural state
   ↓
check candidate cluster
   ↓
apply time-window qualification
   ↓
update active clusters
```

---

## 20. Pine Version

Use the current stable Pine Script version supported by TradingView at implementation time.

Do not use deprecated syntax.

The script must compile without errors and avoid warnings where reasonably possible.

---

## 21. Indicator Declaration

Use a normal overlay indicator.

Conceptually:

```pine
indicator(
    "Clustered OB + MSS + FVG",
    overlay=true,
    max_boxes_count=...,
    max_lines_count=...,
    max_labels_count=...
)
```

Choose appropriate object limits based on the implementation.

Do not expose unnecessary settings.

---

## 22. Acceptance Criteria

Codex must not consider the task complete merely because the script compiles.

The following must be verified.

### Test 1 — Bullish cluster

Given price action containing:

```text
bearish OB
      ↓
bullish displacement
      ↓
bullish MSS
      ↓
bullish FVG
```

the indicator displays:

```text
Bullish OB
Bullish FVG
Bullish MSS
```

as one cluster.

### Test 2 — Bearish cluster

Given:

```text
bullish OB
      ↓
bearish displacement
      ↓
bearish MSS
      ↓
bearish FVG
```

display the corresponding bearish cluster.

### Test 3 — Isolated OB

An OB without a corresponding MSS + FVG must **not** be displayed.

### Test 4 — Isolated FVG

An FVG unrelated to an MSS/OB displacement must **not** be displayed.

### Test 5 — Isolated MSS

An MSS without a valid associated OB and FVG must **not** create a cluster.

### Test 6 — Unrelated components

If:

```text
MSS A
OB B
FVG C
```

belong to different structural events, they must **not** be combined.

This is one of the most important tests.

### Test 7 — Extend OFF

Verify that zones do not extend beyond their normal boundaries.

### Test 8 — Extend ON

Verify that active zones extend rightward.

### Test 9 — Extend Until Mitigated

Verify:

```text
cluster created
→ zone extends
→ price enters mitigation zone
→ extension stops
```

### Test 10 — Swing Length

Changing `MSS Swing Length` must materially change which structural breaks qualify as MSS.

### Test 11 — Colors

Changing each color input must affect only its corresponding visual component.

### Test 12 — No lookahead

Verify that the implementation does not use:

```text
lookahead_on
```

or equivalent future-information logic.

### Test 13 — Time Window

With:

```text
09:30–10:30 America/New_York
```

verify that:

- a qualifying event at 09:45 creates a cluster;
- a qualifying event at 10:15 creates a cluster;
- a qualifying event at 10:35 does not create a cluster.

### Test 14 — Time Window Does Not Cut Existing Clusters

A cluster qualifying at 10:25 must remain active after 10:30 if extension/mitigation rules permit it.

The time window controls **cluster creation**, not the lifetime of an already-confirmed cluster.

### Test 15 — Historical Sequential Integrity

Verify that a cluster does not appear before the bar on which all information required to establish it became available.

### Test 16 — Historical / Realtime Consistency

The same structural detection logic must be used for historical and realtime bars.

### Test 17 — Visible Range Independence

Changing the chart's visible historical range must not change previously established cluster results.

### Test 18 — DST

Test the time filter across US daylight-saving transitions and verify that the configured New York session remains 09:30–10:30 local New York time.

---

## 23. Visual Validation

Codex should create a small deterministic validation dataset or use a controlled synthetic price sequence where practical.

The validation should make it possible to visually confirm:

```text
          MSS
           │
           ▼
     ┌───────────┐
     │    FVG    │
     └───────────┘
           │
     ┌───────────┐
     │    OB     │
     └───────────┘

       = CLUSTER
```

The critical validation is not whether each individual detector works.

It is whether the **association logic correctly prevents unrelated OBs/FVGs/MSSs from being displayed together**.

---

## 24. Code Quality

The resulting Pine script should be:

- readable;
- modular;
- heavily commented around the cluster-association logic;
- deterministic;
- free of unnecessary complexity;
- free of unrelated trading logic.

Comments should explain **why** a structural decision is made, not merely restate the code.

---

## 25. Deliverables

Codex should produce:

1. The standalone `.pine` indicator.
2. A concise README explaining:
   - what constitutes a cluster;
   - MSS detection;
   - OB detection;
   - FVG detection;
   - cluster association;
   - time-window behavior;
   - mitigation;
   - extension behavior;
   - historical validation methodology;
   - known limitations.
3. Validation/test notes.
4. Example screenshots if the repository workflow supports them.

Do **not** modify the AI Futures Trading Lab repository or its architecture.

---

# 26. Codex Execution Prompt

Use the following as the implementation prompt:

```text
Implement the standalone TradingView Pine Script indicator specified below.

IMPORTANT:

This is an independent project.

It is NOT part of the AI Futures Trading Lab.

Do not reference, import, modify, or depend on any AI Futures Trading Lab code, repository, architecture, documentation, or configuration.

OBJECTIVE

Create a Pine Script overlay indicator that displays ONLY clustered:

- Order Blocks
- Market Structure Shifts
- Fair Value Gaps

A component must NOT be displayed independently.

A valid cluster requires an OB, MSS, and FVG that all belong to the same directional displacement/price-delivery event.

The central requirement is correct ASSOCIATION, not merely detecting the three concepts independently.

The indicator is intended for:

1. visual structural analysis;
2. historical validation.

It is NOT a trading strategy.

Do not implement TradingView Strategy Tester functionality.

Do not use strategy().

Use indicator().

CORE IMPLEMENTATION

1. Detect confirmed swing highs/lows using a configurable MSS Swing Length.

2. Detect bullish and bearish MSS from confirmed structural swings.

3. Identify the displacement responsible for the MSS.

4. Identify the FVG created by that same displacement.

5. Identify the relevant preceding Order Block associated with that displacement.

6. Only when all three components are successfully associated should a Cluster object be created.

7. Do not match arbitrary nearest OB + FVG + MSS objects.

8. Use a finite structural association window so stale components cannot be associated with later MSS events.

9. Keep detection logic separate from rendering logic.

10. Maintain explicit cluster state.

Suggested state flow:

NO_CLUSTER
→ MSS_DETECTED
→ DISPLACEMENT_IDENTIFIED
→ FVG_IDENTIFIED
→ OB_IDENTIFIED
→ CLUSTER_CONFIRMED
→ ACTIVE
→ MITIGATED

Discard incomplete candidates.

USER INPUTS

Expose:

- Bullish OB color
- Bearish OB color
- Bullish FVG color
- Bearish FVG color
- Bullish MSS color
- Bearish MSS color
- MSS Swing Length
- Extend ON/OFF
- Extend Until Mitigated ON/OFF
- Use Time Window ON/OFF
- Start Time
- End Time
- Time Zone

TIME WINDOW

The time window is an intraday qualification filter.

Example:

Use Time Window = ON
Start = 09:30
End = 10:30
Time Zone = America/New_York

Only clusters whose qualifying MSS/displacement event occurs inside the configured window may be created.

Do NOT detect all historical clusters and merely hide those outside the window.

The time filter must participate in cluster qualification.

Examples:

09:42 qualifying event → valid cluster
10:17 qualifying event → valid cluster
10:34 qualifying event → no cluster

A cluster created at 10:25 may remain active after 10:30.

The time window controls cluster CREATION, not cluster lifetime.

The time filter must work correctly on historical data and across US daylight-saving transitions.

EXTENSION

Extend = false:
    Do not extend zones rightward.

Extend = true:
    Extend active zones rightward.

Extend = true AND Extend Until Mitigated = true:
    Extend until mitigation occurs, then stop.

Extend Until Mitigated must have no effect when Extend is false.

MITIGATION

Use deterministic mitigation.

For the initial implementation:

Bullish OB:
    mitigated when price trades into the OB zone.

Bearish OB:
    mitigated when price trades into the OB zone.

FVG:
    mitigated when price trades into the FVG zone.

Document the exact implementation.

HISTORICAL VALIDATION

This is NOT a trading strategy.

Do NOT implement:

- strategy()
- Strategy Tester
- entries
- exits
- stop losses
- profit targets
- position sizing
- P&L
- trade statistics
- automated execution

The indicator must perform historical structural validation.

Process historical bars sequentially.

A cluster must never be displayed using information that would not have been available at the time the cluster became valid.

Requirements:

1. No lookahead.
2. No lookahead_on.
3. No future-bar information.
4. Confirmed swing points only.
5. Respect MSS confirmation latency.
6. Cluster association must occur only when required information becomes available.
7. Apply the time-window filter during cluster qualification.
8. Use the same detection logic historically and in realtime.
9. Do not retroactively combine unrelated structures.
10. Changing the visible chart range must not alter previously established cluster results.

REPAINTING

Avoid repainting.

Do not use future information.

Do not retroactively associate old OB/FVG structures with later MSS events.

Confirmed swing latency is expected and must be documented.

ARCHITECTURE

Keep these concerns separate:

- swing detection
- MSS detection
- displacement detection
- FVG detection
- OB detection
- cluster association
- time-window qualification
- cluster state
- mitigation
- rendering
- object cleanup

Suggested functions:

detectSwingPoints()
detectMSS()
detectDisplacement()
detectFVG()
detectOrderBlock()
buildCluster()
validateCluster()
isWithinTimeWindow()
updateCluster()
checkMitigation()
renderCluster()
cleanupObjects()

Adapt names to idiomatic Pine if appropriate.

OBJECT MANAGEMENT

Use Pine drawing objects efficiently.

Use arrays/state where appropriate.

Avoid recreating every historical object on every bar.

Respect TradingView object limits.

Do not delete active clusters prematurely.

PERFORMANCE

Process bars incrementally.

Do not repeatedly scan the entire historical dataset on every bar.

Do not use expensive loops where incremental state is sufficient.

VALIDATION

Do not consider the task complete simply because the script compiles.

Verify:

1. Valid bullish OB + bullish MSS + bullish FVG produces one bullish cluster.

2. Valid bearish OB + bearish MSS + bearish FVG produces one bearish cluster.

3. Isolated OB is not displayed.

4. Isolated FVG is not displayed.

5. Isolated MSS is not displayed.

6. OB/FVG/MSS from different structural events are NOT combined.

7. Extend OFF behaves correctly.

8. Extend ON behaves correctly.

9. Extend Until Mitigated behaves correctly.

10. MSS Swing Length changes structural detection.

11. Color inputs affect only their corresponding objects.

12. No lookahead/future-information logic exists.

13. Time window correctly filters cluster creation.

14. A cluster created inside the time window remains active after the window closes according to extension/mitigation settings.

15. Historical sequential processing does not reveal a cluster before all required information became available.

16. Historical and realtime processing use the same detection logic.

17. Changing visible chart range does not change established cluster results.

18. DST behavior is correct for America/New_York.

The most important acceptance criterion is:

UNRELATED OB + MSS + FVG MUST NEVER BE DISPLAYED AS A CLUSTER.

DELIVERABLES

Produce:

- standalone .pine indicator
- README
- validation/test notes
- example screenshots if practical

Do not add:

- entries
- exits
- SL
- TP
- alerts
- automated trading
- AI logic
- Strategy Tester logic
- unrelated indicators

unless explicitly requested later.
```
