import datetime as dt
import logging
import dataclasses
from hyundai_kia_connect_api import VehicleManager
from hyundai_kia_connect_api.const import VEHICLE_LOCK_ACTION, VALET_MODE_ACTION
from hyundai_kia_connect_api.ApiImpl import ClimateRequestOptions
from hyundai_kia_connect_api.utils import get_index_into_hex_temp

_LOGGER = logging.getLogger(__name__)

FORCE_REFRESH_INTERVAL = 1800  # 30 minutes in seconds


class KiaClient:
    def __init__(
        self,
        username: str,
        password: str,
        pin: str,
        region: int,
        brand: int,
        tank_liters: float = 45.0,
        fuel_price: float = 105.0,
    ):
        self._vm = VehicleManager(
            region=region,
            brand=brand,
            username=username,
            password=password,
            pin=pin,
        )
        self._logged_in = False
        self._last_force_refresh: dt.datetime | None = None
        self._tank_liters = tank_liters
        self._fuel_price = fuel_price

    def _ensure_login(self):
        if not self._logged_in:
            self._vm.check_and_refresh_token()
            self._logged_in = True

    def _get_vehicle(self):
        self._ensure_login()
        if not self._vm.vehicles:
            raise RuntimeError("No vehicles found in your Kia Connect account")
        return next(iter(self._vm.vehicles.values()))

    def _vehicle_to_dict(self, v) -> dict:
        skip = {"data", "enabled", "key", "timezone"}
        result = {}
        for f in dataclasses.fields(v):
            name = f.name.lstrip("_")
            if name in skip:
                continue
            val = getattr(v, name, None)
            if val is None:
                continue
            if isinstance(val, dt.datetime):
                val = val.isoformat()
            elif isinstance(val, dt.time):
                val = val.isoformat()
            elif hasattr(val, "value"):
                val = val.value
            result[name] = val
        return result

    def get_vehicle_info(self) -> dict:
        v = self._get_vehicle()
        return {
            "id": v.id,
            "name": v.name,
            "model": v.model,
            "vin": v.VIN,
            "engine_type": v.engine_type.value if v.engine_type else None,
            "registration_date": str(v.registration_date),
        }

    def get_cached_status(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return self._vehicle_to_dict(v)

    def get_full_status(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return self._vehicle_to_dict(v)

    def is_car_locked(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "is_locked": v.is_locked,
            "front_left_door_open": v.front_left_door_is_open,
            "front_right_door_open": v.front_right_door_is_open,
            "back_left_door_open": v.back_left_door_is_open,
            "back_right_door_open": v.back_right_door_is_open,
            "trunk_open": v.trunk_is_open,
            "hood_open": v.hood_is_open,
            "last_updated": v.last_updated_at.isoformat() if v.last_updated_at else None,
        }

    def get_windows(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "front_left_open": v.front_left_window_is_open,
            "front_right_open": v.front_right_window_is_open,
            "back_left_open": v.back_left_window_is_open,
            "back_right_open": v.back_right_window_is_open,
        }

    def get_fuel(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "fuel_level_percent": v.fuel_level,
            "fuel_low_warning": v.fuel_level_is_low,
            "driving_range_km": v.fuel_driving_range,
            "driving_range_unit": v._fuel_driving_range_unit,
        }

    def get_tires(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "all_ok": not v.tire_pressure_all_warning_is_on,
            "front_left_warning": v.tire_pressure_front_left_warning_is_on,
            "front_right_warning": v.tire_pressure_front_right_warning_is_on,
            "rear_left_warning": v.tire_pressure_rear_left_warning_is_on,
            "rear_right_warning": v.tire_pressure_rear_right_warning_is_on,
        }

    def get_climate_status(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "ac_on": v.air_control_is_on,
            "set_temperature": v.air_temperature,
            "temperature_unit": v._air_temperature_unit,
            "defrost_on": v.defrost_is_on,
            "steering_wheel_heater": v.steering_wheel_heater_is_on,
            "rear_window_heater": v.back_window_heater_is_on,
            "front_left_seat": v.front_left_seat_status,
            "front_right_seat": v.front_right_seat_status,
            "rear_left_seat": v.rear_left_seat_status,
            "rear_right_seat": v.rear_right_seat_status,
        }

    def get_lights(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "headlamp_on": v.headlamp_status,
            "left_low_beam": v.headlamp_left_low,
            "right_low_beam": v.headlamp_right_low,
            "left_stop_lamp": v.stop_lamp_left,
            "right_stop_lamp": v.stop_lamp_right,
            "left_front_turn": v.turn_signal_left_front,
            "right_front_turn": v.turn_signal_right_front,
            "left_rear_turn": v.turn_signal_left_rear,
            "right_rear_turn": v.turn_signal_right_rear,
        }

    def get_warnings(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        raw = v.data or {}
        return {
            "washer_fluid_low": v.washer_fluid_warning_is_on,
            "brake_fluid_low": v.brake_fluid_warning_is_on,
            "smart_key_battery_low": v.smart_key_battery_warning_is_on,
            "engine_oil_warning": raw.get("engineOilStatus"),
            "battery_12v_state": raw.get("battery", {}).get("batState"),
            "battery_12v_warning": raw.get("battery", {}).get("batSignalReferenceValue", {}).get("batWarning"),
        }

    def get_location(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        address = None
        if v.location_latitude and v.location_longitude:
            try:
                self._vm.api.update_geocoded_location(self._vm.token, v, use_email=True)
                if v.geocode and v.geocode[0]:
                    address = v.geocode[0]
            except Exception:
                pass
        return {
            "latitude": v.location_latitude,
            "longitude": v.location_longitude,
            "address": address,
            "last_updated": v.location_last_updated_at.isoformat() if v.location_last_updated_at else None,
            "google_maps_link": f"https://maps.google.com/?q={v.location_latitude},{v.location_longitude}" if v.location_latitude else None,
        }

    def get_car_health(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        raw = v.data or {}
        battery = raw.get("battery", {})
        air = raw.get("airCleaning", {})
        return {
            "sunroof_open": raw.get("sunroofOpen"),
            "parking_brake_engaged": raw.get("parkingBrakeHighNotch"),
            "gear_in_neutral": raw.get("neutralPosition"),
            "hazard_lights_on": bool(raw.get("hazardStatus")),
            "air_purifier_on": bool(air.get("airPurifierStatus")),
            "cabin_air_quality": air.get("fineDustColor"),
            "battery_12v_state": battery.get("batState"),
            "battery_12v_warning": battery.get("batSignalReferenceValue", {}).get("batWarning"),
            "power_auto_cut_mode": battery.get("powerAutoCutMode"),
            "engine_oil_warning": raw.get("engineOilStatus"),
            "vehicle_movement_detected": raw.get("vehicleMovementHis"),
        }

    def get_maintenance_schedule(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/maintenance"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        response = requests.get(url, headers=headers).json()
        msg = response.get("resMsg", {})
        schedule = []
        for item in msg.get("mainList", []):
            schedule.append({
                "item": item["itemId"],
                "interval_km": item["items"]["distValue"],
                "interval_months": item["items"]["termValue"],
                "km_remaining": item["items"]["distValue"] - msg.get("odometer", 0),
            })
        return {
            "odometer_km": msg.get("odometer"),
            "schedule": schedule,
        }

    def get_odometer(self) -> dict:
        v = self._get_vehicle()
        self._vm.update_vehicle_with_cached_state(v.id)
        return {
            "odometer_km": v.odometer,
            "unit": v.odometer_unit,
        }

    def _get_ccs2_state(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/ccs2/carstatus/latest"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        response = requests.get(url, headers=headers, timeout=15).json()
        return response.get("resMsg", {}).get("state", {}).get("Vehicle", {})

    def get_battery(self) -> dict:
        state = self._get_ccs2_state()
        electronics = state.get("Electronics", {})
        battery = electronics.get("Battery", {})
        return {
            "battery_12v_percent": battery.get("Level"),
            "charging_warning": battery.get("Charging", {}).get("WarningLevel"),
            "sensor_reliable": bool(battery.get("SensorReliability")),
            "discharge_alert": bool(state.get("Body", {}).get("Lights", {}).get("DischargeAlert", {}).get("State")),
            "auto_cut_mode": electronics.get("AutoCut", {}).get("PowerMode"),
            "sleep_mode": bool(state.get("RemoteControl", {}).get("SleepMode")),
        }

    def get_vehicle_profile(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/profile"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        response = requests.get(url, headers=headers, timeout=15).json()
        info = response.get("resMsg", {}).get("vinInfo", [{}])[0]
        basic = info.get("basic", {})
        device = info.get("device", {})
        option = info.get("option", {})
        detail = info.get("detailInfo", {})
        seat = option.get("seatHeaterVent", {})
        return {
            "model": basic.get("modelName"),
            "model_year": basic.get("modelYear"),
            "transmission": "Automatic" if basic.get("transmission") == "AT" else "Manual",
            "vin": basic.get("vin"),
            "exterior_color": detail.get("outColor"),
            "interior_color": detail.get("inColor"),
            "sim_telecom": device.get("telecom"),
            "sim_active": device.get("simStatus") == "A",
            "sim_start": basic.get("simStartDate"),
            "sim_end": basic.get("simEndDate"),
            "head_unit": device.get("headUnitType"),
            "features": {
                "remote_control": bool(int(option.get("remoteControl", "0"))),
                "air_purifier": bool(option.get("airPurifierOption")),
                "fine_dust_sensor": bool(option.get("fineDustOption")),
                "horn_and_lights": bool(option.get("hornLightAvailable")),
                "lights_only": bool(option.get("lightOnlyAvailable")),
                "heated_rear_window": bool(int(option.get("heatingRearWindow", "0"))),
                "heated_steering_wheel": bool(int(option.get("heatingSteeringWheel", "0"))),
                "heated_side_mirrors": bool(int(option.get("heatingSideMirror", "0"))),
                "front_driver_seat_heat_levels": seat.get("drvSeatHeat"),
                "front_passenger_seat_heat_levels": seat.get("astSeatHeat"),
                "valet_service": bool(info.get("serviceOption", {}).get("valetServiceOption")),
            },
        }

    def get_trip_today(self, date_str: str | None = None) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")
        try:
            self._vm.api.update_day_trip_info(self._vm.token, v, date_str)
        except (AttributeError, TypeError):
            pass
        if v.day_trip_info is None:
            raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
            day_list = raw.get("resMsg", {}).get("dayTripList", [])
            if not day_list:
                return {"date": date_str, "trips": [], "summary": None}
            msg = day_list[0]
            summary = {
                "drive_time_min": msg.get("tripDrvTime"),
                "idle_time_min": msg.get("tripIdleTime"),
                "distance_km": msg.get("tripDist"),
                "avg_speed_kmh": msg.get("tripAvgSpeed"),
                "max_speed_kmh": msg.get("tripMaxSpeed"),
            }
            trips = []
            for t in msg.get("tripList", []):
                trip = {
                    "time": t.get("tripTime"),
                    "drive_time_min": t.get("tripDrvTime"),
                    "idle_time_min": t.get("tripIdleTime"),
                    "distance_km": t.get("tripDist"),
                    "avg_speed_kmh": t.get("tripAvgSpeed"),
                    "max_speed_kmh": t.get("tripMaxSpeed"),
                }
                if any(v is not None for v in trip.values()):
                    trips.append(trip)
            return {"date": date_str, "summary": summary, "trip_count": len(msg.get("tripList", [])), "trips": trips}
        summary = None
        if v.day_trip_info.summary:
            s = v.day_trip_info.summary
            summary = {
                "drive_time_min": s.drive_time,
                "idle_time_min": s.idle_time,
                "distance_km": s.distance,
                "avg_speed_kmh": s.avg_speed,
                "max_speed_kmh": s.max_speed,
            }
        trips = []
        for t in (v.day_trip_info.trip_list or []):
            if t is None:
                continue
            trips.append({
                "time": t.hhmmss,
                "drive_time_min": t.drive_time,
                "idle_time_min": t.idle_time,
                "distance_km": t.distance,
                "avg_speed_kmh": t.avg_speed,
                "max_speed_kmh": t.max_speed,
            })
        return {"date": date_str, "summary": summary, "trips": trips}

    def get_trip_month(self, month_str: str | None = None) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        if month_str is None:
            month_str = dt.datetime.now().strftime("%Y%m")
        self._vm.api.update_month_trip_info(self._vm.token, v, month_str)
        if v.month_trip_info is None:
            return {"month": month_str, "days": [], "summary": None}
        summary = None
        if v.month_trip_info.summary:
            s = v.month_trip_info.summary
            summary = {
                "drive_time_min": s.drive_time,
                "idle_time_min": s.idle_time,
                "distance_km": s.distance,
                "avg_speed_kmh": s.avg_speed,
                "max_speed_kmh": s.max_speed,
            }
        days = []
        for d in v.month_trip_info.day_list or []:
            days.append({"date": d.yyyymmdd, "trip_count": d.trip_count})
        return {"month": month_str, "summary": summary, "days": days}

    def get_trip_route(self, date_str: str | None = None, trip_index: int = 0) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")
        import requests as req
        raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
        day_list = raw.get("resMsg", {}).get("dayTripList", [])
        if not day_list or not day_list[0].get("tripList"):
            return {"date": date_str, "error": "No trips found"}
        trip_list = day_list[0]["tripList"]
        if trip_index >= len(trip_list):
            return {"date": date_str, "error": f"Only {len(trip_list)} trips. Use trip_index 0-{len(trip_list)-1}"}
        trip = trip_list[trip_index]
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/tripinfo/detail"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {
            "tripPeriodType": 1,
            "setTripDay": date_str,
            "setTripStartTime": trip["tripStartTime"],
            "setServiceTID": trip["serviceTID"],
            "tripStartTime": trip["tripStartTime"],
            "tripEndTime": trip["tripEndTime"],
        }
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        info = r.get("resMsg", {}).get("tripInfo", {})
        waypoints = info.get("tripList", [])
        coords = [{"lat": w["lat"], "lon": w["lon"], "speed": w.get("tripSpeed"), "time": w.get("tripTime")} for w in waypoints]
        sampled = coords[::max(1, len(coords) // 20)]
        stops = []
        prev_coord = None
        for i, c in enumerate(coords):
            key = (round(c["lat"], 4), round(c["lon"], 4))
            if key == prev_coord:
                if not stops or stops[-1] != key:
                    stops.append(key)
                prev_coord = None
            else:
                prev_coord = key
        gmaps_url = None
        if coords:
            origin = f"{coords[0]['lat']},{coords[0]['lon']}"
            dest = f"{coords[-1]['lat']},{coords[-1]['lon']}"
            via = "|".join([f"{c['lat']},{c['lon']}" for c in sampled[1:-1]]) if len(sampled) > 2 else ""
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}"
            if via:
                gmaps_url += f"&waypoints={via}"
        return {
            "date": date_str,
            "trip_index": trip_index,
            "trip_count_today": len(trip_list),
            "distance_km": info.get("tripDist"),
            "drive_time_min": info.get("tripDrvTime"),
            "idle_time_min": info.get("tripIdleTime"),
            "avg_speed_kmh": info.get("tripAvgSpeed"),
            "max_speed_kmh": info.get("tripMaxSpeed"),
            "hard_braking_events": info.get("tripHardBreakingTime"),
            "rapid_acceleration_events": info.get("tripRapidAccelationTime"),
            "excessive_speed_events": info.get("tripExcessiveSpeedTime"),
            "start_gps": f"{info.get('tripStartLat')},{info.get('tripStartLon')}",
            "end_gps": f"{info.get('tripEndLat')},{info.get('tripEndLon')}",
            "waypoints": coords,
            "waypoint_count": len(coords),
            "stops": [{"lat": s[0], "lon": s[1]} for s in stops],
            "google_maps_url": gmaps_url,
        }

    def send_destination(self, name: str, latitude: float, longitude: float, address: str = "") -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/location/routes"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {
            "deviceID": self._vm.token.device_id,
            "poiInfoList": [{
                "phone": "",
                "waypointID": 0,
                "lang": 1,
                "src": "HERE",
                "coord": {"lat": latitude, "alt": 0, "lon": longitude, "type": 0},
                "addr": address,
                "zip": "",
                "placeid": "",
                "name": name,
            }],
        }
        r = req.post(url, json=payload, headers=headers, timeout=10).json()
        if r.get("retCode") == "S":
            return {"status": "destination_sent", "name": name, "address": address, "latitude": latitude, "longitude": longitude}
        return {"status": "failed", "error": str(r)}

    def get_rate_limit(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/status/latest"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.get(url, headers=headers, timeout=10)
        return {
            "limit": int(r.headers.get("x-ratelimit-limit", 0)),
            "remaining": int(r.headers.get("x-ratelimit-remaining", 0)),
            "reset_timestamp": int(r.headers.get("x-ratelimit-reset", 0)),
        }

    def get_alert_settings(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        response = requests.get(url, headers=headers, timeout=10).json()
        msg = response.get("resMsg", {})
        speed = msg.get("speedvalue", {})
        idle = msg.get("idlevalue", {})
        valet = msg.get("valetvalue", {})
        return {
            "speed_alert_enabled": bool(speed.get("keyvalue")),
            "speed_alert_kmh": speed.get("keyvalue") if speed.get("keyvalue") else None,
            "idle_alert_enabled": bool(idle.get("keyvalue")),
            "idle_alert_minutes": idle.get("keyvalue") if idle.get("keyvalue") else None,
            "valet_alert_enabled": bool(valet.get("keyvalue")),
            "valet_speed_limit": valet.get("speed") if valet.get("speed") else None,
            "valet_idle_limit": valet.get("idletime") if valet.get("idletime") else None,
        }

    def get_trip_details(self, date_str: str | None = None) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")
        raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
        day_list = raw.get("resMsg", {}).get("dayTripList", [])
        if not day_list:
            return {"date": date_str, "trips": []}

        msg = day_list[0]
        summary = {
            "drive_time_min": msg.get("tripDrvTime"),
            "idle_time_min": msg.get("tripIdleTime"),
            "distance_km": msg.get("tripDist"),
            "avg_speed_kmh": msg.get("tripAvgSpeed"),
            "max_speed_kmh": msg.get("tripMaxSpeed"),
        }

        import requests as req
        trips = []
        for t in msg.get("tripList", []):
            start_coord = t.get("tripStartCoord", {})
            end_coord = t.get("tripEndCoord", {})
            start_time = t.get("tripStartTime", "")
            end_time = t.get("tripEndTime", "")

            st = f"{start_time[8:10]}:{start_time[10:12]}" if len(start_time) >= 12 else start_time
            et = f"{end_time[8:10]}:{end_time[10:12]}" if len(end_time) >= 12 else end_time

            start_addr = None
            end_addr = None
            try:
                geo = req.get(
                    f"https://nominatim.openstreetmap.org/reverse?lat={start_coord['lat']}&lon={start_coord['lon']}&format=json&zoom=16",
                    headers={"user-agent": "curl/7.81.0"}, timeout=5,
                ).json()
                start_addr = geo.get("display_name")
            except Exception:
                pass
            try:
                geo = req.get(
                    f"https://nominatim.openstreetmap.org/reverse?lat={end_coord['lat']}&lon={end_coord['lon']}&format=json&zoom=16",
                    headers={"user-agent": "curl/7.81.0"}, timeout=5,
                ).json()
                end_addr = geo.get("display_name")
            except Exception:
                pass

            trips.append({
                "start_time": st,
                "end_time": et,
                "from_address": start_addr,
                "to_address": end_addr,
                "from_gps": f"{start_coord.get('lat')},{start_coord.get('lon')}",
                "to_gps": f"{end_coord.get('lat')},{end_coord.get('lon')}",
                "from_maps": f"https://maps.google.com/?q={start_coord.get('lat')},{start_coord.get('lon')}",
                "to_maps": f"https://maps.google.com/?q={end_coord.get('lat')},{end_coord.get('lon')}",
            })

        return {"date": date_str, "summary": summary, "trip_count": len(trips), "trips": trips}

    def get_driving_analysis(self, date_str: str | None = None) -> dict:
        v = self._get_vehicle()
        self._ensure_login()

        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")

        # Get today's trip data
        raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
        day_list = raw.get("resMsg", {}).get("dayTripList", [])
        if not day_list:
            return {"date": date_str, "analysis": "No trips found for this date."}

        msg = day_list[0]
        distance = msg.get("tripDist", 0)
        drive_time = msg.get("tripDrvTime", 0)
        idle_time = msg.get("tripIdleTime", 0)
        avg_speed = msg.get("tripAvgSpeed", 0)
        max_speed = msg.get("tripMaxSpeed", 0)
        trip_count = len(msg.get("tripList", []))

        # Get fuel data for mileage estimate
        self._vm.update_vehicle_with_cached_state(v.id)
        current_fuel = v.fuel_level
        current_range = v.fuel_driving_range

        # Car's computer gives us current range and fuel% — derive average mileage
        tank_size = self._tank_liters
        mileage_estimate = None
        fuel_used_liters = None
        if current_range and current_fuel and current_fuel > 0:
            full_tank_range = current_range / (current_fuel / 100.0)
            overall_mileage = full_tank_range / tank_size  # km per liter average
            mileage_estimate = round(overall_mileage, 1)
            fuel_used_liters = round(distance / overall_mileage, 1) if overall_mileage > 0 else None

        # Calculate scores
        total_time = drive_time + idle_time
        idle_ratio = round((idle_time / total_time) * 100, 1) if total_time > 0 else 0
        speed_consistency = round((avg_speed / max_speed) * 100, 1) if max_speed > 0 else 0

        # Determine driving type
        if avg_speed <= 25:
            drive_type = "Heavy city/traffic"
        elif avg_speed <= 45:
            drive_type = "City driving"
        elif avg_speed <= 65:
            drive_type = "Mixed city-highway"
        elif avg_speed <= 85:
            drive_type = "Highway driving"
        else:
            drive_type = "Fast highway driving"

        # Idle rating
        if idle_ratio <= 5:
            idle_rating = "Excellent — minimal idling"
        elif idle_ratio <= 15:
            idle_rating = "Good — normal city idle"
        elif idle_ratio <= 25:
            idle_rating = "Average — consider turning off engine at long stops"
        else:
            idle_rating = "High — too much idling, wastes fuel"

        # Speed consistency rating
        if speed_consistency >= 70:
            speed_rating = "Smooth — consistent speed, good for mileage"
        elif speed_consistency >= 50:
            speed_rating = "Moderate — some acceleration bursts"
        elif speed_consistency >= 35:
            speed_rating = "Aggressive — big gap between avg and max, heavy braking/acceleration"
        else:
            speed_rating = "Very aggressive — extreme speed variations, bad for mileage and brakes"

        # Max speed check
        if max_speed <= 60:
            speed_safety = "Safe city speeds"
        elif max_speed <= 80:
            speed_safety = "Normal"
        elif max_speed <= 100:
            speed_safety = "Moderate highway speed"
        elif max_speed <= 120:
            speed_safety = "Fast — watch out on Indian highways"
        else:
            speed_safety = "Too fast — dangerous, high fuel burn"

        # Overall score (out of 100)
        score = 100
        if idle_ratio > 15:
            score -= min(int((idle_ratio - 15) * 1.5), 20)
        if speed_consistency < 50:
            score -= min(int((50 - speed_consistency) * 0.8), 25)
        if max_speed > 120:
            score -= 15
        elif max_speed > 100:
            score -= 5
        score = max(score, 10)

        tips = []
        if idle_ratio > 15:
            tips.append(f"Reduce idling — you idled {idle_time} min out of {total_time} min. Turn off engine at stops longer than 60 seconds.")
        if speed_consistency < 50:
            tips.append(f"Drive smoother — your avg was {avg_speed} but max was {max_speed} km/h. Gradual acceleration saves 10-15% fuel.")
        if max_speed > 100:
            tips.append(f"Reduce top speed — above 100 km/h fuel consumption increases exponentially. 80-90 km/h is the sweet spot for mileage.")
        if avg_speed < 25:
            tips.append("Heavy traffic detected. Use AC in recirculation mode and keep steady pace in traffic to save fuel.")
        if not tips:
            tips.append("Great driving! Keep maintaining steady speeds and minimal idling for best mileage.")

        return {
            "date": date_str,
            "trip_count": trip_count,
            "distance_km": distance,
            "drive_time_min": drive_time,
            "idle_time_min": idle_time,
            "avg_speed_kmh": avg_speed,
            "max_speed_kmh": max_speed,
            "driving_type": drive_type,
            "car_avg_mileage_kmpl": mileage_estimate if mileage_estimate else "Not enough data",
            "estimated_fuel_used_liters": fuel_used_liters if fuel_used_liters else "Not enough data",
            "current_fuel_percent": current_fuel,
            "current_range_km": current_range,
            "scores": {
                "overall_score": f"{score}/100",
                "idle_ratio": f"{idle_ratio}% — {idle_rating}",
                "speed_consistency": f"{speed_consistency}% — {speed_rating}",
                "max_speed_check": f"{max_speed} km/h — {speed_safety}",
            },
            "tips_to_improve": tips,
        }

    # --- COMMANDS (all require confirmation) ---

    def lock_car(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        msg_id = self._vm.api.lock_action(self._vm.token, v, VEHICLE_LOCK_ACTION.LOCK)
        return {"status": "lock_command_sent", "message_id": msg_id}

    def unlock_car(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        msg_id = self._vm.api.lock_action(self._vm.token, v, VEHICLE_LOCK_ACTION.UNLOCK)
        return {"status": "unlock_command_sent", "message_id": msg_id}

    def start_climate(self, temperature: float = 22.0, duration: int = 10, defrost: bool = False) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        temp_range = [x * 0.5 for x in range(28, 60)]
        clamped = min(max(temperature, 14.0), 29.5)
        closest = min(temp_range, key=lambda x: abs(x - clamped))
        options = ClimateRequestOptions(
            set_temp=closest,
            duration=duration,
            defrost=defrost,
            climate=True,
            heating=0,
        )
        msg_id = self._vm.api.start_climate(self._vm.token, v, options)
        return {"status": "climate_started", "temperature": closest, "duration_min": duration, "defrost": defrost, "message_id": msg_id}

    def stop_climate(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        msg_id = self._vm.api.stop_climate(self._vm.token, v)
        return {"status": "climate_stopped", "message_id": msg_id}

    def flash_lights(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        msg_id = self._vm.api.start_hazard_lights(self._vm.token, v)
        return {"status": "lights_flashing", "message_id": msg_id}

    def honk_horn(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        msg_id = self._vm.api.start_hazard_lights_and_horn(self._vm.token, v)
        return {"status": "horn_and_lights_activated", "message_id": msg_id}

    def valet_mode(self, enable: bool) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        action = VALET_MODE_ACTION.ACTIVATE if enable else VALET_MODE_ACTION.DEACTIVATE
        msg_id = self._vm.api.valet_mode_action(self._vm.token, v, action)
        return {"status": "valet_enabled" if enable else "valet_disabled", "message_id": msg_id}

    def open_trunk(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/trunk"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {"action": "open", "deviceId": self._vm.token.device_id}
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "trunk_open_command_sent", "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def close_trunk(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/trunk"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {"action": "close", "deviceId": self._vm.token.device_id}
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "trunk_close_command_sent", "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def control_windows(self, front_left: int = 0, front_right: int = 0, back_left: int = 0, back_right: int = 0) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/windowcurtain"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {
            "frontLeft": front_left,
            "frontRight": front_right,
            "backLeft": back_left,
            "backRight": back_right,
        }
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        state_map = {0: "close", 1: "open", 2: "ventilation"}
        if r.get("retCode") == "S":
            return {
                "status": "window_command_sent",
                "front_left": state_map.get(front_left, front_left),
                "front_right": state_map.get(front_right, front_right),
                "back_left": state_map.get(back_left, back_left),
                "back_right": state_map.get(back_right, back_right),
                "message_id": r.get("msgId"),
            }
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def start_ac_only(self, temperature: float = 22.0, duration: int = 10, defrost: bool = False) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        temp_range = [x * 0.5 for x in range(28, 60)]
        clamped = min(max(temperature, 14.0), 29.5)
        closest = min(temp_range, key=lambda x: abs(x - clamped))
        hex_temp = get_index_into_hex_temp(temp_range.index(closest))
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/temperature"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {
            "action": "start",
            "hvacType": 0,
            "options": {
                "defrost": defrost,
                "heating1": 0,
            },
            "tempCode": hex_temp,
            "unit": "C",
        }
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "ac_only_started", "temperature": closest, "duration_min": duration, "defrost": defrost, "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def stop_ac_only(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/temperature"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {
            "action": "stop",
            "hvacType": 0,
            "options": {"defrost": True, "heating1": 1},
            "tempCode": "10H",
            "unit": "C",
        }
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "ac_only_stopped", "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def rename_vehicle(self, new_name: str) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/profile"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.put(url, json={"nickname": new_name}, headers=headers, timeout=10).json()
        if r.get("retCode") == "S":
            return {"status": "vehicle_renamed", "new_name": new_name}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def start_panic_alarm(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/alarm"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.post(url, json={"action": "start", "deviceId": self._vm.token.device_id}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "panic_alarm_activated", "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def stop_panic_alarm(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/control/alarm"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.post(url, json={"action": "stop", "deviceId": self._vm.token.device_id}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "panic_alarm_stopped", "message_id": r.get("msgId")}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def force_refresh(self) -> dict:
        now = dt.datetime.now()
        if self._last_force_refresh:
            elapsed = (now - self._last_force_refresh).total_seconds()
            if elapsed < FORCE_REFRESH_INTERVAL:
                remaining = int(FORCE_REFRESH_INTERVAL - elapsed)
                return {
                    "status": "rate_limited",
                    "message": f"Force refresh blocked — protects your 12V battery. Try again in {remaining} seconds.",
                    "next_available_in_seconds": remaining,
                }
        v = self._get_vehicle()
        self._ensure_login()
        self._vm.force_refresh_vehicle_state(v.id)
        self._last_force_refresh = now
        return {"status": "refreshed", "message": "Car woken up, fresh data retrieved"}

    def get_live_status(self) -> dict:
        import time
        now = dt.datetime.now()
        if self._last_force_refresh:
            elapsed = (now - self._last_force_refresh).total_seconds()
            if elapsed < FORCE_REFRESH_INTERVAL:
                remaining = int(FORCE_REFRESH_INTERVAL - elapsed)
                return {
                    "status": "rate_limited",
                    "message": f"Live status blocked — protects 12V battery. Try again in {remaining} seconds. Use get_full_status for cached data instead.",
                    "next_available_in_seconds": remaining,
                }
        v = self._get_vehicle()
        self._ensure_login()
        try:
            self._vm.force_refresh_vehicle_state(v.id)
        except Exception:
            pass
        self._last_force_refresh = now
        time.sleep(5)
        self._vm.update_vehicle_with_cached_state(v.id)
        return self._vehicle_to_dict(v)

    # --- ALERT CONFIGURATION ---

    def set_speed_alert(self, speed_kmh: int) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/speed"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.post(url, json={"keyvalue": speed_kmh}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "speed_alert_set", "speed_kmh": speed_kmh}
        return {"status": "failed", "error": str(r.get("resMsg", r)), "hint": "Car may be sleeping — try force_refresh first"}

    def set_idle_alert(self, minutes: int) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/idle"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.post(url, json={"keyvalue": minutes}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "idle_alert_set", "minutes": minutes}
        return {"status": "failed", "error": str(r.get("resMsg", r)), "hint": "Car may be sleeping — try force_refresh first"}

    def set_valet_alert(self, speed_limit: int = 80, idle_limit: int = 10) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/valet"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        enabled = 1 if speed_limit > 0 else 0
        r = req.post(url, json={"keyvalue": enabled, "speed": speed_limit, "idletime": idle_limit}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "valet_alert_set", "speed_limit_kmh": speed_limit, "idle_limit_min": idle_limit}
        return {"status": "failed", "error": str(r.get("resMsg", r)), "hint": "Car may be sleeping — try force_refresh first"}

    def update_maintenance_interval(self, item_name: str, interval_km: int, interval_months: int, enabled: bool = True) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/maintenance"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        current = req.get(url, headers=headers, timeout=10).json()
        main_list = current.get("resMsg", {}).get("mainList", [])
        found = False
        for item in main_list:
            if item["itemId"].lower() == item_name.lower():
                item["items"]["distValue"] = interval_km
                item["items"]["termValue"] = interval_months
                item["enable"] = enabled
                found = True
                break
        if not found:
            return {"status": "failed", "error": f"Item '{item_name}' not found. Available: {[i['itemId'] for i in main_list]}"}
        r = req.post(url, json={"mainList": main_list}, headers=headers, timeout=10).json()
        if r.get("retCode") == "S":
            return {"status": "maintenance_updated", "item": item_name, "interval_km": interval_km, "interval_months": interval_months, "enabled": enabled}
        return {"status": "failed", "error": str(r.get("resMsg", r))}

    def set_curfew_alert(self, enabled: bool) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/curfew"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        r = req.post(url, json={"keyvalue": 1 if enabled else 0}, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "curfew_alert_enabled" if enabled else "curfew_alert_disabled"}
        return {"status": "failed", "error": str(r.get("resMsg", r)), "hint": "Car may be sleeping — try force_refresh first"}

    def set_geofence_alert(self, latitude: float, longitude: float, radius_meters: int = 1000) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/geofence"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        payload = {"geofencevalue": [{"lat": latitude, "lon": longitude, "radius": radius_meters}]}
        r = req.post(url, json=payload, headers=headers, timeout=15).json()
        if r.get("retCode") == "S":
            return {"status": "geofence_set", "latitude": latitude, "longitude": longitude, "radius_m": radius_meters}
        return {"status": "failed", "error": str(r.get("resMsg", r)), "hint": "Car may be sleeping — try force_refresh first"}

    # --- ROAD TRIP ANALYZER ---

    def get_road_trip(self, date_str: str) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        import math

        raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
        day_list = raw.get("resMsg", {}).get("dayTripList", [])
        if not day_list:
            return {"date": date_str, "error": "No trips found"}

        msg = day_list[0]
        trip_list = msg.get("tripList", [])
        api_headers = self._vm.api._get_authenticated_headers(self._vm.token)
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/tripinfo/detail"

        legs = []
        total_waypoints = 0
        total_hard_brake = 0
        total_rapid_accel = 0
        total_excess_speed = 0
        total_stops = 0
        all_waypoints = []

        for trip in reversed(trip_list):
            payload = {
                "tripPeriodType": 1, "setTripDay": date_str,
                "setTripStartTime": trip["tripStartTime"],
                "setServiceTID": trip["serviceTID"],
                "tripStartTime": trip["tripStartTime"],
                "tripEndTime": trip["tripEndTime"],
            }
            try:
                r = req.post(url, json=payload, headers=api_headers, timeout=15).json()
                info = r.get("resMsg", {}).get("tripInfo", {})
            except Exception:
                continue

            wp = info.get("tripList", [])
            total_waypoints += len(wp)
            total_hard_brake += info.get("tripHardBreakingTime", 0)
            total_rapid_accel += info.get("tripRapidAccelationTime", 0)
            total_excess_speed += info.get("tripExcessiveSpeedTime", 0)

            stops = 0
            prev = None
            for w in wp:
                coord = (w["lat"], w["lon"])
                if coord == prev:
                    stops += 1
                    prev = None
                else:
                    prev = coord
                all_waypoints.append(coord)
            total_stops += stops

            st = trip["tripStartTime"]
            et = trip["tripEndTime"]
            start_addr = None
            end_addr = None
            try:
                geo = req.get(f"https://nominatim.openstreetmap.org/reverse?lat={info['tripStartLat']}&lon={info['tripStartLon']}&format=json&zoom=14",
                    headers={"user-agent": "curl/7.81.0"}, timeout=5).json()
                start_addr = geo.get("address", {}).get("county", geo.get("address", {}).get("city"))
            except Exception:
                pass
            try:
                geo = req.get(f"https://nominatim.openstreetmap.org/reverse?lat={info['tripEndLat']}&lon={info['tripEndLon']}&format=json&zoom=14",
                    headers={"user-agent": "curl/7.81.0"}, timeout=5).json()
                end_addr = geo.get("address", {}).get("county", geo.get("address", {}).get("city"))
            except Exception:
                pass

            legs.append({
                "start_time": f"{st[8:10]}:{st[10:12]}",
                "end_time": f"{et[8:10]}:{et[10:12]}",
                "from": start_addr,
                "to": end_addr,
                "distance_km": info.get("tripDist"),
                "drive_time_min": info.get("tripDrvTime"),
                "avg_speed_kmh": info.get("tripAvgSpeed"),
                "max_speed_kmh": info.get("tripMaxSpeed"),
                "hard_braking": info.get("tripHardBreakingTime"),
                "rapid_acceleration": info.get("tripRapidAccelationTime"),
                "excessive_speed": info.get("tripExcessiveSpeedTime"),
                "waypoints": len(wp),
                "stops_detected": stops,
            })

        # Build map URL
        sampled = all_waypoints[::max(1, len(all_waypoints) // 20)]
        map_url = None
        if sampled:
            map_url = f"https://www.google.com/maps/dir/{sampled[0][0]},{sampled[0][1]}/{sampled[-1][0]},{sampled[-1][1]}"

        # Mileage estimate
        self._vm.update_vehicle_with_cached_state(v.id)
        mileage = None
        fuel_cost = None
        total_dist = msg.get("tripDist", 0)
        if v.fuel_level and v.fuel_driving_range and v.fuel_level > 0:
            mileage = round((v.fuel_driving_range / (v.fuel_level / 100.0)) / self._tank_liters, 1)
            fuel_used = total_dist / mileage if mileage > 0 else 0
            fuel_cost = round(fuel_used * self._fuel_price, 0)

        return {
            "date": date_str,
            "total_distance_km": total_dist,
            "total_drive_time_min": msg.get("tripDrvTime"),
            "total_idle_time_min": msg.get("tripIdleTime"),
            "avg_speed_kmh": msg.get("tripAvgSpeed"),
            "max_speed_kmh": msg.get("tripMaxSpeed"),
            "total_legs": len(legs),
            "total_waypoints": total_waypoints,
            "total_stops_detected": total_stops,
            "total_hard_braking": total_hard_brake,
            "total_rapid_acceleration": total_rapid_accel,
            "total_excessive_speed": total_excess_speed,
            "estimated_mileage_kmpl": mileage,
            "estimated_fuel_cost_inr": fuel_cost,
            "route_map": map_url,
            "legs": legs,
        }

    # --- COMPUTED INSIGHTS (no extra API calls) ---

    def get_fuel_cost(self, date_str: str | None = None, fuel_price_per_liter: float | None = None) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        if date_str is None:
            date_str = dt.datetime.now().strftime("%Y%m%d")
        if fuel_price_per_liter is None:
            fuel_price_per_liter = self._fuel_price
        raw = self._vm.api._get_trip_info(self._vm.token, v, date_str, 1)
        day_list = raw.get("resMsg", {}).get("dayTripList", [])
        if not day_list:
            return {"date": date_str, "error": "No trips found"}
        msg = day_list[0]
        distance = msg.get("tripDist", 0)
        self._vm.update_vehicle_with_cached_state(v.id)
        current_fuel = v.fuel_level
        current_range = v.fuel_driving_range
        tank_size = self._tank_liters
        if current_range and current_fuel and current_fuel > 0:
            mileage = (current_range / (current_fuel / 100.0)) / tank_size
            fuel_used = distance / mileage if mileage > 0 else 0
            cost = fuel_used * fuel_price_per_liter
            return {
                "date": date_str,
                "distance_km": distance,
                "estimated_mileage_kmpl": round(mileage, 1),
                "estimated_fuel_used_liters": round(fuel_used, 1),
                "fuel_price_per_liter": fuel_price_per_liter,
                "estimated_cost": round(cost, 0),
                "cost_per_km": round(cost / distance, 1) if distance > 0 else 0,
            }
        return {"date": date_str, "distance_km": distance, "error": "Cannot estimate — no fuel data"}

    def get_next_service(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        url = self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/setting/alert/maintenance"
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        response = req.get(url, headers=headers, timeout=10).json()
        msg = response.get("resMsg", {})
        odometer = msg.get("odometer", 0)
        raw_trips = self._vm.api._get_trip_info(self._vm.token, v, dt.datetime.now().strftime("%Y%m"), 0)
        monthly = raw_trips.get("resMsg", {})
        days_with_trips = len(monthly.get("tripDayList", []))
        total_dist = monthly.get("tripDist", 0)
        daily_avg_km = total_dist / days_with_trips if days_with_trips > 0 else 50
        services = []
        for item in msg.get("mainList", []):
            km_remaining = item["items"]["distValue"] - odometer
            days_remaining = int(km_remaining / daily_avg_km) if daily_avg_km > 0 else None
            due_date = (dt.datetime.now() + dt.timedelta(days=days_remaining)).strftime("%Y-%m-%d") if days_remaining else None
            urgency = "overdue" if km_remaining <= 0 else "soon" if km_remaining < 1000 else "upcoming" if km_remaining < 3000 else "ok"
            services.append({
                "item": item["itemId"],
                "interval_km": item["items"]["distValue"],
                "km_remaining": km_remaining,
                "estimated_days_remaining": days_remaining,
                "estimated_due_date": due_date,
                "urgency": urgency,
            })
        services.sort(key=lambda x: x["km_remaining"])
        return {
            "odometer_km": odometer,
            "daily_avg_km": round(daily_avg_km, 0),
            "services": services,
        }

    def get_driving_summary(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        raw_month = self._vm.api._get_trip_info(self._vm.token, v, dt.datetime.now().strftime("%Y%m"), 0)
        monthly = raw_month.get("resMsg", {})
        days = monthly.get("tripDayList", [])
        total_trips = sum(d.get("tripCntDay", 0) for d in days)
        total_hard_brake = 0
        total_rapid_accel = 0
        total_excess_speed = 0
        trip_speeds = []
        base = 'https://prd.in-ccapi.kia.connected-car.io:8080'
        headers = self._vm.api._get_authenticated_headers(self._vm.token)
        for day_info in days:
            day = day_info["tripDayInMonth"]
            try:
                raw = self._vm.api._get_trip_info(self._vm.token, v, day, 1)
                trip_list = raw["resMsg"]["dayTripList"][0]["tripList"]
                for trip in trip_list:
                    try:
                        payload = {
                            "tripPeriodType": 1, "setTripDay": day,
                            "setTripStartTime": trip["tripStartTime"],
                            "setServiceTID": trip["serviceTID"],
                            "tripStartTime": trip["tripStartTime"],
                            "tripEndTime": trip["tripEndTime"],
                        }
                        r = req.post(
                            self._vm.api.SPA_API_URL + "vehicles/" + v.id + "/tripinfo/detail",
                            json=payload, headers=headers, timeout=15,
                        ).json()
                        info = r.get("resMsg", {}).get("tripInfo", {})
                        total_hard_brake += info.get("tripHardBreakingTime", 0)
                        total_rapid_accel += info.get("tripRapidAccelationTime", 0)
                        total_excess_speed += info.get("tripExcessiveSpeedTime", 0)
                        if info.get("tripAvgSpeed"):
                            trip_speeds.append(info["tripAvgSpeed"])
                    except Exception:
                        pass
            except Exception:
                pass
        self._vm.update_vehicle_with_cached_state(v.id)
        current_fuel = v.fuel_level
        current_range = v.fuel_driving_range
        tank_size = self._tank_liters
        mileage = None
        if current_range and current_fuel and current_fuel > 0:
            mileage = round((current_range / (current_fuel / 100.0)) / tank_size, 1)
        avg_trip_speed = round(sum(trip_speeds) / len(trip_speeds), 1) if trip_speeds else None
        if avg_trip_speed and avg_trip_speed <= 30:
            drive_profile = "Mostly city/traffic driving"
        elif avg_trip_speed and avg_trip_speed <= 50:
            drive_profile = "Mixed city driving"
        elif avg_trip_speed and avg_trip_speed <= 70:
            drive_profile = "Mixed city-highway"
        elif avg_trip_speed:
            drive_profile = "Highway-heavy driving"
        else:
            drive_profile = "Unknown"
        safety_score = 100
        if total_hard_brake > 0:
            safety_score -= min(total_hard_brake * 5, 30)
        if total_rapid_accel > 0:
            safety_score -= min(total_rapid_accel * 5, 20)
        if total_excess_speed > 0:
            safety_score -= min(total_excess_speed * 10, 30)
        return {
            "period": dt.datetime.now().strftime("%B %Y"),
            "total_distance_km": monthly.get("tripDist", 0),
            "total_drive_time_min": monthly.get("tripDrvTime", 0),
            "total_idle_time_min": monthly.get("tripIdleTime", 0),
            "total_trips": total_trips,
            "days_driven": len(days),
            "avg_daily_km": round(monthly.get("tripDist", 0) / len(days), 1) if days else 0,
            "avg_trip_speed_kmh": avg_trip_speed,
            "max_speed_ever_kmh": monthly.get("tripMaxSpeed", 0),
            "drive_profile": drive_profile,
            "car_avg_mileage_kmpl": mileage,
            "current_fuel_percent": current_fuel,
            "current_range_km": current_range,
            "odometer_km": v.odometer,
            "safety": {
                "score": f"{safety_score}/100",
                "hard_braking_events": total_hard_brake,
                "rapid_acceleration_events": total_rapid_accel,
                "excessive_speed_events": total_excess_speed,
            },
        }

    def get_departure_patterns(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        raw_month = self._vm.api._get_trip_info(self._vm.token, v, dt.datetime.now().strftime("%Y%m"), 0)
        days = raw_month.get("resMsg", {}).get("tripDayList", [])
        departures = []
        for day_info in days:
            day = day_info["tripDayInMonth"]
            try:
                raw = self._vm.api._get_trip_info(self._vm.token, v, day, 1)
                trip_list = raw["resMsg"]["dayTripList"][0]["tripList"]
                for trip in trip_list:
                    st = trip.get("tripStartTime", "")
                    if len(st) >= 12:
                        hour = int(st[8:10])
                        minute = int(st[10:12])
                        departures.append({
                            "date": f"{st[:4]}-{st[4:6]}-{st[6:8]}",
                            "time": f"{hour:02d}:{minute:02d}",
                            "hour": hour,
                        })
            except Exception:
                pass
        hour_counts = {}
        for d in departures:
            h = d["hour"]
            hour_counts[h] = hour_counts.get(h, 0) + 1
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        if departures:
            earliest = min(departures, key=lambda x: x["time"])
            latest = max(departures, key=lambda x: x["time"])
        else:
            earliest = latest = None
        return {
            "total_departures": len(departures),
            "departures": departures,
            "peak_hour": f"{peak_hour:02d}:00" if peak_hour is not None else None,
            "earliest_ever": earliest["time"] if earliest else None,
            "latest_ever": latest["time"] if latest else None,
            "departures_by_hour": {f"{h:02d}:00": c for h, c in sorted(hour_counts.items())},
        }

    def get_frequent_locations(self) -> dict:
        v = self._get_vehicle()
        self._ensure_login()
        import requests as req
        raw_month = self._vm.api._get_trip_info(self._vm.token, v, dt.datetime.now().strftime("%Y%m"), 0)
        days = raw_month.get("resMsg", {}).get("tripDayList", [])
        all_coords = []
        for day_info in days:
            day = day_info["tripDayInMonth"]
            try:
                raw = self._vm.api._get_trip_info(self._vm.token, v, day, 1)
                trip_list = raw["resMsg"]["dayTripList"][0]["tripList"]
                for trip in trip_list:
                    sc = trip.get("tripStartCoord", {})
                    ec = trip.get("tripEndCoord", {})
                    if sc.get("lat"):
                        all_coords.append((round(sc["lat"], 3), round(sc["lon"], 3)))
                    if ec.get("lat"):
                        all_coords.append((round(ec["lat"], 3), round(ec["lon"], 3)))
            except Exception:
                pass
        coord_counts = {}
        for c in all_coords:
            coord_counts[c] = coord_counts.get(c, 0) + 1
        sorted_locs = sorted(coord_counts.items(), key=lambda x: -x[1])
        locations = []
        for (lat, lon), count in sorted_locs[:10]:
            addr = None
            try:
                geo = req.get(
                    f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=16",
                    headers={"user-agent": "curl/7.81.0"}, timeout=5,
                ).json()
                addr = geo.get("display_name")
            except Exception:
                pass
            locations.append({
                "latitude": lat,
                "longitude": lon,
                "visit_count": count,
                "address": addr,
                "maps_link": f"https://maps.google.com/?q={lat},{lon}",
            })
        return {"total_unique_locations": len(coord_counts), "top_locations": locations}
