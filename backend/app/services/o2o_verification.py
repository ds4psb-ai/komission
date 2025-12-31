import math

from app.utils.time import utcnow

class O2OVerificationService:
    def __init__(self):
        pass

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between two points in meters.
        """
        R = 6371000  # Radius of Earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def verify_visit(self, user_lat: float, user_lng: float, location_data: dict, max_distance_meters: float = 100.0) -> dict:
        """
        Verifies if the user is within the allowed distance of the target location.
        """
        target_lat = location_data.get('lat')
        target_lng = location_data.get('lng')

        if target_lat is None or target_lng is None:
             return {"verified": False, "reason": "Invalid target location data"}

        distance = self.calculate_distance(user_lat, user_lng, target_lat, target_lng)

        if distance <= max_distance_meters:
            return {
                "verified": True,
                "distance": distance,
                "timestamp": utcnow().isoformat(),
                "method": "gps_match"
            }
        else:
            return {
                "verified": False,
                "reason": f"Too far from location. Distance: {distance:.1f}m",
                "distance": distance
            }

o2o_service = O2OVerificationService()
