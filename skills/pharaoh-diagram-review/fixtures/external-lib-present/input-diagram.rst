.. mermaid::
   :caption: FEAT_weather_fetch — fetch weather report
   :source_doc: input-source.py

   sequenceDiagram
       participant CLI
       participant WeatherService
       participant requests as Requests

       CLI->>WeatherService: fetch_report(city)
       WeatherService->>requests: GET /weather/{city}
       requests-->>WeatherService: response
       WeatherService-->>CLI: report
