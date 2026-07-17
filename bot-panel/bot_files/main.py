"""
Bot de Discord — Punto de entrada principal.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Carga automática de cogs desde cogs/*.py
• Slash commands + prefix commands (híbrido)
• Sesión aiohttp compartida (bot.session)
• Wavelink / Lavalink (opcional)
• Configuración leída del panel (os.environ)
"""

import os
import sys
import asyncio
import logging
import aiohttp
import discord
from discord.ext import commands

# ── Logging ──────────────────────────────────────────
log = logging.getLogger("bot")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ── Configuración desde el panel ─────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
BOT_PREFIX = os.environ.get("BOT_PREFIX", "!")

# Intents (controlados desde Ajustes → Comportamiento)
intents = discord.Intents.default()
intents.message_content = os.environ.get("INTENT_MESSAGE_CONTENT", "true").lower() == "true"
intents.members          = os.environ.get("INTENT_MEMBERS",         "false").lower() == "true"

# Presencia / actividad (controlada desde Ajustes → Presencia)
_STATUS_MAP = {
    "online":    discord.Status.online,
    "idle":      discord.Status.idle,
    "dnd":       discord.Status.dnd,
    "invisible": discord.Status.invisible,
}
_ACTIVITY_MAP = {
    "playing":   discord.ActivityType.playing,
    "streaming": discord.ActivityType.streaming,
    "listening": discord.ActivityType.listening,
    "watching":  discord.ActivityType.watching,
    "competing": discord.ActivityType.competing,
}

STATUS_TYPE   = os.environ.get("STATUS_TYPE",    "online")
ACTIVITY_TYPE = os.environ.get("ACTIVITY_TYPE",  "playing")
ACTIVITY_TEXT = os.environ.get("ACTIVITY_TEXT",  "")

# Lavalink / Wavelink (opcional)
LAVALINK_HOST = os.environ.get("LAVALINK_HOST",     "")
LAVALINK_PORT = int(os.environ.get("LAVALINK_PORT", "2333"))
LAVALINK_PASS = os.environ.get("LAVALINK_PASSWORD", "youshallnotpass")


# ── Bot ───────────────────────────────────────────────
class MyBot(commands.Bot):
    """Bot principal con sesión aiohttp y soporte wavelink."""

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(BOT_PREFIX),
            intents=intents,
            help_command=None,          # puedes poner tu propio comando help en un cog
            case_insensitive=True,
        )
        self.session: aiohttp.ClientSession | None = None

    # ── Setup (antes de conectar) ─────────────────────
    async def setup_hook(self):
        # Sesión HTTP compartida para todos los cogs
        self.session = aiohttp.ClientSession()

        # Cargar cogs
        await self._load_cogs()

        # Nota: Lavalink lo gestiona el cog cogs/lavalink.py
        # No conectar aquí para evitar conflicto con el cog.

        # Sincronizar slash commands globalmente
        await self.tree.sync()
        log.info("Slash commands sincronizados globalmente.")

    async def _load_cogs(self):
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        if not os.path.isdir(cogs_dir):
            os.makedirs(cogs_dir)
            log.info("Carpeta cogs/ creada. Añade tus archivos .py ahí.")
            return

        loaded, failed = 0, 0
        for fname in sorted(os.listdir(cogs_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            ext = f"cogs.{fname[:-3]}"
            try:
                await self.load_extension(ext)
                log.info(f"  ✓ Cog cargado: {ext}")
                loaded += 1
            except Exception as e:
                log.error(f"  ✗ Error cargando {ext}: {e}")
                failed += 1

        log.info(f"Cogs: {loaded} cargados, {failed} con error.")

    # ── Eventos ───────────────────────────────────────
    async def on_ready(self):
        log.info(f"Conectado como {self.user} (ID: {self.user.id})")
        log.info(f"Servidores: {len(self.guilds)}")

        # Aplicar presencia desde configuración del panel
        status   = _STATUS_MAP.get(STATUS_TYPE, discord.Status.online)
        act_type = _ACTIVITY_MAP.get(ACTIVITY_TYPE, discord.ActivityType.playing)
        activity = discord.Activity(type=act_type, name=ACTIVITY_TEXT) if ACTIVITY_TEXT else None
        await self.change_presence(status=status, activity=activity)

        # Enviar info del bot al panel (bot_manager parsea esta línea)
        import json as _json
        total_users = sum(g.member_count or 0 for g in self.guilds)
        _info = {
            "name":       str(self.user),
            "bot_id":     str(self.user.id),
            "avatar_url": str(self.user.display_avatar.url),
            "guilds":     len(self.guilds),
            "users":      total_users,
            "ping":       round(self.latency * 1000),
        }
        print(f"BOT_INFO:{_json.dumps(_info)}", flush=True)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ No tienes permisos para esto.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Falta argumento: `{error.param.name}`")
            return
        log.error(f"Error en comando '{ctx.command}': {error}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()


# ── Comandos built-in básicos ─────────────────────────
# (puedes moverlos a un cog en cogs/general.py)
bot = MyBot()


@bot.hybrid_command(name="ping", description="Muestra la latencia del bot.")
async def ping(ctx: commands.Context):
    ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{ms}ms`", ephemeral=isinstance(ctx.interaction, discord.Interaction))


@bot.hybrid_command(name="info", description="Información del bot.")
async def info(ctx: commands.Context):
    embed = discord.Embed(title="ℹ️ Información del Bot", color=discord.Color.blurple())
    embed.add_field(name="Prefijo",    value=BOT_PREFIX,                inline=True)
    embed.add_field(name="Servidores", value=len(bot.guilds),           inline=True)
    embed.add_field(name="Latencia",   value=f"{round(bot.latency*1000)}ms", inline=True)
    embed.set_footer(text=str(bot.user), icon_url=bot.user.display_avatar.url if bot.user else None)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="reload", description="Recarga un cog (solo administradores).")
@commands.is_owner()
async def reload_cog(ctx: commands.Context, cog: str):
    """Recarga un cog sin reiniciar el bot. Uso: !reload general"""
    ext = f"cogs.{cog}"
    try:
        await bot.reload_extension(ext)
        await ctx.send(f"✅ `{ext}` recargado.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`", ephemeral=True)


# ── Inicio ────────────────────────────────────────────
if __name__ == "__main__":
    if not BOT_TOKEN:
        log.error("BOT_TOKEN no configurado. Añádelo en el panel → Variables.")
        sys.exit(1)

    bot.run(BOT_TOKEN, log_handler=None)
