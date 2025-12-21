#!/usr/bin/env python3

from http import HTTPStatus
import os
import requests
import sys
import yaml

CONFIG_FILE = "config.yaml"

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


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            
        if not config or 'api_key' not in config:
            print(f"Error: 'api_key' not found in '{CONFIG_FILE}'.")
            print("Please ensure the file has the line: api_key: YOUR_KEY")
            sys.exit(1)

        if not config or 'server_url' not in config:
            print(f"Error: 'server_url' not found in '{CONFIG_FILE}'.")
            print("Please ensure the file has the line: server_url: YOUR_SERVER")
            sys.exit(1)
            
        api_key = config['api_key']
        server_url = config['server_url']
            
        return api_key, server_url
        
    except yaml.YAMLError as e:
        print(f"Error parsing '{CONFIG_FILE}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{CONFIG_FILE}': {e}")
        sys.exit(1)

def send_request(method: str, headers: dict[str,str], url: str):
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
        pass # request didn't have a json body, which is fine since we return None by default
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
        "q": "Quit"
    }

    print("Admin options:")
    for k, v in options.items():
        print(f"{k}:  {v}")

    choice = ""
    while choice not in options:
        choice = input("choice: ").strip().lower()

    return choice


def main():
    api_key, server_url = load_config()

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

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
                    "Content-Type": "application/json"
                }
                send_request("get", new_headers, url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
