# Kia Connect MCP

> **Talk to your Kia.** "Did I lock the car? Pre-cool it for me. Where did I park? What was my driving score this week? Send 'IGI Airport T3' to nav. If the car leaves a 2 km radius after 11 PM, ping me."

An [MCP](https://modelcontextprotocol.io) server, CLI, and PWA dashboard for any Kia / Hyundai / Genesis vehicle that supports Kia Connect or Hyundai Bluelink. **52 tools**, every cloud-API capability the official app exposes, plus computed insights the official app *doesn't* give you.

Wraps [`hyundai-kia-connect-api`](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api). Works in every region that library supports — **Europe, USA, Canada, India, South Korea, Australia, China**.

## What you get

- **MCP server (52 tools)** — drop into Claude Code, Claude Desktop, or any MCP client and start talking to your car in plain English.
- **CLI (`kia-connect`)** — for shell scripts, cron jobs, voice assistants, terminal nerds.
- **PWA dashboard** *(optional)* — mobile-friendly FastAPI + Tailwind UI with server-side caching and SQLite trip history. Install to your iPhone home screen.

Every write/control command requires `confirm=True` so the LLM can't accidentally unlock your car or honk the horn. **Two-step confirmation is hardcoded — not a setting.**

---

## Why it's fun

Things you can suddenly do that the official app makes painful or impossible:

| Scenario | Sample ask | What happens |
|---|---|---|
| **Forgot to lock at 2 AM** | *"Hey Claude, lock my car"* | Two prompts → done. From bed. |
| **Pre-cool before stepping out** | *"Start the AC at 21°C for 15 minutes"* | Cabin's cool by the time you reach it. Summer-saver in Indian/Texas/UAE heat. |
| **Find car in a 4-floor mall** | *"Flash the lights and tell me where it is"* | GPS + Google Maps link + flashing hazards. |
| **Was that a bad drive?** | *"What was my driving score yesterday?"* | Out-of-100 score with hard braking, rapid acceleration, idle %, mileage tips. The app shows none of this. |
| **Road trip recap** | *"Analyze my Mumbai → Goa drive on 20251014"* | Leg-by-leg breakdown — FROM/TO cities, stops detected, hard braking events, fuel cost estimate, sampled GPS map link. |
| **Monthly fuel spend** | *"How much did I spend on fuel this week?"* | Distance × estimated mileage × your local price. |
| **Service prediction** | *"When's my next oil change?"* | Predicts the date based on your daily km average — not just "every 7,500 km". |
| **Find your patterns** | *"When do I usually leave for work?"* | Departure-time histogram across the last month. |
| **Most visited places** | *"Where do I drive most?"* | Top destinations with addresses and Maps links. |
| **Hand keys to a valet** | *"Set valet alert: cap at 60 km/h, idle limit 5 min"* | Notification if they break either limit. |
| **Geo-fence the teen driver** | *"Alert me if the car leaves a 2 km radius from home"* | Geofence set. |
| **Hot car panic** | *"Trigger the panic alarm"* | Loud siren + flashing lights. Emergency button without the key fob. |
| **Send POI to nav** | *"Send 'Andaz Delhi, Aerocity' to the car's navigation"* | Pin appears in the head unit. No phone-pairing dance. |
| **Did I leave a window cracked?** | *"Are all windows closed?"* | Per-window status. |
| **Tire warning before a trip** | *"Any tire warnings? Any maintenance flags?"* | Combined low-tire / brake fluid / washer / 12V battery report. |

---

## Install

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv) (recommended).

```bash
git clone https://github.com/sharozdawa/kia-connect-mcp.git
cd kia-connect-mcp
uv sync
cp .env.example .env
$EDITOR .env   # fill in KIA_USERNAME, KIA_PASSWORD, KIA_PIN
```

## Configure

Edit `.env`:

| Var | Required | Default | Notes |
|---|---|---|---|
| `KIA_USERNAME` | yes | — | Kia Connect / Hyundai Bluelink email |
| `KIA_PASSWORD` | yes | — | Account password |
| `KIA_PIN`      | for write commands | `""` | Required for remote lock/unlock and a few others |
| `KIA_REGION`   | yes | `6` | 1=Europe 2=Canada 3=USA 4=China 5=Australia **6=India** 7=South Korea |
| `KIA_BRAND`    | yes | `1` | **1=Kia** 2=Hyundai 3=Genesis |
| `KIA_TANK_LITERS` | no | `45` | Used by fuel cost / mileage estimates. Look up your model. |
| `KIA_FUEL_PRICE`  | no | `105` | Local fuel price per liter (any currency). |

