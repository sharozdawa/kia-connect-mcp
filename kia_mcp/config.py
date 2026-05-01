import os
import sys


def get_config() -> dict:
    username = os.environ.get("KIA_USERNAME")
    password = os.environ.get("KIA_PASSWORD")
    pin = os.environ.get("KIA_PIN", "")
    region = int(os.environ.get("KIA_REGION", "6"))
    brand = int(os.environ.get("KIA_BRAND", "1"))
    tank_liters = float(os.environ.get("KIA_TANK_LITERS", "45"))
    fuel_price = float(os.environ.get("KIA_FUEL_PRICE", "105"))

    if not username or not password:
        print("Error: KIA_USERNAME and KIA_PASSWORD environment variables required", file=sys.stderr)
        sys.exit(1)

    return {
        "username": username,
        "password": password,
        "pin": pin,
        "region": region,
        "brand": brand,
        "tank_liters": tank_liters,
        "fuel_price": fuel_price,
    }
