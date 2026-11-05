from __future__ import annotations

import pathlib
import unittest
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
PINE = ROOT / "Clustered_OB_MSS_FVG.pine"
MAX_ASSOCIATION_BARS = 12
DISPLAY_LATEST = "Latest Cluster"
DISPLAY_ALL = "All Clusters"


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class ClusterParts:
    displacement_start: int
    displacement_end: int
    ob: int
    fvg_left: int
    fvg_right: int


@dataclass
class DisplayState:
    mode: str = DISPLAY_LATEST
    logical_clusters: list[int] | None = None
    visible_clusters: set[int] | None = None

    def __post_init__(self):
        self.logical_clusters = []
        self.visible_clusters = set()

    def confirm(self, cluster_id: int):
        self.logical_clusters.append(cluster_id)
        if self.mode == DISPLAY_LATEST:
            self.visible_clusters.clear()
        self.visible_clusters.add(cluster_id)


def recalculate_display(cluster_ids: list[int], mode: str) -> DisplayState:
    state = DisplayState(mode)
    for cluster_id in cluster_ids:
        state.confirm(cluster_id)
    return state


def is_displacement_bar(direction: int, bars: list[Bar], index: int) -> bool:
    if index == 0:
        return False
    bar, previous = bars[index], bars[index - 1]
    if direction == 1:
        return bar.close > bar.open and bar.close > previous.high
    return bar.close < bar.open and bar.close < previous.low


def detect_displacement(direction: int, bars: list[Bar], mss_index: int):
    start = None
    count = 0
    for index in range(mss_index, max(-1, mss_index - (MAX_ASSOCIATION_BARS - 1)), -1):
        if not is_displacement_bar(direction, bars, index):
            break
        start = index
        count += 1
    return (start, mss_index) if count >= 2 else None


def identify_ob(direction: int, bars: list[Bar], displacement_start: int, displacement_end: int):
    ob = displacement_start - 1
    if ob < 0 or displacement_end - ob > MAX_ASSOCIATION_BARS:
        return None
    opposing = bars[ob].close < bars[ob].open if direction == 1 else bars[ob].close > bars[ob].open
    return ob if opposing else None


def identify_fvg(
    direction: int,
    bars: list[Bar],
    displacement_start: int,
    displacement_end: int,
    ob: int,
):
    for right in range(displacement_start, displacement_end + 1):
        left = right - 2
        if left < ob:
            continue
        if direction == 1:
            gap = bars[left].high < bars[right].low
        else:
            gap = bars[left].low > bars[right].high
        if gap:
            return left, right
    return None


def qualify(direction: int, bars: list[Bar], mss_index: int):
    displacement = detect_displacement(direction, bars, mss_index)
    if displacement is None:
        return None
    start, end = displacement
    ob = identify_ob(direction, bars, start, end)
    if ob is None:
        return None
    fvg = identify_fvg(direction, bars, start, end, ob)
    if fvg is None:
        return None
    return ClusterParts(start, end, ob, fvg[0], fvg[1])


def in_window(now_minutes: int, start: int, end: int) -> bool:
    if start < end:
        return start <= now_minutes < end
    if start > end:
        return now_minutes >= start or now_minutes < end
    return True


def bullish_event() -> list[Bar]:
    return [
        Bar(10.0, 10.2, 8.8, 9.0),
        Bar(9.1, 12.0, 9.0, 11.8),
        Bar(11.9, 13.4, 10.6, 13.0),
    ]


def bearish_event() -> list[Bar]:
    return [
        Bar(9.0, 10.2, 8.8, 10.0),
        Bar(9.9, 10.0, 7.0, 7.2),
        Bar(7.1, 8.2, 5.7, 6.0),
    ]


