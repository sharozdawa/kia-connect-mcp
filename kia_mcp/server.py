from mcp.server.fastmcp import FastMCP
from kia_mcp.config import get_config
from kia_mcp.client import KiaClient

mcp = FastMCP("Kia Connect", dependencies=["hyundai-kia-connect-api"])

_client: KiaClient | None = None


def _get_client() -> KiaClient:
    global _client
    if _client is None:
        cfg = get_config()
        _client = KiaClient(**cfg)
    return _client


# ── Read-Only Tools (no confirmation needed) ──


@mcp.tool()
def get_vehicle_info() -> dict:
    """Get vehicle identity: name, model, VIN, engine type, registration date."""
    return _get_client().get_vehicle_info()


@mcp.tool()
def get_full_status() -> dict:
    """Get complete vehicle status — all 45+ data points including doors, windows, fuel, tires, climate, lights, and warnings."""
    return _get_client().get_full_status()


@mcp.tool()
def is_car_locked() -> dict:
    """Check if the car is locked. Returns lock status for all doors, trunk, and hood."""
    return _get_client().is_car_locked()


@mcp.tool()
def get_windows() -> dict:
    """Check if all windows are closed. Returns open/closed status for each window."""
    return _get_client().get_windows()


@mcp.tool()
def get_fuel() -> dict:
    """Get fuel level percentage, low fuel warning, and estimated driving range in km."""
    return _get_client().get_fuel()


@mcp.tool()
def get_tires() -> dict:
    """Get tire pressure warnings for each wheel. Shows which tires have low pressure."""
    return _get_client().get_tires()


@mcp.tool()
def get_climate_status() -> dict:
    """Get AC status, set temperature, defrost, seat heater/cooler status, and steering wheel heater."""
    return _get_client().get_climate_status()


@mcp.tool()
def get_lights() -> dict:
    """Get status of all lamps — headlamps, stop lamps, and turn signals. Useful for checking if any bulb is out."""
    return _get_client().get_lights()


@mcp.tool()
def get_warnings() -> dict:
    """Get maintenance warnings: washer fluid low, brake fluid low, smart key battery low, engine oil, 12V battery."""
    return _get_client().get_warnings()


@mcp.tool()
def get_location() -> dict:
    """Get GPS location of the car — latitude, longitude, street address, last update time, and a Google Maps link."""
    return _get_client().get_location()


@mcp.tool()
def get_car_health() -> dict:
    """Get extended car health: sunroof, parking brake, gear position, hazard lights, air purifier, cabin air quality, 12V battery, engine oil."""
    return _get_client().get_car_health()


@mcp.tool()
def get_trip_route(date: str | None = None, trip_index: int = 0) -> dict:
    """Get detailed route for a specific trip — per-trip distance, speed, hard braking events, rapid acceleration events, excessive speed events, start/end GPS, and Google Maps route link. Use trip_index to select which trip (0 = most recent)."""
    return _get_client().get_trip_route(date, trip_index)


@mcp.tool()
def send_destination(name: str, latitude: float, longitude: float, address: str = "", confirm: bool = False) -> dict:
    """Send a destination/POI directly to the car's navigation system. Provide name, latitude, longitude, and optional address. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will send '{name}' ({latitude}, {longitude}) to your car's navigation. Call again with confirm=True."}
    return _get_client().send_destination(name, latitude, longitude, address)


@mcp.tool()
def get_rate_limit() -> dict:
    """Check API rate limit — how many requests remaining out of 100 per window."""
    return _get_client().get_rate_limit()


@mcp.tool()
def get_alert_settings() -> dict:
    """Get current alert configuration — speed alert, idle alert, and valet alert thresholds."""
    return _get_client().get_alert_settings()


@mcp.tool()
def get_trip_details(date: str | None = None) -> dict:
    """Get detailed trip history with FROM and TO addresses, GPS coordinates, Google Maps links, and start/end times for each trip. Pass date as YYYYMMDD or leave empty for today."""
    return _get_client().get_trip_details(date)


@mcp.tool()
def get_driving_analysis(date: str | None = None) -> dict:
    """Analyze driving performance for a day — driving score, mileage estimate, idle ratio, speed consistency, and tips to improve. Pass date as YYYYMMDD or leave empty for today."""
    return _get_client().get_driving_analysis(date)


@mcp.tool()
def get_maintenance_schedule() -> dict:
    """Get service schedule — when engine oil, air filter, fuel filter, tires, etc. are due. Shows interval and km remaining for each item."""
    return _get_client().get_maintenance_schedule()


@mcp.tool()
def get_odometer() -> dict:
    """Get current odometer reading in km."""
    return _get_client().get_odometer()


@mcp.tool()
def get_battery() -> dict:
    """Get 12V battery status — charge percentage, charging warning, discharge alert, and sleep mode."""
    return _get_client().get_battery()


@mcp.tool()
def get_vehicle_profile() -> dict:
    """Get vehicle profile — model year, colors, SIM details, transmission type, and all equipped features (heated seats, air purifier, etc.)."""
    return _get_client().get_vehicle_profile()


@mcp.tool()
def get_trip_today(date: str | None = None) -> dict:
    """Get today's trip history — each trip's distance, drive time, idle time, average and max speed. Pass date as YYYYMMDD for a specific day."""
    return _get_client().get_trip_today(date)


@mcp.tool()
def get_trip_month(month: str | None = None) -> dict:
    """Get monthly trip summary — total distance, drive time, and daily trip counts. Pass month as YYYYMM for a specific month."""
    return _get_client().get_trip_month(month)


# ── Computed Insight Tools ──


@mcp.tool()
def get_fuel_cost(date: str | None = None, fuel_price_per_liter: float = 105.0) -> dict:
    """Calculate estimated fuel cost for a day's driving. Pass date as YYYYMMDD and fuel price in INR/liter (default ₹105). Returns distance, fuel used, total cost, and cost per km."""
    return _get_client().get_fuel_cost(date, fuel_price_per_liter)