---

## Use it

### As an MCP server (Claude Code)

```bash
claude mcp add kia-connect -- uv --directory /absolute/path/to/kia-connect-mcp run kia-mcp
```

### As an MCP server (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kia-connect": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/kia-connect-mcp", "run", "kia-mcp"],
      "env": {
        "KIA_USERNAME": "you@example.com",
        "KIA_PASSWORD": "...",
        "KIA_PIN": "0000",
        "KIA_REGION": "6",
        "KIA_BRAND": "1"
      }
    }
  }
}
```

### As a CLI

```bash
./kia status         # full vehicle status
./kia locked         # lock state for all doors
./kia location       # GPS + Maps link
./kia trips          # today's trips
./kia driving-score  # day's driving analysis
./kia fuel-cost      # estimated fuel cost for today
./kia lock           # lock the doors
./kia ac-on 22 10    # AC at 22°C for 10 min
./kia road-trip 20260420   # full leg-by-leg road trip analysis
./kia geofence 19.0760 72.8777 1500   # 1.5 km geofence alert at this point
./kia help           # full command list (50+)
```

The `./kia` wrapper auto-loads `.env` and runs through `uv`. Use it in cron, shell scripts, voice assistants, agents.

### As a PWA dashboard (optional)

The web dashboard pulls in FastAPI + Jinja, an optional extra:

```bash
uv sync --extra web
uv run --python 3.13 uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Open `http://<your-machine>:8000` on your phone and "Add to Home Screen". Server-side caches read endpoints for 2 minutes; persists trips in `trips.db`.

---

## Tool reference (52 tools)

### Status & state (16)

| Tool | What it does |
|---|---|
| `get_vehicle_info` | Identity: name, model, VIN, engine type, registration date |
| `get_full_status` | Complete dump — 45+ data points (doors, windows, fuel, tires, climate, lights, warnings) |
| `is_car_locked` | Lock state for every door + trunk + hood, with last-update timestamp |
| `get_windows` | Open/closed for each window |
| `get_fuel` | Fuel %, low-fuel warning, estimated km range |
| `get_tires` | Per-wheel low-pressure warnings |
| `get_climate_status` | AC, set temperature, defrost, seat heater/cooler, steering-wheel heater |
| `get_lights` | Headlamps, stop lamps, turn signals — useful to spot a dead bulb remotely |
| `get_warnings` | Washer fluid, brake fluid, smart-key battery, engine oil, 12V battery |
| `get_location` | GPS + reverse-geocoded street address + Google Maps link + last-update time |
| `get_car_health` | Sunroof, parking brake, gear position, hazards, air purifier, cabin air quality, 12V, engine oil |
| `get_battery` | 12V battery % + charging warning + discharge alert + sleep mode |
| `get_odometer` | Current km |
| `get_vehicle_profile` | Model year, body/interior colors, SIM details, transmission, every equipped feature |
| `get_alert_settings` | Current speed/idle/valet alert thresholds |
| `get_maintenance_schedule` | Service items + km intervals + km remaining for each |

### Trips & driving analytics (9)

| Tool | What it does |
|---|---|
| `get_trip_today` | Each trip today: distance, drive time, idle time, avg/max speed |
| `get_trip_month` | Monthly: total distance, drive time, daily trip counts |
| `get_trip_route` | One trip's route: hard-braking events, rapid acceleration events, excessive-speed events, start/end GPS, Google Maps route link |
| `get_trip_details` | Trips with FROM/TO **addresses** (reverse-geocoded), GPS, Maps links |
| `get_driving_analysis` | Score out of 100 + driving-type detection + idle ratio + speed-consistency rating + personalized tips |
| `get_driving_summary` | Whole-month report: distance, trips, safety score across **every** trip, drive profile, current fuel |
| `get_road_trip` | Multi-leg road trip: FROM/TO cities per leg, stop detection, behavior counts, sampled waypoints, route map link, fuel cost |
| `get_departure_patterns` | When you typically start driving — peak hours, earliest, latest, by-hour histogram |
| `get_frequent_locations` | Most visited places with visit count, address, Maps link |

### Computed insights (2)

| Tool | What it does |
|---|---|
| `get_fuel_cost` | For any day: distance, estimated mileage from car's own range data, fuel used, cost in your currency, cost per km |
| `get_next_service` | Predicts the **due date** for every service item based on your daily km average — not just the static interval |

### Control / commands (16, all require `confirm=True`)

