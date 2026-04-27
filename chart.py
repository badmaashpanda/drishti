import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime, timezone
import pytz
import json

swe.set_ephe_path(None)  # use built-in ephemeris

PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,   # North Node
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Vimshottari dasha sequence and years
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS =    [7,      20,      6,     10,     7,      18,     16,        19,        17]
TOTAL_YEARS = sum(DASHA_YEARS)  # 120

# Moon nakshatra lord determines dasha start
NAKSHATRA_LORD = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",  # 1-9
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",  # 10-18
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",  # 19-27
]


def degrees_to_sign(deg):
    deg = deg % 360
    sign_idx = int(deg / 30)
    deg_in_sign = deg % 30
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    return SIGNS[sign_idx], sign_idx, f"{d}° {m}'"


def degrees_to_nakshatra(deg):
    deg = deg % 360
    nak_idx = int(deg / (360 / 27))
    pada = int((deg % (360 / 27)) / (360 / 108)) + 1
    return NAKSHATRAS[nak_idx], nak_idx, pada


def get_coordinates(city):
    geolocator = Nominatim(user_agent="drishti_astro")
    location = geolocator.geocode(city, timeout=10)
    if not location:
        raise ValueError(f"Could not find coordinates for: {city}")
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    return location.latitude, location.longitude, tz_str


def local_to_ut(date_str, time_str, tz_str):
    """Convert local birth time to Universal Time."""
    local_tz = pytz.timezone(tz_str)
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(naive_dt)
    ut_dt = local_dt.astimezone(pytz.utc)
    return ut_dt


def calculate_chart(date_str, time_str, city):
    """
    Main function. Returns a dict with full Jyotish chart data.
    date_str: "YYYY-MM-DD"
    time_str: "HH:MM"
    city: "Mumbai, India"
    """
    lat, lon, tz_str = get_coordinates(city)
    ut_dt = local_to_ut(date_str, time_str, tz_str)

    jd = swe.julday(
        ut_dt.year, ut_dt.month, ut_dt.day,
        ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0
    )

    # Lahiri ayanamsa (standard for Jyotish)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Calculate lagna (ascendant)
    cusps, ascmc = swe.houses(jd, lat, lon, b'W')
    lagna_deg = (ascmc[0] - swe.get_ayanamsa_ut(jd)) % 360
    lagna_sign, lagna_sign_idx, lagna_dms = degrees_to_sign(lagna_deg)

    planets = {}
    moon_nak_idx = 0
    moon_deg_in_nak = 0

    for name, planet_id in PLANETS.items():
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        result, _ = swe.calc_ut(jd, planet_id, flags)
        deg = result[0] % 360

        sign, sign_idx, dms = degrees_to_sign(deg)
        nak, nak_idx, pada = degrees_to_nakshatra(deg)
        house = ((sign_idx - lagna_sign_idx) % 12) + 1

        planets[name] = {
            "degrees_full": round(deg, 4),
            "sign": sign,
            "position": dms,
            "nakshatra": nak,
            "pada": pada,
            "house": house,
        }

        if name == "Moon":
            moon_nak_idx = nak_idx
            moon_deg_in_nak = deg % (360 / 27)

    # Ketu = Rahu + 180
    rahu_deg = planets["Rahu"]["degrees_full"]
    ketu_deg = (rahu_deg + 180) % 360
    k_sign, k_sign_idx, k_dms = degrees_to_sign(ketu_deg)
    k_nak, k_nak_idx, k_pada = degrees_to_nakshatra(ketu_deg)
    planets["Ketu"] = {
        "degrees_full": round(ketu_deg, 4),
        "sign": k_sign,
        "position": k_dms,
        "nakshatra": k_nak,
        "pada": k_pada,
        "house": ((k_sign_idx - lagna_sign_idx) % 12) + 1,
    }

    # Vimshottari dasha
    dasha_info = calculate_dasha(moon_nak_idx, moon_deg_in_nak, ut_dt)

    return {
        "birth": {
            "date": date_str,
            "time": time_str,
            "city": city,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "timezone": tz_str,
        },
        "lagna": lagna_sign,
        "lagna_position": lagna_dms,
        "planets": planets,
        "dasha": dasha_info,
    }


def calculate_dasha(moon_nak_idx, moon_deg_in_nak, birth_dt):
    """Calculate current and upcoming Vimshottari dasha periods."""
    lord = NAKSHATRA_LORD[moon_nak_idx]
    lord_idx = DASHA_SEQUENCE.index(lord)

    nak_span = 360 / 27  # degrees per nakshatra
    fraction_elapsed = moon_deg_in_nak / nak_span
    first_dasha_years = DASHA_YEARS[lord_idx] * (1 - fraction_elapsed)

    from datetime import timedelta

    def add_years(dt, years):
        days = years * 365.25
        return dt + timedelta(days=days)

    now = datetime.now(tz=pytz.utc)
    cursor = birth_dt.replace(tzinfo=pytz.utc) if birth_dt.tzinfo is None else birth_dt

    periods = []
    for i in range(9):
        idx = (lord_idx + i) % 9
        planet = DASHA_SEQUENCE[idx]
        years = DASHA_YEARS[idx] if i > 0 else first_dasha_years
        end = add_years(cursor, years)
        periods.append({
            "planet": planet,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        })
        cursor = end

    # Find current dasha
    current = None
    upcoming = []
    for p in periods:
        start_dt = datetime.strptime(p["start"], "%Y-%m-%d").replace(tzinfo=pytz.utc)
        end_dt = datetime.strptime(p["end"], "%Y-%m-%d").replace(tzinfo=pytz.utc)
        if start_dt <= now <= end_dt:
            current = p
        elif start_dt > now:
            upcoming.append(p)

    return {
        "current": current,
        "upcoming": upcoming[:3],
        "all_periods": periods,
    }


def chart_to_summary(chart):
    """Human-readable one-paragraph summary for the system prompt."""
    p = chart["planets"]
    d = chart["dasha"]
    current = d["current"]

    lines = [
        f"Lagna (Ascendant): {chart['lagna']} {chart['lagna_position']}",
    ]
    for name, data in p.items():
        lines.append(
            f"{name}: {data['sign']} {data['position']} (House {data['house']}, Nakshatra: {data['nakshatra']} Pada {data['pada']})"
        )

    if current:
        lines.append(f"Current Mahadasha: {current['planet']} (until {current['end']})")

    if d["upcoming"]:
        upcoming_str = ", ".join(f"{x['planet']} ({x['start']} to {x['end']})" for x in d["upcoming"])
        lines.append(f"Upcoming Dashas: {upcoming_str}")

    return "\n".join(lines)
