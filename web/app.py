"""Kia Connect PWA — FastAPI backend with server-side caching + SQLite trip storage."""

import os
import sys
import time
import json
import sqlite3
import datetime as dt
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from kia_mcp.client import KiaClient

app = FastAPI(title="Kia Connect", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

_client: KiaClient | None = None
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 120  # 2 minutes for read endpoints
TRIP_CACHE_TTL = 300  # 5 minutes for trip data


def get_client() -> KiaClient:
    global _client
    if _client is None:
        _client = KiaClient(
            username=os.environ.get("KIA_USERNAME", ""),
            password=os.environ.get("KIA_PASSWORD", ""),
            pin=os.environ.get("KIA_PIN", ""),
            region=int(os.environ.get("KIA_REGION", "6")),
            brand=int(os.environ.get("KIA_BRAND", "1")),
            tank_liters=float(os.environ.get("KIA_TANK_LITERS", "45")),
            fuel_price=float(os.environ.get("KIA_FUEL_PRICE", "105")),
        )
    return _client


def cached(ttl: int = CACHE_TTL):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            now = time.time()
            if cache_key in _cache:
                cached_time, cached_data = _cache[cache_key]
                if now - cached_time < ttl:
                    return JSONResponse(cached_data)
            try:
                data = func(*args, **kwargs)
                _cache[cache_key] = (now, data)
                return JSONResponse(data)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        return wrapper
    return decorator


def invalidate_cache():
    _cache.clear()


# --- SQLite persistent trip storage ---

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trips.db")

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS trip_cache (
        date TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (date, endpoint)
    )""")
    return conn

def db_get(date: str, endpoint: str):
    conn = _db()
    row = conn.execute("SELECT data FROM trip_cache WHERE date=? AND endpoint=?", (date, endpoint)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def db_put(date: str, endpoint: str, data: dict):
    conn = _db()
    conn.execute("INSERT OR REPLACE INTO trip_cache (date, endpoint, data) VALUES (?, ?, ?)",
                 (date, endpoint, json.dumps(data)))
    conn.commit()
    conn.close()

def is_past_date(date_str: str) -> bool:
    today = dt.datetime.now().strftime("%Y%m%d")
    return date_str < today


# --- Pages ---

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active_page": "home"})

@app.get("/trips")
async def trips_page(request: Request):
    return templates.TemplateResponse(request, "trips.html", {"active_page": "trips"})

@app.get("/controls")
async def controls_page(request: Request):
    return templates.TemplateResponse(request, "controls.html", {"active_page": "controls"})

@app.get("/car")
async def car_page(request: Request):
    return templates.TemplateResponse(request, "car.html", {"active_page": "car"})


# --- Batch endpoint: single call for dashboard (SQLite-backed) ---

@app.get("/api/dashboard")
async def api_dashboard():
    now = time.time()
    cache_key = "api_dashboard::"
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if now - cached_time < CACHE_TTL:
            return JSONResponse(cached_data)
    stored = db_get("_dashboard", "dashboard")
    if stored and now - stored.get("_ts", 0) < CACHE_TTL:
        _cache[cache_key] = (now, stored)
        return JSONResponse(stored)
    try:
        data = _fetch_dashboard()
        data["_ts"] = now
        _cache[cache_key] = (now, data)
        db_put("_dashboard", "dashboard", data)
        return JSONResponse(data)
    except Exception as e:
        if stored:
            return JSONResponse(stored)
        return JSONResponse({"error": str(e)}, status_code=500)

def _fetch_dashboard():
    c = get_client()
    status = c.get_full_status()
    location = c.get_location()
    fuel = c.get_fuel()
    locked = c.is_car_locked()
    battery = c.get_battery()
    tires = c.get_tires()
    climate = c.get_climate_status()
    trips = None
    try:
        trips = c.get_trip_today()
    except Exception:
        pass
    service = None
    try:
        service = c.get_next_service()
    except Exception:
        pass
    return {
        "status": status,
        "location": location,
        "fuel": fuel,
        "locked": locked,
        "battery": battery,
        "tires": tires,
        "climate": climate,
        "trips": trips,
        "service": service,
    }


# --- Read API endpoints (all cached) ---

@app.get("/api/status")
@cached(ttl=CACHE_TTL)
def api_status():
    return get_client().get_full_status()

@app.get("/api/location")
@cached(ttl=CACHE_TTL)
def api_location():
    return get_client().get_location()

@app.get("/api/fuel")
@cached(ttl=CACHE_TTL)
def api_fuel():
    return get_client().get_fuel()

@app.get("/api/locked")
@cached(ttl=CACHE_TTL)
def api_locked():
    return get_client().is_car_locked()

@app.get("/api/battery")
@cached(ttl=CACHE_TTL)
def api_battery():
    return get_client().get_battery()

@app.get("/api/tires")
@cached(ttl=CACHE_TTL)
def api_tires():
    return get_client().get_tires()

@app.get("/api/climate")
@cached(ttl=CACHE_TTL)
def api_climate():
    return get_client().get_climate_status()

@app.get("/api/warnings")
@cached(ttl=CACHE_TTL)
def api_warnings():
    return get_client().get_warnings()

@app.get("/api/odometer")
@cached(ttl=CACHE_TTL)
def api_odometer():
    return get_client().get_odometer()

@app.get("/api/windows")
@cached(ttl=CACHE_TTL)
def api_windows():
    return get_client().get_windows()

@app.get("/api/lights")
@cached(ttl=CACHE_TTL)
def api_lights():
    return get_client().get_lights()

@app.get("/api/next-service")
@cached(ttl=TRIP_CACHE_TTL)
def api_next_service():
    return get_client().get_next_service()

@app.get("/api/maintenance")
@cached(ttl=TRIP_CACHE_TTL)
def api_maintenance():
    return get_client().get_maintenance_schedule()

@app.get("/api/profile")
@cached(ttl=TRIP_CACHE_TTL)
def api_profile():
    return get_client().get_vehicle_profile()

@app.get("/api/info")
@cached(ttl=TRIP_CACHE_TTL)
def api_info():
    return get_client().get_vehicle_info()

@app.get("/api/health")
@cached(ttl=CACHE_TTL)
def api_health():
    return get_client().get_car_health()

@app.get("/api/alerts")
@cached(ttl=TRIP_CACHE_TTL)
def api_alerts():
    return get_client().get_alert_settings()

@app.get("/api/departure-patterns")
@cached(ttl=TRIP_CACHE_TTL)
def api_departure_patterns():
    return get_client().get_departure_patterns()

@app.get("/api/frequent-places")
@cached(ttl=TRIP_CACHE_TTL)
def api_frequent_places():
    return get_client().get_frequent_locations()

@app.get("/api/rate-limit")
async def api_rate_limit():
    try:
        return JSONResponse(get_client().get_rate_limit())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/driving-summary")
@cached(ttl=TRIP_CACHE_TTL)
def api_driving_summary():
    return get_client().get_driving_summary()


# --- Trip endpoints (SQLite for past dates, API+cache for today) ---

def _trip_endpoint(date: str, endpoint: str, fetcher):
    if is_past_date(date):
        stored = db_get(date, endpoint)
        if stored is not None:
            return JSONResponse(stored)
    cache_key = f"{endpoint}:{date}"
    now = time.time()
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if now - cached_time < TRIP_CACHE_TTL:
            return JSONResponse(cached_data)
    try:
        data = fetcher()
        _cache[cache_key] = (now, data)
        if is_past_date(date) and not data.get("error"):
            db_put(date, endpoint, data)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/trips/today")
@cached(ttl=TRIP_CACHE_TTL)
def api_trips_today():
    return get_client().get_trip_today()

@app.get("/api/trips/{date}")
async def api_trips_date(date: str):
    return _trip_endpoint(date, "trips", lambda: get_client().get_trip_today(date))

@app.get("/api/trips/month/{month}")
async def api_trips_month(month: str):
    cache_key = f"trips_month:{month}"
    now = time.time()
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if now - cached_time < TRIP_CACHE_TTL:
            return JSONResponse(cached_data)
    try:
        data = get_client().get_trip_month(month)
        _cache[cache_key] = (now, data)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/trip-details/{date}")
async def api_trip_details(date: str):
    return _trip_endpoint(date, "trip_details", lambda: get_client().get_trip_details(date))

@app.get("/api/trip-route/{date}/{index}")
async def api_trip_route(date: str, index: int = 0):
    return _trip_endpoint(date, f"trip_route_{index}", lambda: get_client().get_trip_route(date, index))

@app.get("/api/driving-score/{date}")
async def api_driving_score(date: str = None):
    if date:
        return _trip_endpoint(date, "driving_score", lambda: get_client().get_driving_analysis(date))
    try:
        return JSONResponse(get_client().get_driving_analysis(date))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/road-trip/{date}")
async def api_road_trip(date: str):
    return _trip_endpoint(date, "road_trip", lambda: get_client().get_road_trip(date))

@app.get("/api/fuel-cost/{date}")
async def api_fuel_cost(date: str):
    return _trip_endpoint(date, "fuel_cost", lambda: get_client().get_fuel_cost(date))


# --- Command endpoints (POST, invalidate cache after) ---

@app.post("/api/lock")
async def api_lock():
    try:
        result = get_client().lock_car()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/unlock")
async def api_unlock():
    try:
        result = get_client().unlock_car()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/climate/start")
async def api_climate_start(request: Request):
    try:
        body = await request.json()
        temp = body.get("temperature", 22.0)
        duration = body.get("duration", 10)
        defrost = body.get("defrost", False)
        result = get_client().start_climate(temp, duration, defrost)
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/climate/stop")
async def api_climate_stop():
    try:
        result = get_client().stop_climate()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/horn")
async def api_horn():
    try:
        result = get_client().honk_horn()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/flash")
async def api_flash():
    try:
        result = get_client().flash_lights()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/trunk/open")
async def api_trunk_open():
    try:
        result = get_client().open_trunk()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/trunk/close")
async def api_trunk_close():
    try:
        result = get_client().close_trunk()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/panic/start")
async def api_panic_start():
    try:
        result = get_client().start_panic_alarm()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/panic/stop")
async def api_panic_stop():
    try:
        result = get_client().stop_panic_alarm()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/refresh")
async def api_refresh():
    try:
        result = get_client().force_refresh()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/live-status")
async def api_live_status():
    try:
        result = get_client().get_live_status()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/windows/control")
async def api_windows_control(request: Request):
    try:
        body = await request.json()
        result = get_client().control_windows(
            front_left=body.get("front_left", 0),
            front_right=body.get("front_right", 0),
            back_left=body.get("back_left", 0),
            back_right=body.get("back_right", 0),
        )
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/valet")
async def api_valet(request: Request):
    try:
        body = await request.json()
        result = get_client().valet_mode(body.get("enable", True))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/destination")
async def api_destination(request: Request):
    try:
        body = await request.json()
        result = get_client().send_destination(
            name=body.get("name", ""),
            latitude=body.get("latitude", 0),
            longitude=body.get("longitude", 0),
            address=body.get("address", ""),
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/ac-only/start")
async def api_ac_only_start(request: Request):
    try:
        body = await request.json()
        result = get_client().start_ac_only(
            temperature=body.get("temperature", 22.0),
            duration=body.get("duration", 10),
            defrost=body.get("defrost", False),
        )
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/ac-only/stop")
async def api_ac_only_stop():
    try:
        result = get_client().stop_ac_only()
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/rename")
async def api_rename(request: Request):
    try:
        body = await request.json()
        result = get_client().rename_vehicle(body.get("name", ""))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/alerts/speed")
async def api_alert_speed(request: Request):
    try:
        body = await request.json()
        result = get_client().set_speed_alert(body.get("speed_kmh", 0))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/alerts/idle")
async def api_alert_idle(request: Request):
    try:
        body = await request.json()
        result = get_client().set_idle_alert(body.get("minutes", 0))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/alerts/valet")
async def api_alert_valet(request: Request):
    try:
        body = await request.json()
        result = get_client().set_valet_alert(
            speed_limit=body.get("speed_limit", 80),
            idle_limit=body.get("idle_limit", 10),
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/alerts/curfew")
async def api_alert_curfew(request: Request):
    try:
        body = await request.json()
        result = get_client().set_curfew_alert(body.get("enabled", True))
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/alerts/geofence")
async def api_alert_geofence(request: Request):
    try:
        body = await request.json()
        result = get_client().set_geofence_alert(
            latitude=body.get("latitude", 0),
            longitude=body.get("longitude", 0),
            radius_meters=body.get("radius_meters", 1000),
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/maintenance/update")
async def api_maintenance_update(request: Request):
    try:
        body = await request.json()
        result = get_client().update_maintenance_interval(
            item_name=body.get("item_name", ""),
            interval_km=body.get("interval_km", 10000),
            interval_months=body.get("interval_months", 12),
            enabled=body.get("enabled", True),
        )
        invalidate_cache()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# PWA manifest
@app.get("/manifest.json")
async def manifest():
    return JSONResponse({
        "name": "Kia Connect",
        "short_name": "Kia Connect",
        "description": "Control and monitor your Kia / Hyundai vehicle",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f6f2ed",
        "theme_color": "#05141f",
        "orientation": "portrait",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
