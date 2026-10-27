import os
import io
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from lua_engine import analyze_lua, beautify_lua, decode_strings, deobfuscate_lua

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", str(700_000)))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def make_embed(title: str, description: str = "", color: int = 0xD4AF37):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="CAT HUB PROMETHEUS • Lua Analysis")
    return embed


async def read_upload(attachment: discord.Attachment) -> str:
    if attachment.size > MAX_FILE_BYTES:
        raise ValueError(f"File is too large. Maximum size is {MAX_FILE_BYTES:,} bytes.")
    data = await attachment.read()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("This file is not valid UTF-8 text. Upload a .lua or .txt source file.") from exc


async def send_text_file(interaction: discord.Interaction, filename: str, content: str, message: str):
    payload = content.encode("utf-8")
    if len(payload) > MAX_FILE_BYTES:
        await interaction.followup.send(
            embed=make_embed("Output too large", "The generated output exceeds the configured file limit."),
            ephemeral=True
        )
        return
    file = discord.File(io.BytesIO(payload), filename=filename)
    await interaction.followup.send(content=message, file=file)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}; synced {len(synced)} global slash commands.")
    except Exception as exc:
        print(f"Slash command sync failed: {exc}")
    print("CAT HUB PROMETHEUS is online.")


@bot.tree.command(name="ping", description="Check whether CAT HUB PROMETHEUS is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_embed("CAT HUB PROMETHEUS", f"Pong! `{round(bot.latency * 1000)} ms`"),
        ephemeral=True
    )


@bot.tree.command(name="help", description="Show CAT HUB PROMETHEUS commands.")
async def help_command(interaction: discord.Interaction):
    embed = make_embed("CAT HUB PROMETHEUS • Help")
    embed.add_field(name="/deobfuscate", value="Apply safe, static Lua cleanup and supported local transformations.", inline=False)
    embed.add_field(name="/analyze", value="Inspect a Lua file for common obfuscation indicators without executing it.", inline=False)
    embed.add_field(name="/beautify", value="Normalize indentation and whitespace conservatively.", inline=False)
    embed.add_field(name="/decode", value="Decode common quoted-string escapes where safe.", inline=False)
    embed.add_field(name="/ping", value="Check bot latency.", inline=False)
    embed.add_field(name="Safety", value="Uploaded Lua is treated as text. The bot never executes uploaded scripts.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="analyze", description="Analyze a Lua file without executing it.")
@app_commands.describe(file="Upload a .lua or .txt file")
async def analyze(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(thinking=True)
    try:
        source = await read_upload(file)
        report = analyze_lua(source)
        embed = make_embed("Lua Analysis", f"**File:** `{file.filename}`\n**Lines:** {report['lines']}\n**Characters:** {report['characters']}")
        embed.add_field(name="Indicators", value="\n".join(f"• {item}" for item in report["indicators"]) or "No common indicators detected.", inline=False)
        embed.add_field(name="Notes", value="Static heuristics can produce false positives and cannot guarantee that a file is safe.", inline=False)
        await interaction.followup.send(embed=embed)
    except ValueError as exc:
        await interaction.followup.send(embed=make_embed("Could not analyze file", str(exc)), ephemeral=True)


@bot.tree.command(name="beautify", description="Conservatively format a Lua source file.")
@app_commands.describe(file="Upload a .lua or .txt file")
async def beautify(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(thinking=True)
    try:
        source = await read_upload(file)
        output = beautify_lua(source)
        name = os.path.splitext(file.filename)[0] + ".beautified.lua"
        await send_text_file(interaction, name, output, "Formatting complete. This is conservative formatting, not a full Lua parser.")
    except ValueError as exc:
        await interaction.followup.send(embed=make_embed("Could not format file", str(exc)), ephemeral=True)


@bot.tree.command(name="decode", description="Decode common escaped sequences inside Lua quoted strings.")
@app_commands.describe(file="Upload a .lua or .txt file")
async def decode(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(thinking=True)
    try:
        source = await read_upload(file)
        output = decode_strings(source)
        name = os.path.splitext(file.filename)[0] + ".decoded.lua"
        await send_text_file(interaction, name, output, "String escape pass finished. Unsupported or ambiguous constructs are left unchanged.")
    except ValueError as exc:
        await interaction.followup.send(embed=make_embed("Could not decode file", str(exc)), ephemeral=True)


@bot.tree.command(name="deobfuscate", description="Run the available static Lua cleanup passes.")
@app_commands.describe(file="Upload a .lua or .txt file")
async def deobfuscate(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(thinking=True)
    try:
        source = await read_upload(file)
        output, notes = deobfuscate_lua(source)
        name = os.path.splitext(file.filename)[0] + ".deobfuscated.lua"
        await send_text_file(interaction, name, output, "Static cleanup completed. No uploaded code was executed.")
        if notes:
            await interaction.followup.send(embed=make_embed("Pass report", "\n".join(f"• {n}" for n in notes)))
    except ValueError as exc:
        await interaction.followup.send(embed=make_embed("Could not process file", str(exc)), ephemeral=True)


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it in your host's environment variables.")

bot.run(TOKEN)
