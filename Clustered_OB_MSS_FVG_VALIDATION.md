# Clustered OB + MSS + FVG — Validation Notes

## Local validation

The companion test `tests/test_clustered_ob_mss_fvg.py` models the displacement-linked association rules and checks the Pine source for prohibited or missing constructs. Run it with:

```bash
python3 -m unittest -v tests/test_clustered_ob_mss_fvg.py
```

The synthetic cases cover:

- a complete bullish cluster;
- a complete bearish cluster;
- isolated OB, FVG, and MSS rejection;
- rejection of an unrelated older FVG inside the 12-bar cap;
- deterministic selection when two FVGs exist but only the newer one belongs to the MSS displacement;
- earliest-FVG selection when one displacement generates multiple valid gaps;
- selection of the actual displacement-anchor OB over an older OB;
- separation after an opposing interruption;
- separation of two delivery events inside the same 12-bar cap;
- rejection when the exact displacement has no qualifying FVG;
- rejection when the exact displacement has no opposing anchor OB;
- rejection beyond the 12-bar association bound;
- extension precedence and post-creation mitigation;
- normal, excluded-end, and overnight time-window behavior.
- default latest-cluster rendering;
- all-cluster rendering;
- replacement of prior latest drawings by a new cluster;
- identical logical detection results across display modes;
- clean All-to-Latest and Latest-to-All recalculation models.

Static checks cover `indicator()` rather than `strategy()`, Pine v6, all required user-facing inputs, the default and options for `Display Mode`, separation of logical storage from rendering policy, explicit displacement/OB/FVG/validation stages, confirmed pivots, realtime close confirmation, the 12-bar safety cap, and absence of `lookahead_on`, entries, exits, alerts, and external data requests.

### Latest automated result

Run on 2026-09-25 after the Display Mode revision:

```text
Ran 32 tests in 0.002s

OK
```

## TradingView validation matrix

Hosted compilation and chart rendering are still required. Paste `Clustered_OB_MSS_FVG.pine` into TradingView's Pine Editor and verify the following on an intraday futures chart with bar replay:

| Test | Procedure | Expected result |
|---|---|---|
| Bullish cluster | Replay a bearish candle followed by bullish displacement, a bullish FVG, and a close above a confirmed swing high. | One bullish OB box, one bullish FVG box, and one bullish MSS marker appear together. |
| Bearish cluster | Mirror the bullish sequence. | One complete bearish cluster appears. |
| Isolated component | Locate standalone gaps, opposing candles, and swing breaks. | None render unless all three are causally linked to one displacement. |
| Unrelated FVG | Find an old FVG followed by a non-impulse interruption and a new MSS displacement. | The old FVG is not borrowed even when it is inside 12 bars. |
| Multiple FVGs | Replay two gaps separated into different delivery events before an MSS. | The earliest FVG inside the exact MSS-ending displacement is selected; the older gap is ignored. |
| Unrelated OB | Replay an older opposing candle and then a newer opposing candle immediately before the MSS displacement. | Only the immediate displacement anchor is used. |
| Interrupted displacement | Replay a directional move, an interruption, then a fresh impulse into the MSS. | Pre-interruption components are not combined with the new displacement. |
| Latest default | Load a range with several confirmed clusters using the default settings. | Only the newest cluster's OB, FVG, MSS line, and label remain visible. |
| Latest replacement | In Bar Replay, confirm cluster A and then cluster B. | B replaces A's four drawings; A remains logical state only. |
| All clusters | Select `All Clusters` and recalculate the same range. | Every retained cluster is rendered, subject to the 100-cluster policy. |
| Mode equivalence | Compare the latest cluster in both display modes. | Direction, creation/MSS bar and level, OB, and FVG are identical. |
| All to Latest | Change the input from All to Latest. | Recalculation leaves only the latest cluster visible and no stale older drawings. |
| Latest to All | Change the input from Latest to All. | Recalculation rebuilds every retained eligible cluster drawing. |
| Swing length | Compare values 2, 3, and 5 on the same replay range. | Confirmed swing levels and resulting MSS clusters materially change. |
| Extend off | Disable `Extend`. | OB ends at source candle + 1; FVG ends at its third candle + 1. |
| Extend on | Enable `Extend`, leave mitigation extension off. | Both zones continue through the latest chart bar. |
| Until mitigated | Enable both extension options and replay a zone touch. | The touched zone stops on the touch bar; the untouched zone keeps extending. |
| Time qualification | Enable 09:30–10:30 America/New_York. | 09:45 and 10:15 MSS events may qualify; 10:30 and 10:35 events do not. |
| Window lifetime | Create a cluster at 10:25 and continue replay after 10:30. | The existing cluster remains and follows its extension settings. |
| Sequential integrity | Replay one bar at a time through a candidate event. | Nothing appears before the final required component is available. |
| Realtime parity | Compare replay results with the same fully loaded range. | Cluster creation bars and bounds match. |
| Visible range | Pan/zoom without changing symbol, timeframe, data, or settings. | Established results do not change. |
| DST | Check sessions around 2026-03-08 and 2026-11-01 on exchange data containing those dates. | Qualification remains aligned to 09:30–10:30 New York local time. |

## Validation boundary

Local tests validate the deterministic association model and source invariants; they do not replace TradingView compilation, bar-replay inspection, or exchange-data DST checks. Screenshots should be captured only after those hosted checks.