@mcp.tool()
def get_next_service() -> dict:
    """Predict when each service item is due — engine oil, filters, tires, etc. Shows km remaining, estimated days remaining, and due date based on your daily driving average."""
    return _get_client().get_next_service()


@mcp.tool()
def get_driving_summary() -> dict:
    """Complete monthly driving summary — total distance, trips, safety score (hard braking/rapid acceleration/excess speed across ALL trips), drive profile, mileage, and fuel status."""
    return _get_client().get_driving_summary()


@mcp.tool()
def get_departure_patterns() -> dict:
    """Analyze your departure time patterns — when you typically start driving, peak hours, earliest and latest departures, and departures by hour of day."""
    return _get_client().get_departure_patterns()


@mcp.tool()
def get_frequent_locations() -> dict:
    """Find your most visited locations based on trip start/end coordinates. Shows visit count, address, and Google Maps link for each location."""
    return _get_client().get_frequent_locations()


# ── Command Tools (all require user confirmation) ──


@mcp.tool()
def lock_car(confirm: bool = False) -> dict:
    """Lock all doors of the car. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will LOCK your car. Call again with confirm=True to proceed."}
    return _get_client().lock_car()


@mcp.tool()
def unlock_car(confirm: bool = False) -> dict:
    """Unlock all doors of the car. Set confirm=True to execute. SECURITY SENSITIVE — only unlock when the user explicitly asks."""
    if not confirm:
        return {"status": "confirmation_required", "message": "⚠️ This will UNLOCK your car. Call again with confirm=True to proceed."}
    return _get_client().unlock_car()


@mcp.tool()
def start_climate(temperature: float = 22.0, duration: int = 10, defrost: bool = False, confirm: bool = False) -> dict:
    """Start remote climate control (AC). Temperature in Celsius (14-29.5), duration in minutes. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will start AC at {temperature}°C for {duration} minutes. Call again with confirm=True to proceed."}
    return _get_client().start_climate(temperature, duration, defrost)


@mcp.tool()
def stop_climate(confirm: bool = False) -> dict:
    """Stop remote climate control. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will stop the remote AC. Call again with confirm=True to proceed."}
    return _get_client().stop_climate()


@mcp.tool()
def flash_lights(confirm: bool = False) -> dict:
    """Flash the hazard lights for ~30 seconds. Useful for finding the car in a parking lot. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will flash hazard lights on your car. Call again with confirm=True to proceed."}
    return _get_client().flash_lights()


@mcp.tool()
def honk_horn(confirm: bool = False) -> dict:
    """Honk the horn and flash lights for ~30 seconds. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will HONK the horn and flash lights on your car. Call again with confirm=True to proceed."}
    return _get_client().honk_horn()


@mcp.tool()
def valet_mode(enable: bool = True, confirm: bool = False) -> dict:
    """Enable or disable valet mode. Restricts speed and zone for valet drivers. Set confirm=True to execute."""
    action = "enable" if enable else "disable"
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will {action} valet mode. Call again with confirm=True to proceed."}
    return _get_client().valet_mode(enable)


@mcp.tool()
def set_speed_alert(speed_kmh: int, confirm: bool = False) -> dict:
    """Set a speed alert — get notified when car exceeds this speed. Set to 0 to disable. Requires force_refresh first if car is sleeping. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will set a speed alert at {speed_kmh} km/h. Call again with confirm=True."}
    return _get_client().set_speed_alert(speed_kmh)


@mcp.tool()
def set_idle_alert(minutes: int, confirm: bool = False) -> dict:
    """Set an idle alert — get notified when car idles longer than this. Set to 0 to disable. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will set an idle alert at {minutes} minutes. Call again with confirm=True."}
    return _get_client().set_idle_alert(minutes)


@mcp.tool()
def set_valet_alert(speed_limit: int = 80, idle_limit: int = 10, confirm: bool = False) -> dict:
    """Set valet alert — get notified when car exceeds speed limit or idles too long while with a valet. Set speed_limit=0 to disable. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will set valet alert: speed limit {speed_limit} km/h, idle limit {idle_limit} min. Call again with confirm=True."}
    return _get_client().set_valet_alert(speed_limit, idle_limit)