| Tool | What it does |
|---|---|
| `lock_car` | Lock all doors |
| `unlock_car` | Unlock all doors *(security-sensitive — only on explicit ask)* |
| `start_climate` | Start AC at temperature/duration *(starts engine on ICE)* |
| `stop_climate` | Stop remote climate |
| `start_ac_only` | EU-style temperature-controlled AC **without** engine start |
| `stop_ac_only` | Stop AC-only |
| `flash_lights` | Hazard flash for ~30s — find your car in a parking lot |
| `honk_horn` | Horn + lights for ~30s |
| `open_trunk` | Remote trunk release *(security-sensitive)* |
| `close_trunk` | Close trunk |
| `control_windows` | Per-window control: 0=close, 1=open, 2=ventilation |
| `valet_mode` | Restrict speed/zone for a valet driver |
| `start_panic_alarm` | Loud siren + flashing lights — emergency only |
| `stop_panic_alarm` | Cancel panic alarm |
| `rename_vehicle` | Change the car's nickname in Kia Connect |
| `send_destination` | Push a POI (name + lat/lon + address) directly to the car's nav head unit |

### Alerts & geofencing (5)

| Tool | What it does |
|---|---|
| `set_speed_alert` | Notify when the car exceeds X km/h |
| `set_idle_alert` | Notify when idling longer than X minutes |
| `set_valet_alert` | Combined speed + idle limits for valet handoff |
| `set_curfew_alert` | Notify if the car is used outside allowed hours |
| `set_geofence_alert` | Notify if the car leaves a (lat, lon, radius) area |

### Maintenance (1)

| Tool | What it does |
|---|---|
| `update_maintenance_interval` | Change km/months for any service item (engine oil, oil filter, air cleaner, fuel filter, tire rotation, wheel alignment, …) |

### System (3)

| Tool | What it does |
|---|---|
| `force_refresh` | Wake the car's TCU and pull fresh data. **Rate-limited to once per 30 min** to protect the 12V battery. |
| `get_live_status` | Same as `force_refresh` but returns the fresh data inline |
| `get_rate_limit` | How many API calls remain in the current window |

---

## Sample Claude conversations

> **You:** Did I forget to lock the car?
> **Claude:** Front-left door is unlocked. Want me to lock it? *(asks confirmation, locks)*

> **You:** I'm leaving in 15 minutes — pre-cool the car to 21° and check fuel.
> **Claude:** Fuel is at 38% (~280 km range). Start AC at 21° for 15 min? *(confirms, starts)*

> **You:** Make a small report on my driving this week.
> **Claude:** *(calls `get_driving_summary`)* 6 days driven, 412 km, avg 42 km/h (mixed city), 3 hard-braking events, 1 rapid acceleration. Safety score 87/100. Highest day was Tuesday — 98 km, mostly highway.

> **You:** I'm handing the car to a valet. Set safe limits.
> **Claude:** Setting valet alert: speed 60 km/h, idle 5 min. Confirm? *(confirms, sets)*

> **You:** Where did I park at the airport?
> **Claude:** Last GPS: 28.5562°N, 77.1000°E (Indira Gandhi Intl Airport, T3 Parking). [Open in Maps]. Want me to flash the hazards when you're close?

> **You:** Why is fuel dropping so fast this month?
> **Claude:** *(calls `get_driving_analysis` for 5 recent days)* Idle ratio is 22% (typical: 8–10%) and avg max speed is 118 km/h. Both push fuel use up ~20%. Suggestions: turn off engine at stops > 60s, hold 80–90 km/h on the highway.

---

## Safety, rate limits, gotchas

- **Confirmations are hardcoded.** Every write tool returns `{status: "confirmation_required"}` first; you have to call again with `confirm=True`. The LLM can see the full effect before doing anything.
- **Cloud API only.** No OBD-II, no CAN bus poking — only what the Kia Connect / Bluelink cloud exposes. Safe.
- **Rate limit.** Kia/Hyundai's API enforces ~100 calls per window. The PWA caches reads for 2 min to stay polite.
- **Cached vs live.** Most read tools return what the car last uploaded (usually within minutes). Use `get_live_status` / `force_refresh` only when you genuinely need fresh data — they wake the TCU and drain the 12V slightly. Both are rate-limited to once per 30 min.
- **PIN.** Lock/unlock and a few other writes need `KIA_PIN` set. Read-only tools do not.
- **Tested on.** Kia Carens Clavis (India). Should work on any Kia/Hyundai/Genesis vehicle that the upstream library supports — please open an issue or PR with results from your model.

## Credits

Built on the excellent [`hyundai-kia-connect-api`](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api). All thanks to that project's maintainers — this repo is just the MCP / CLI / PWA layer on top.

## License

MIT — see [LICENSE](./LICENSE).
