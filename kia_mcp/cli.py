#!/usr/bin/env python3
"""CLI for Kia Connect — used by Aiden/OpenClaw via exec on VPS."""

import json
import sys
from kia_mcp.config import get_config
from kia_mcp.client import KiaClient


def print_json(data: dict):
    print(json.dumps(data, indent=2, default=str))


COMMANDS = {
    "status": "Full vehicle status",
    "info": "Vehicle identity (model, VIN)",
    "locked": "Lock status for all doors",
    "windows": "Window open/closed status",
    "fuel": "Fuel level and driving range",
    "tires": "Tire pressure warnings",
    "climate": "AC and seat heater status",
    "lights": "Lamp status (headlamps, stop, turn)",
    "warnings": "Maintenance warnings",
    "health": "Extended car health (sunroof, parking brake, air quality, battery)",
    "service": "Maintenance schedule (when oil change, filters due)",
    "location": "GPS location with address and Maps link",
    "odometer": "Odometer reading",
    "battery": "12V battery level and status",
    "profile": "Vehicle profile, SIM, colors, features",
    "trips": "Today's trip history",
    "trips-month": "Monthly trip summary",
    "trip-route": "Detailed trip route with driving behavior (usage: trip-route [YYYYMMDD] [trip_index])",
    "send-dest": "Send destination to car nav (usage: send-dest 'Name' lat lon 'address')",
    "rate-limit": "Check API rate limit remaining",
    "alerts": "Current speed/idle/valet alert settings",
    "trip-details": "Detailed trips with FROM/TO addresses and maps links (usage: trip-details [YYYYMMDD])",
    "driving-score": "Driving analysis with score, mileage, tips (usage: driving-score [YYYYMMDD])",
    "fuel-cost": "Estimated fuel cost for a day (usage: fuel-cost [YYYYMMDD] [price_per_liter])",
    "next-service": "When is each service item due (oil, filters, tires)",
    "driving-summary": "Complete monthly driving report with safety score",
    "departure-times": "Your departure time patterns and peak hours",
    "frequent-places": "Your most visited locations with addresses",
    "lock": "Lock all doors",
    "unlock": "Unlock all doors",
    "ac-on": "Start AC (usage: ac-on [temp] [duration])",
    "ac-off": "Stop AC",
    "horn": "Honk horn + flash lights",
    "flash": "Flash hazard lights",
    "valet-on": "Enable valet mode",
    "valet-off": "Disable valet mode",
    "speed-alert": "Set speed alert (usage: speed-alert 120)",
    "idle-alert": "Set idle alert in minutes (usage: idle-alert 10)",
    "valet-alert": "Set valet alert with speed/idle limits (usage: valet-alert 80 10)",
    "update-service": "Update maintenance interval (usage: update-service 'Engine oil' 7500 12)",
    "curfew-alert": "Toggle curfew alert (usage: curfew-alert on/off)",
    "geofence": "Set geofence alert (usage: geofence lat lon [radius_m])",
    "road-trip": "Full road trip analysis with legs, stops, map (usage: road-trip YYYYMMDD)",
    "trunk-open": "Open trunk remotely",
    "trunk-close": "Close trunk remotely",
    "windows-open": "Open all windows",
    "windows-close": "Close all windows",
    "windows-vent": "Set all windows to ventilation mode",
    "ac-only": "Start AC without engine (usage: ac-only [temp] [duration])",
    "ac-only-off": "Stop AC-only mode",
    "rename": "Rename car in Kia Connect (usage: rename 'New Name')",
    "panic": "Trigger panic alarm (loud siren + lights)",
    "panic-off": "Stop panic alarm",
    "refresh": "Force refresh from car (rate limited)",
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("Usage: kia-connect <command>")
        print()
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd:15s} {desc}")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    cfg = get_config()
    client = KiaClient(**cfg)

    if cmd == "status":
        print_json(client.get_full_status())
    elif cmd == "info":
        print_json(client.get_vehicle_info())
    elif cmd == "locked":
        print_json(client.is_car_locked())
    elif cmd == "windows":
        print_json(client.get_windows())
    elif cmd == "fuel":
        print_json(client.get_fuel())
    elif cmd == "tires":
        print_json(client.get_tires())
    elif cmd == "climate":
        print_json(client.get_climate_status())
    elif cmd == "lights":
        print_json(client.get_lights())
    elif cmd == "warnings":
        print_json(client.get_warnings())
    elif cmd == "health":
        print_json(client.get_car_health())
    elif cmd == "service":
        print_json(client.get_maintenance_schedule())
    elif cmd == "location":
        print_json(client.get_location())
    elif cmd == "odometer":
        print_json(client.get_odometer())
    elif cmd == "battery":
        print_json(client.get_battery())
    elif cmd == "profile":
        print_json(client.get_vehicle_profile())
    elif cmd == "trips":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        print_json(client.get_trip_today(date))
    elif cmd == "trips-month":
        month = sys.argv[2] if len(sys.argv) > 2 else None
        print_json(client.get_trip_month(month))
    elif cmd == "trip-route":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        print_json(client.get_trip_route(date, idx))
    elif cmd == "send-dest":
        if len(sys.argv) < 5:
            print("Usage: kia-connect send-dest 'Name' latitude longitude ['address']", file=sys.stderr)
            sys.exit(1)
        name = sys.argv[2]
        lat = float(sys.argv[3])
        lon = float(sys.argv[4])
        addr = sys.argv[5] if len(sys.argv) > 5 else ""
        print_json(client.send_destination(name, lat, lon, addr))
    elif cmd == "rate-limit":
        print_json(client.get_rate_limit())
    elif cmd == "alerts":
        print_json(client.get_alert_settings())
    elif cmd == "trip-details":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        print_json(client.get_trip_details(date))
    elif cmd == "driving-score":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        print_json(client.get_driving_analysis(date))
    elif cmd == "fuel-cost":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        price = float(sys.argv[3]) if len(sys.argv) > 3 else 105.0
        print_json(client.get_fuel_cost(date, price))
    elif cmd == "next-service":
        print_json(client.get_next_service())
    elif cmd == "driving-summary":
        print_json(client.get_driving_summary())
    elif cmd == "departure-times":
        print_json(client.get_departure_patterns())
    elif cmd == "frequent-places":
        print_json(client.get_frequent_locations())
    elif cmd == "lock":
        print_json(client.lock_car())
    elif cmd == "unlock":
        print_json(client.unlock_car())
    elif cmd == "ac-on":
        temp = float(sys.argv[2]) if len(sys.argv) > 2 else 22.0
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        print_json(client.start_climate(temp, duration))
    elif cmd == "ac-off":
        print_json(client.stop_climate())
    elif cmd == "horn":
        print_json(client.honk_horn())
    elif cmd == "flash":
        print_json(client.flash_lights())
    elif cmd == "valet-on":
        print_json(client.valet_mode(True))
    elif cmd == "valet-off":
        print_json(client.valet_mode(False))
    elif cmd == "speed-alert":
        speed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        print_json(client.set_speed_alert(speed))
    elif cmd == "idle-alert":
        mins = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        print_json(client.set_idle_alert(mins))
    elif cmd == "valet-alert":
        speed = int(sys.argv[2]) if len(sys.argv) > 2 else 80
        idle = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        print_json(client.set_valet_alert(speed, idle))
    elif cmd == "update-service":
        if len(sys.argv) < 5:
            print("Usage: kia-connect update-service 'Item Name' interval_km interval_months", file=sys.stderr)
            sys.exit(1)
        print_json(client.update_maintenance_interval(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])))
    elif cmd == "curfew-alert":
        enabled = sys.argv[2].lower() in ('on', 'true', '1', 'yes') if len(sys.argv) > 2 else True
        print_json(client.set_curfew_alert(enabled))
    elif cmd == "geofence":
        if len(sys.argv) < 4:
            print("Usage: kia-connect geofence latitude longitude [radius_meters]", file=sys.stderr)
            sys.exit(1)
        lat = float(sys.argv[2])
        lon = float(sys.argv[3])
        radius = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
        print_json(client.set_geofence_alert(lat, lon, radius))
    elif cmd == "road-trip":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        if not date:
            print("Usage: kia-connect road-trip YYYYMMDD", file=sys.stderr)
            sys.exit(1)
        print_json(client.get_road_trip(date))
    elif cmd == "trunk-open":
        print_json(client.open_trunk())
    elif cmd == "trunk-close":
        print_json(client.close_trunk())
    elif cmd == "windows-open":
        print_json(client.control_windows(1, 1, 1, 1))
    elif cmd == "windows-close":
        print_json(client.control_windows(0, 0, 0, 0))
    elif cmd == "windows-vent":
        print_json(client.control_windows(2, 2, 2, 2))
    elif cmd == "ac-only":
        temp = float(sys.argv[2]) if len(sys.argv) > 2 else 22.0
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        print_json(client.start_ac_only(temp, duration))
    elif cmd == "ac-only-off":
        print_json(client.stop_ac_only())
    elif cmd == "rename":
        if len(sys.argv) < 3:
            print("Usage: kia-connect rename 'New Name'", file=sys.stderr)
            sys.exit(1)
        print_json(client.rename_vehicle(sys.argv[2]))
    elif cmd == "panic":
        print_json(client.start_panic_alarm())
    elif cmd == "panic-off":
        print_json(client.stop_panic_alarm())
    elif cmd == "refresh":
        print_json(client.force_refresh())
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Run 'kia-connect help' for available commands", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