@mcp.tool()
def update_maintenance_interval(item_name: str, interval_km: int, interval_months: int, enabled: bool = True, confirm: bool = False) -> dict:
    """Update a maintenance service interval. Items: 'Engine oil', 'Oil Filter', 'Air Cleaner', 'Fuel filter', 'Tire position change', 'Wheel alignment', etc. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will update '{item_name}' interval to {interval_km}km / {interval_months} months (enabled={enabled}). Call again with confirm=True."}
    return _get_client().update_maintenance_interval(item_name, interval_km, interval_months, enabled)


@mcp.tool()
def set_curfew_alert(enabled: bool = True, confirm: bool = False) -> dict:
    """Enable or disable curfew alert — get notified when car is used outside allowed hours. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will {'enable' if enabled else 'disable'} the curfew alert. Call again with confirm=True."}
    return _get_client().set_curfew_alert(enabled)


@mcp.tool()
def set_geofence_alert(latitude: float, longitude: float, radius_meters: int = 1000, confirm: bool = False) -> dict:
    """Set a geofence alert — get notified when car leaves this area. Provide center GPS and radius in meters. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will set a geofence at ({latitude}, {longitude}) with {radius_meters}m radius. Call again with confirm=True."}
    return _get_client().set_geofence_alert(latitude, longitude, radius_meters)


@mcp.tool()
def get_road_trip(date: str) -> dict:
    """Analyze a full road trip — leg-by-leg breakdown with FROM/TO cities, driving behavior (hard braking, rapid acceleration, excessive speed), stop detection, GPS waypoints, route map link, and fuel cost estimate. Pass date as YYYYMMDD."""
    return _get_client().get_road_trip(date)


@mcp.tool()
def open_trunk(confirm: bool = False) -> dict:
    """Open the trunk remotely. Set confirm=True to execute. SECURITY SENSITIVE."""
    if not confirm:
        return {"status": "confirmation_required", "message": "⚠️ This will OPEN your car's trunk remotely. Call again with confirm=True to proceed."}
    return _get_client().open_trunk()


@mcp.tool()
def close_trunk(confirm: bool = False) -> dict:
    """Close the trunk remotely. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will CLOSE your car's trunk. Call again with confirm=True to proceed."}
    return _get_client().close_trunk()


@mcp.tool()
def control_windows(front_left: int = 0, front_right: int = 0, back_left: int = 0, back_right: int = 0, confirm: bool = False) -> dict:
    """Control car windows remotely. Values: 0=close, 1=open, 2=ventilation. Set confirm=True to execute. SECURITY SENSITIVE."""
    state_map = {0: "close", 1: "open", 2: "ventilation"}
    desc = f"FL={state_map.get(front_left)}, FR={state_map.get(front_right)}, BL={state_map.get(back_left)}, BR={state_map.get(back_right)}"
    if not confirm:
        return {"status": "confirmation_required", "message": f"⚠️ This will set windows to: {desc}. Call again with confirm=True to proceed."}
    return _get_client().control_windows(front_left, front_right, back_left, back_right)


@mcp.tool()
def start_ac_only(temperature: float = 22.0, duration: int = 10, defrost: bool = False, confirm: bool = False) -> dict:
    """Start AC only (without engine start, EU-style temperature control). Temperature in Celsius (14-29.5). Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will start AC-only at {temperature}°C for {duration} minutes (no engine start). Call again with confirm=True to proceed."}
    return _get_client().start_ac_only(temperature, duration, defrost)


@mcp.tool()
def stop_ac_only(confirm: bool = False) -> dict:
    """Stop AC-only mode. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will stop the AC-only mode. Call again with confirm=True to proceed."}
    return _get_client().stop_ac_only()


@mcp.tool()
def rename_vehicle(new_name: str, confirm: bool = False) -> dict:
    """Rename your car's nickname in Kia Connect. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": f"This will rename your car to '{new_name}'. Call again with confirm=True."}
    return _get_client().rename_vehicle(new_name)


@mcp.tool()
def start_panic_alarm(confirm: bool = False) -> dict:
    """Trigger the car's PANIC alarm remotely — loud siren + lights. Like the panic button on your key fob. EMERGENCY USE. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "⚠️ This will trigger the PANIC ALARM (loud siren + flashing lights) on your car. EMERGENCY USE ONLY. Call again with confirm=True."}
    return _get_client().start_panic_alarm()


@mcp.tool()
def stop_panic_alarm(confirm: bool = False) -> dict:
    """Stop the panic alarm. Set confirm=True to execute."""
    if not confirm:
        return {"status": "confirmation_required", "message": "This will stop the panic alarm. Call again with confirm=True."}
    return _get_client().stop_panic_alarm()


# ── Maintenance Tool (rate limited) ──


@mcp.tool()
def force_refresh() -> dict:
    """Wake the car's TCU to get fresh data. Rate limited to once per 30 minutes to protect the 12V battery from drain."""
    return _get_client().force_refresh()


@mcp.tool()
def get_live_status() -> dict:
    """Get LIVE status from the car — wakes the TCU, waits for fresh data, then returns updated status. Use this when cached data is stale. Rate limited to once per 30 minutes to protect 12V battery."""
    return _get_client().get_live_status()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
