#!/usr/bin/env python3

import sys
from http import HTTPStatus

import requests
import yaml
from _common import load_config


def pretty(code: int, resp: dict | None):
    print("-" * 50)
    status = HTTPStatus(code)
    print(f"Status: {code} {status.phrase}")
    if resp is None:
        print("None")
        print("-" * 50)
        return

    print(yaml.dump(resp, allow_unicode=True, default_flow_style=False, sort_keys=False))
    print("-" * 50)


def send_request(method: str, headers: dict[str, str], url: str):
    status = 0
    data: dict | None = None
    try:
        if method.lower() == "post":
            response = requests.post(url, headers=headers, timeout=30)
        elif method.lower() == "get":
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.delete(url, headers=headers, timeout=30)
        status = response.status_code
        data = response.json()
    except requests.JSONDecodeError:
        pass  # request didn't have a json body, which is fine since we return None by default
    except requests.exceptions.HTTPError as e:
        print(f"-> HTTP ERROR for {method} {url}: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"-> ERROR for {method} {url}: {e}")

    pretty(status, data)


def get_choice():
    options = {
        "a": "Get all Keys for a Channel",
        "b": "Create new key for Channel",
        "c": "Delete all keys for a Channel",
        "d": "Get all keys",
        "e": "Verify a key",
        "q": "Quit",
    }

    print("Admin options:")
    for k, v in options.items():
        print(f"{k}:  {v}")

    choice = ""
    while choice not in options:
        choice = input("choice: ").strip().lower()

    return choice


def main():
    config = load_config()
    api_key = config["api_key"]
    server_url = config["server_url"]

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    choice = ""
    while choice != "q":
        choice = get_choice()

        match choice:
            case "a":
                channel = input("Channel name: ")
                url = f"{server_url}/membership/{channel}"
                send_request("get", headers, url)
            case "b":
                channel = input("Channel name: ")
                url = f"{server_url}/membership/{channel}"
                send_request("post", headers, url)
            case "c":
                channel = input("Channel name: ")
                url = f"{server_url}/membership/{channel}"
                send_request("delete", headers, url)
            case "d":
                url = f"{server_url}/membership"
                send_request("get", headers, url)
            case "e":
                key = input("key: ")
                url = f"{server_url}/membership/verify"
                new_headers = {
                    "X-Membership-Key": key,
                    "Content-Type": "application/json",
                }
                send_request("get", new_headers, url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
