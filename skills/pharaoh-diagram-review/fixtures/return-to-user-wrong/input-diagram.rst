.. mermaid::
   :caption: FEAT_settings_update — update user setting from CLI
   :source_doc: input-source.py

   sequenceDiagram
       participant CLI
       participant SettingsService
       participant Store
       participant User

       CLI->>SettingsService: update_setting(key, value)
       SettingsService->>Store: write(key, value)
       Store-->>SettingsService: ok
       SettingsService-->>User: updated
