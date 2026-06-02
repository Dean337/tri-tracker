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
