"""
Bot de Discord principal.
Usa discord.py con soporte para Wavelink (música) y aiohttp.
Este archivo es ejecutado por el bot_manager como subprocess.
"""
import asyncio
import logging
import os
import signal
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bot")

# ─── Configuración ───────────────────────────────────────────────
TOKEN = os.environ.get("BOT_TOKEN", "")
PREFIX = os.environ.get("BOT_PREFIX", "!")

# Lavalink
LAVALINK_HOST = os.environ.get("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.environ.get("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.environ.get("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_SSL = os.environ.get("LAVALINK_SSL", "false").lower() == "true"

# ─── Intents ─────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


class BotClient(commands.Bot):
    """Bot principal con sesión aiohttp global y soporte Wavelink."""

    session: aiohttp.ClientSession

    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)

    async def setup_hook(self):
        """Se ejecuta antes de conectar al gateway de Discord."""
        # Sesión aiohttp reutilizable (un solo objeto para toda la vida del bot)
        self.session = aiohttp.ClientSession()
        logger.info("Sesión aiohttp inicializada.")

        # Intentar configurar Wavelink / Lavalink
        await self._setup_wavelink()

        # Cargar extensiones/cogs
        await self._load_cogs()

    async def _setup_wavelink(self):
        """Configura el nodo Lavalink con reconexión automática."""
        try:
            import wavelink
            node = wavelink.Node(
                uri=f"{'https' if LAVALINK_SSL else 'http'}://{LAVALINK_HOST}:{LAVALINK_PORT}",
                password=LAVALINK_PASSWORD,
            )
            await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)
            logger.info(f"Wavelink conectado a {LAVALINK_HOST}:{LAVALINK_PORT}")
        except Exception as e:
            logger.warning(f"Wavelink no disponible (configura Lavalink): {e}")

    async def _load_cogs(self):
        """Carga los cogs/extensiones del bot."""
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        if os.path.isdir(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    ext = f"cogs.{filename[:-3]}"
                    try:
                        await self.load_extension(ext)
                        logger.info(f"Cog cargado: {ext}")
                    except Exception as e:
                        logger.error(f"Error cargando {ext}: {e}")

    async def on_ready(self):
        logger.info(f"Bot conectado como {self.user} (ID: {self.user.id})")
        logger.info(f"Servidores: {len(self.guilds)} | Usuarios: {sum(g.member_count for g in self.guilds)}")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="el panel web")
        )

    async def close(self):
        """Cierra la sesión aiohttp al apagar el bot."""
        if hasattr(self, "session") and not self.session.closed:
            await self.session.close()
            logger.info("Sesión aiohttp cerrada.")
        await super().close()

    # ─── Comandos básicos ─────────────────────────────────────────

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ No tienes permisos para usar este comando.")
            return
        logger.error(f"Error en comando {ctx.command}: {error}")
        await ctx.send(f"❌ Error: {error}")


bot = BotClient()


# ─── Comandos de ejemplo ──────────────────────────────────────────

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """Muestra el ping del bot."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")


@bot.command(name="info")
async def info(ctx: commands.Context):
    """Información del bot."""
    embed = discord.Embed(title="ℹ️ Información del Bot", color=discord.Color.blue())
    embed.add_field(name="Nombre", value=str(bot.user), inline=True)
    embed.add_field(name="ID", value=str(bot.user.id), inline=True)
    embed.add_field(name="Servidores", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="fetch")
async def http_fetch(ctx: commands.Context, url: str):
    """Hace una petición GET a una URL (ejemplo de aiohttp)."""
    try:
        async with bot.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            await ctx.send(f"✅ Status: `{resp.status}` — `{url}`")
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")


# ─── Señal de parada elegante ────────────────────────────────────

def _handle_sigterm(*_):
    asyncio.create_task(bot.close())


signal.signal(signal.SIGTERM, _handle_sigterm)


# ─── Entrada principal ───────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        logger.error("BOT_TOKEN no configurado. Edita la configuración en el panel.")
        exit(1)
    try:
        bot.run(TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("Token de Discord inválido.")
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario.")
