from geolite2 import geolite2

def get_country_from_ip(user_ip):
    if user_ip is None:
        return "NO"
    reader = geolite2.reader()
    tmpcountry = reader.get(user_ip)
    country = "NO"
    if tmpcountry is not None:
        country = tmpcountry['country']['iso_code']

    return country