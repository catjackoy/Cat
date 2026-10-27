# CAT HUB PROMETHEUS

A Python Discord bot for conservative, static Lua/Luau source analysis and cleanup. Black-and-gold embeds are used for bot responses.

## Commands
- `/deobfuscate file:<upload>` — safe static cleanup passes; not a universal deobfuscator.
- `/analyze file:<upload>` — identifies common obfuscation indicators.
- `/beautify file:<upload>` — conservative whitespace normalization.
- `/decode file:<upload>` — decodes selected escape sequences in quoted strings.
- `/help` — command list.
- `/ping` — latency check.

## Deploy on Railway
1. Create a Discord application and bot in the Discord Developer Portal.
2. Invite the bot to your server with `bot` and `applications.commands` scopes. Grant `Send Messages`, `Embed Links`, `Attach Files`, and `Read Message History` permissions.
3. Push this folder to a GitHub repository, or upload the project through your preferred supported Railway deployment flow.
4. Create a Railway project from the repository.
5. In Railway Variables, add `DISCORD_TOKEN` with your bot token. Optionally set `MAX_FILE_BYTES` (default 700000).
6. Deploy. The start command is `python main.py`.

Do not put your token in source code or commit `.env`. If exposed, reset it in the Discord Developer Portal.

## Important limitations
This project does not execute uploaded Lua. Its current processing is conservative text cleanup and heuristic analysis; it does not yet include the external repositories supplied by the user. Each external engine must be reviewed for dependencies, license, compatibility, and safe invocation before integration. Obfuscation is not guaranteed to be reversible, especially for virtualized or encrypted scripts.
