.. mermaid::
   :caption: FEAT_weather_fetch — fetch weather report
   :source_doc: input-source.py

   sequenceDiagram
       participant CLI
       participant WeatherService

       CLI->>WeatherService: fetch_report(city)
       WeatherService-->>CLI: report
