"""
Bot de Discord — Punto de entrada principal.
Coloca aquí tu código o importa tus cogs/módulos.
"""
import os
import discord
from discord.ext import commands

# ── Configuración ────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
BOT_PREFIX = os.environ.get("BOT_PREFIX", "!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# ── Eventos ──────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[Bot] Conectado como {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Error: {error}")

# ── Comandos básicos ─────────────────────────────────
@bot.command(name="ping")
async def ping(ctx):
    """Responde con la latencia del bot."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@bot.command(name="info")
async def info(ctx):
    """Información del bot."""
    embed = discord.Embed(
        title="ℹ️ Información del Bot",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Prefijo", value=BOT_PREFIX, inline=True)
    embed.add_field(name="Servidores", value=len(bot.guilds), inline=True)
    embed.add_field(name="Latencia", value=f"{round(bot.latency*1000)}ms", inline=True)
    await ctx.send(embed=embed)

# ── Cargar cogs automáticamente ──────────────────────
import os as _os
cogs_dir = _os.path.join(_os.path.dirname(__file__), "cogs")
if _os.path.isdir(cogs_dir):
    import asyncio
    async def load_cogs():
        for fname in _os.listdir(cogs_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                cog = f"cogs.{fname[:-3]}"
                try:
                    await bot.load_extension(cog)
                    print(f"[Cog] Cargado: {cog}")
                except Exception as e:
                    print(f"[Cog] Error cargando {cog}: {e}")

# ── Inicio ────────────────────────────────────────────
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("[Error] BOT_TOKEN no configurado. Añádelo en el panel → Ajustes.")
        exit(1)

    import asyncio
    async def main():
        async with bot:
            await load_cogs()
            await bot.start(BOT_TOKEN)

    asyncio.run(main())
