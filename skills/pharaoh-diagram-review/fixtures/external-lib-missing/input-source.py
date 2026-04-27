"""Source cited by the diagram's :source_doc: option."""

import requests


def fetch_report(city):
    response = requests.get(f"https://api.example.com/weather/{city}")
    response.raise_for_status()
    return response.json()