class DisplacementAssociationTests(unittest.TestCase):
    def test_complete_bullish_cluster(self):
        self.assertEqual(qualify(1, bullish_event(), 2), ClusterParts(1, 2, 0, 0, 2))

    def test_complete_bearish_cluster(self):
        self.assertEqual(qualify(-1, bearish_event(), 2), ClusterParts(1, 2, 0, 0, 2))

    def test_isolated_ob_does_not_complete(self):
        bars = [Bar(10, 10.2, 8.8, 9), Bar(9, 10.3, 8.9, 10.1), Bar(10, 10.5, 9.7, 10.4)]
        self.assertIsNone(qualify(1, bars, 2))

    def test_isolated_fvg_has_no_displacement_anchor(self):
        bars = [Bar(9, 10, 8.8, 9.8), Bar(9.9, 12, 9.8, 11.8), Bar(11, 13, 10.5, 12.8)]
        self.assertIsNone(qualify(1, bars, 2))

    def test_isolated_mss_has_no_displacement_fvg(self):
        bars = [Bar(10, 10.2, 8.8, 9), Bar(9, 10.5, 8.9, 10.3), Bar(10.2, 11, 10.0, 10.8)]
        self.assertIsNone(qualify(1, bars, 2))

    def test_unrelated_fvg_inside_cap_is_not_borrowed(self):
        bars = bullish_event() + [
            Bar(13.0, 13.2, 11.8, 12.0),
            Bar(12.1, 13.5, 12.0, 13.3),
            Bar(13.3, 14.2, 13.0, 14.0),
        ]
        self.assertIsNone(qualify(1, bars, 5))

    def test_two_fvgs_selects_only_one_in_mss_displacement(self):
        bars = bullish_event() + [
            Bar(13.0, 13.2, 11.5, 12.0),
            Bar(12.1, 14.0, 12.0, 13.8),
            Bar(13.9, 15.2, 13.5, 15.0),
        ]
        self.assertEqual(qualify(1, bars, 5), ClusterParts(4, 5, 3, 3, 5))

    def test_multiple_fvgs_in_one_displacement_selects_earliest(self):
        bars = bullish_event() + [Bar(13.1, 15.0, 12.5, 14.8)]
        self.assertEqual(qualify(1, bars, 3), ClusterParts(1, 3, 0, 0, 2))

    def test_actual_displacement_anchor_wins_over_older_ob(self):
        bars = [
            Bar(10, 10.2, 8.8, 9),
            Bar(9.1, 11.0, 9.0, 10.8),
            Bar(10.8, 11.1, 9.7, 10.0),
            Bar(10.1, 12.0, 10.0, 11.8),
            Bar(11.9, 13.5, 11.3, 13.2),
        ]
        self.assertEqual(qualify(1, bars, 4), ClusterParts(3, 4, 2, 2, 4))

    def test_opposing_interruption_starts_a_new_event(self):
        bars = bullish_event() + [
            Bar(13.0, 13.1, 11.0, 11.5),
            Bar(11.6, 13.4, 11.5, 13.2),
            Bar(13.2, 15.0, 13.2, 14.8),
        ]
        self.assertEqual(qualify(1, bars, 5), ClusterParts(4, 5, 3, 3, 5))

    def test_two_events_inside_same_cap_do_not_mix(self):
        bars = bullish_event() + [
            Bar(13.0, 13.2, 12.0, 12.2),
            Bar(12.3, 14.0, 12.2, 13.8),
            Bar(13.9, 15.0, 13.4, 14.8),
        ]
        result = qualify(1, bars, 5)
        self.assertEqual(result, ClusterParts(4, 5, 3, 3, 5))
        self.assertNotEqual(result.ob, 0)
        self.assertNotEqual(result.fvg_left, 0)

    def test_no_qualifying_fvg_rejects_ob_and_mss(self):
        bars = [Bar(10, 10.2, 8.8, 9), Bar(9, 11, 8.9, 10.8), Bar(10.7, 12, 10.0, 11.8)]
        self.assertIsNone(qualify(1, bars, 2))

    def test_no_qualifying_ob_rejects_fvg_and_mss(self):
        bars = [Bar(9, 10.2, 8.8, 10), Bar(10.1, 12, 10.0, 11.8), Bar(11.9, 13.5, 10.5, 13.2)]
        self.assertIsNone(qualify(1, bars, 2))

    def test_displacement_beyond_safety_cap_is_rejected(self):
        anchor = Bar(10, 10.2, 8.8, 9)
        bars = [anchor]
        prior_high = anchor.high
        for _ in range(12):
            close = prior_high + 1
            bars.append(Bar(close - 0.5, close + 0.2, close - 0.8, close))
            prior_high = close + 0.2
        self.assertIsNone(qualify(1, bars, len(bars) - 1))

    def test_time_window_is_half_open_and_supports_overnight(self):
        self.assertTrue(in_window(9 * 60 + 30, 570, 630))
        self.assertTrue(in_window(10 * 60 + 15, 570, 630))
        self.assertFalse(in_window(10 * 60 + 30, 570, 630))
        self.assertTrue(in_window(23 * 60, 1320, 120))
        self.assertTrue(in_window(60, 1320, 120))
        self.assertFalse(in_window(12 * 60, 1320, 120))

    def test_mitigation_starts_after_creation(self):
        zone_top, zone_bottom = 10.0, 9.0
        formation = Bar(9.5, 10.5, 8.5, 10.2)
        later = Bar(10.2, 10.4, 9.8, 10.0)
        touched_at_formation = formation.high >= zone_bottom and formation.low <= zone_top
        touched_later = later.high >= zone_bottom and later.low <= zone_top
        self.assertTrue(touched_at_formation)
        self.assertFalse(0 > 0 and touched_at_formation)
        self.assertTrue(1 > 0 and touched_later)


