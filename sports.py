def fmt_pace(speed_ms, sport_group):
    """Format m/s as a human-readable pace string for display."""
    if not speed_ms or speed_ms <= 0:
        return "—"
    if sport_group == "Run":
        m, s = divmod(int(1000 / speed_ms), 60)
        return f"{m}:{s:02d} /km"
    if sport_group == "Swim":
        m, s = divmod(int(100 / speed_ms), 60)
        return f"{m}:{s:02d} /100m"
    return f"{speed_ms * 3.6:.1f} km/h"


def pace_decimal(speed_ms, sport_group):
    """Convert m/s to a numeric pace value for Chart.js plotting.

    Run → decimal min/km, Swim → decimal min/100m, Ride → km/h.
    Returns None when speed is zero or missing.
    """
    if not speed_ms or speed_ms <= 0:
        return None
    if sport_group == "Run":
        return round(1000 / speed_ms / 60, 4)
    if sport_group == "Swim":
        return round(100 / speed_ms / 60, 4)
    return round(speed_ms * 3.6, 2)


SPORT_GROUP = {
    "Run": "Run", "VirtualRun": "Run", "TrailRun": "Run",
    "Ride": "Ride", "VirtualRide": "Ride", "EBikeRide": "Ride",
    "GravelRide": "Ride", "MountainBikeRide": "Ride", "Handcycle": "Ride",
    "Swim": "Swim", "OpenWaterSwim": "Swim",
}

SPORT_COLOURS = {"Run": "#dc3545", "Ride": "#0d6efd", "Swim": "#198754"}

# Keys of SPORT_GROUP, grouped by discipline — used for SQL IN clauses
SPORT_GROUP_TYPES = {
    "Run":  ["Run", "VirtualRun", "TrailRun"],
    "Ride": ["Ride", "VirtualRide", "EBikeRide", "GravelRide", "MountainBikeRide", "Handcycle"],
    "Swim": ["Swim", "OpenWaterSwim"],
}
