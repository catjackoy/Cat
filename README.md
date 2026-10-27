# External engine integration area

The repositories supplied for possible integration are candidates only; none are bundled or claimed to work yet. Review each project's license, dependencies, command-line interface, supported obfuscator versions, and safety properties before adapting it.

Suggested integration interface:
`process(source: str) -> tuple[str, list[str]]`

Never run untrusted uploaded Lua. If an external tool needs to execute the uploaded program rather than statically parse it, do not run it on the bot host.