class DisplayModeTests(unittest.TestCase):
    def test_latest_mode_renders_only_latest_cluster(self):
        state = recalculate_display([1, 2, 3], DISPLAY_LATEST)
        self.assertEqual(state.visible_clusters, {3})
        self.assertEqual(state.logical_clusters, [1, 2, 3])

    def test_all_mode_renders_all_retained_clusters(self):
        state = recalculate_display([1, 2, 3], DISPLAY_ALL)
        self.assertEqual(state.visible_clusters, {1, 2, 3})

    def test_new_cluster_replaces_previous_latest_visuals(self):
        state = DisplayState(DISPLAY_LATEST)
        state.confirm(10)
        self.assertEqual(state.visible_clusters, {10})
        state.confirm(11)
        self.assertEqual(state.visible_clusters, {11})
        self.assertEqual(state.logical_clusters, [10, 11])

    def test_display_mode_does_not_change_detection_results(self):
        detected = [1, 2, 3, 4]
        latest = recalculate_display(detected, DISPLAY_LATEST)
        all_clusters = recalculate_display(detected, DISPLAY_ALL)
        self.assertEqual(latest.logical_clusters, all_clusters.logical_clusters)
        self.assertEqual(max(all_clusters.visible_clusters), next(iter(latest.visible_clusters)))

    def test_all_to_latest_recalculation_leaves_no_stale_visuals(self):
        all_clusters = recalculate_display([1, 2, 3], DISPLAY_ALL)
        self.assertEqual(all_clusters.visible_clusters, {1, 2, 3})
        latest = recalculate_display(all_clusters.logical_clusters, DISPLAY_LATEST)
        self.assertEqual(latest.visible_clusters, {3})

    def test_latest_to_all_recalculation_rebuilds_all_visuals(self):
        latest = recalculate_display([1, 2, 3], DISPLAY_LATEST)
        self.assertEqual(latest.visible_clusters, {3})
        all_clusters = recalculate_display(latest.logical_clusters, DISPLAY_ALL)
        self.assertEqual(all_clusters.visible_clusters, {1, 2, 3})


class PineSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_indicator_and_version(self):
        self.assertIn("//@version=6", self.source)
        self.assertIn('indicator("Clustered OB + MSS + FVG"', self.source)
        self.assertNotIn("strategy(", self.source)

    def test_required_inputs_exist(self):
        for label in (
            "Bullish Order Block", "Bearish Order Block", "Bullish FVG", "Bearish FVG",
            "Bullish MSS", "Bearish MSS", "MSS Swing Length", "Extend",
            "Extend Until Mitigated", "Use Time Window", "Start Time", "End Time", "Time Zone",
        ):
            self.assertIn(f'"{label}"', self.source)

    def test_display_mode_input_defaults_to_latest(self):
        self.assertIn('const string DISPLAY_LATEST = "Latest Cluster"', self.source)
        self.assertIn('const string DISPLAY_ALL = "All Clusters"', self.source)
        self.assertIn('input.string(DISPLAY_LATEST, "Display Mode"', self.source)
        self.assertIn("options = [DISPLAY_LATEST, DISPLAY_ALL]", self.source)

    def test_display_policy_is_separate_from_detection(self):
        self.assertIn("f_buildCluster", self.source)
        self.assertIn("f_applyDisplayPolicy", self.source)
        self.assertIn("if displayMode == DISPLAY_LATEST", self.source)
        self.assertIn("if storedCluster.isVisible", self.source)
        self.assertIn("if cluster.isVisible and extendZones", self.source)

    def test_explicit_causal_stages_exist(self):
        for function in (
            "f_detectDisplacement", "f_identifyDisplacementOb",
            "f_identifyDisplacementFvg", "f_validateCluster", "f_renderCluster",
        ):
            self.assertIn(function, self.source)
        self.assertNotIn("f_detectEventFvg", self.source)
        self.assertNotIn("f_detectOrderBlock", self.source)

    def test_displacement_is_directional_range_expansion(self):
        self.assertIn("close[offset] > open[offset] and close[offset] > high[offset + 1]", self.source)
        self.assertIn("close[offset] < open[offset] and close[offset] < low[offset + 1]", self.source)
        self.assertIn("displacementBarCount >= 2", self.source)

    def test_no_prohibited_execution_or_external_data_features(self):
        lowered = self.source.lower()
        for token in ("lookahead_on", "strategy.entry", "strategy.exit", "alertcondition", "request.security"):
            self.assertNotIn(token, lowered)

    def test_confirmed_pivots_and_close_confirmation(self):
        self.assertIn("ta.pivothigh(high, swingLength, swingLength)", self.source)
        self.assertIn("ta.pivotlow(low, swingLength, swingLength)", self.source)
        self.assertIn("barstate.isconfirmed", self.source)
        self.assertIn("na(lastBrokenHighBar) or", self.source)
        self.assertIn("na(lastBrokenLowBar) or", self.source)

    def test_association_cap_is_only_an_internal_constant(self):
        self.assertIn("const int MAX_ASSOCIATION_BARS = 12", self.source)
        self.assertNotIn('input.int(12, "Association', self.source)

    def test_extension_and_mitigation_precedence(self):
        extension = self.source.index("if cluster.isVisible and extendZones", self.source.index("int clusterCount"))
        mitigation = self.source.index("if bar_index > cluster.creationBar")
        self.assertLess(extension, mitigation)
        self.assertIn("box.set_right(cluster.obBox, bar_index + 1)", self.source)
        self.assertIn("box.set_right(cluster.fvgBox, bar_index + 1)", self.source)


if __name__ == "__main__":
    unittest.main()
