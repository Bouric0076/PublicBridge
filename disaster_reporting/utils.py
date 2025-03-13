import requests

def get_address_from_coordinates(lat, lon):
    """
    Uses OpenStreetMap's Nominatim API to convert coordinates into a readable address.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {'User-Agent': 'publicbridge-app'}  # Required by Nominatim
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("display_name", "Address not found")
    return "Error fetching address"
