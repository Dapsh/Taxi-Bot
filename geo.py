from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import random  # For demo purposes

class GeoService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="fifty_drive_bot")
        
    async def get_coordinates(self, address):
        """
        Get coordinates for an address
        
        Note: In a real implementation, this would use a proper geocoding service.
        For demo purposes, we're using a simple geocoder or returning random coordinates.
        """
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
        except Exception:
            pass
            
        # Fallback to random coordinates (for demo purposes only)
        # In a real app, you would handle this differently
        return (
            55.755826 + random.uniform(-0.1, 0.1),  # Moscow center + random offset
            37.617300 + random.uniform(-0.1, 0.1)
        )
        
    async def calculate_distance(self, from_address, to_address):
        """Calculate distance between two addresses in kilometers"""
        from_coords = await self.get_coordinates(from_address)
        to_coords = await self.get_coordinates(to_address)
        
        distance = geodesic(from_coords, to_coords).kilometers
        return round(distance, 2)
        
    async def estimate_travel_time(self, distance, traffic_factor=1.2):
        """
        Estimate travel time in minutes based on distance
        
        Args:
            distance: Distance in kilometers
            traffic_factor: Traffic congestion factor (1.0 = no traffic)
            
        Returns:
            Estimated travel time in minutes
        """
        # Assume average speed of 40 km/h in city
        avg_speed = 40
        
        # Calculate hours, then convert to minutes and apply traffic factor
        hours = distance / avg_speed
        minutes = hours * 60 * traffic_factor
        
        return round(minutes)