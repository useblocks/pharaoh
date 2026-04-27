.. mermaid::
   :caption: FEAT_settings_update — update user setting from interactive shell
   :source_doc: input-source.py

   sequenceDiagram
       actor User
       participant CLI
       participant SettingsService
       participant Store

       User->>CLI: type "set key value"
       CLI->>SettingsService: update_setting(key, value)
       SettingsService->>Store: write(key, value)
       Store-->>SettingsService: ok
       SettingsService-->>CLI: updated
       CLI-->>User: OK
