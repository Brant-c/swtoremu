Run Run-LocalClient.bat from the repository root after asset preparation finishes.
It launches the extracted client with its original arguments and saves logs under Diagnostics/Captures.
The client now reads AssetsConverted on D:. AssetOriginals preserves the copied retail archives.
Conversion is experimental. Archive version and per-entry metadata/checksum fields were preserved, not proven compatible with the old client. Modern game data may still be incompatible even after decompression succeeds.
To restore the prior asset path, copy Diagnostics/client_defaults.before-converted.ini over nexusclient/nexusclient/client_defaults.ini.
The retail installation was not modified. This setup does not implement the missing server-discovery service or complete the emulator.
