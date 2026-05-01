# Kia Connect MCP

Control and monitor your Kia (or Hyundai / Genesis) from Claude, Claude Code, or any MCP-compatible client. Includes a CLI and an optional iPhone-friendly PWA dashboard.

> Wraps [`hyundai-kia-connect-api`](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api). Works in every region that library supports — Europe, USA, Canada, India, South Korea, Australia, China — across Kia, Hyundai, and Genesis brands.

## What you get

- **MCP server** — 50+ tools for Claude / Claude Code: status, location, lock/unlock, AC, trips, driving score, fuel cost, geofence/speed alerts, panic alarm, send-to-nav, and more.
- **CLI** — `kia-connect <command>` for scripting and shell integration.
- **PWA dashboard** *(optional)* — a mobile-friendly FastAPI + Tailwind web UI with server-side caching and SQLite trip history.

All write/control commands require `confirm=True` so the LLM can't accidentally unlock your car or honk the horn.

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
| `KIA_TANK_LITERS` | no | `45` | Used by fuel cost / mileage estimates |
| `KIA_FUEL_PRICE`  | no | `105` | Local fuel price per liter (any currency) |

## Use it

### As an MCP server (Claude Code)

```bash
claude mcp add kia-connect -- uv --directory /absolute/path/to/kia-connect-mcp run kia-mcp
```

Then in Claude Code: *"Is my car locked?"*, *"Start the AC at 22°C for 10 minutes"*, *"Where is my car?"*, *"Show today's trips"*, *"What's my driving score this week?"*.

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
./kia locked         # lock state
./kia location       # GPS + Maps link
./kia trips          # today's trips
./kia driving-score  # day's driving analysis
./kia fuel-cost      # estimated fuel cost for today
./kia lock           # lock the doors
./kia ac-on 22 10    # AC at 22°C for 10 min
./kia help           # full command list
```

The `./kia` wrapper script auto-loads `.env` and runs through `uv`.

### As a PWA dashboard (optional)

The web dashboard pulls in FastAPI + Jinja, which are an optional extra:

```bash
uv sync --extra web
uv run --python 3.13 uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Open `http://<your-machine>:8000` on your phone and "Add to Home Screen". Server-side caches read endpoints for 2 minutes and persists trip data in `trips.db`.

## Tool reference

50+ tools across read-only, computed insights, and control:

**Status** — `get_full_status`, `is_car_locked`, `get_windows`, `get_fuel`, `get_tires`, `get_climate_status`, `get_lights`, `get_warnings`, `get_location`, `get_car_health`, `get_battery`, `get_odometer`, `get_vehicle_info`, `get_vehicle_profile`

**Trips & driving** — `get_trip_today`, `get_trip_month`, `get_trip_route`, `get_trip_details`, `get_driving_analysis`, `get_driving_summary`, `get_road_trip`, `get_departure_patterns`, `get_frequent_locations`

**Maintenance** — `get_maintenance_schedule`, `get_next_service`, `update_maintenance_interval`

**Computed insights** — `get_fuel_cost`

**Control (all require `confirm=True`)** — `lock_car`, `unlock_car`, `start_climate`, `stop_climate`, `start_ac_only`, `stop_ac_only`, `flash_lights`, `honk_horn`, `open_trunk`, `close_trunk`, `control_windows`, `valet_mode`, `start_panic_alarm`, `stop_panic_alarm`, `rename_vehicle`, `send_destination`

**Alerts** — `set_speed_alert`, `set_idle_alert`, `set_valet_alert`, `set_curfew_alert`, `set_geofence_alert`, `get_alert_settings`

**System** — `force_refresh`, `get_live_status`, `get_rate_limit`

## Notes

- **Rate limits.** Kia/Hyundai's API has a window-based rate limit (~100 calls). The PWA caches reads for 2 min to stay polite. `force_refresh` is rate-limited to once per 30 minutes to protect the 12V battery.
- **Cached vs live.** Most read tools return cached state from the car's last upload. Use `get_live_status` or `force_refresh` only when you need fresh data — these wake the TCU and drain the 12V battery slightly.
- **Confirmations.** Every write tool requires `confirm=True`. This is a hard guard so an LLM can't unlock your car or honk the horn without you asking it to twice.
- **Tested on.** Kia Carens Clavis (India). Should work on any Kia/Hyundai/Genesis vehicle the upstream library supports — please open an issue or PR with results from your model.

## Credits

Built on the excellent [`hyundai-kia-connect-api`](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api). All thanks to that project's maintainers — this repo is just an MCP wrapper around it.

## License

MIT — see [LICENSE](./LICENSE).
