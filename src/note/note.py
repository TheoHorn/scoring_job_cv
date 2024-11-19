from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from datetime import datetime


# List of resume
vec1 = [5,"04/2024","New-York, NY, USA"]
vec2 = [10,"05/2024","Boston, MA, USA"]
vec3 = [15,"06/2024","San Francisco, CA, USA"]
resumes = [vec1,vec2,vec3]

# The Offer
offer = [10,"05/2024","Boston, MA, USA"]

# Function to get coordinates from city name
def get_full_coordinates(geolocator,city, region, country):
    location = geolocator.geocode(f"{city}, {region}, {country}")
    if location:
        return (location.latitude, location.longitude)
    else:
        location = geolocator.geocode(f"{region}, {country}")
        if location:
            return (location.latitude, location.longitude)
        else:
            location = geolocator.geocode(f"{country}")
            if location:
                return (location.latitude, location.longitude)
            else:
                return None

### Calculate the distance between dates
def calculate_month_difference(date1, date2):
    date1 = datetime.strptime(date1, "%m/%Y")
    date2 = datetime.strptime(date2, "%m/%Y")
    return abs((date2.year - date1.year) * 12 + date2.month - date1.month)

### Calculate the difference between two years of experience
def calculate_experience_difference(cv_experience, job_experience):
    return job_experience - cv_experience



def order_resume(resumes,offer):
    geolocator = Nominatim(user_agent="city_distance_calculator")
    offer_location = offer[2].split(", ")
    offer_location = get_full_coordinates(geolocator, offer_location[0], offer_location[1], offer_location[2])
    for resume in resumes:
        resume_location = resume[2].split(", ")
        resume_location = get_full_coordinates(geolocator, resume_location[0], resume_location[1], resume_location[2])
        distance_km = geodesic(offer_location, resume_location).kilometers
        month_difference = calculate_month_difference(resume[1], offer[1])
        experience_difference = calculate_experience_difference(resume[0], offer[0])
        print(f"Resume: {resume}")
        print(f"Distance: {distance_km} km")
        print(f"Month difference: {month_difference}")
        print(f"Experience difference: {experience_difference}")
        score = distance_km/100 + month_difference + experience_difference
        print(f"Score: {score}")
        print("\n")

order_resume(resumes,offer)