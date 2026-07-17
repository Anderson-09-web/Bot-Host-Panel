"""
Cog Lavalink — conexión a wavelink vía tu API de nodos.
Obtiene la config de: https://discord-music-link.onrender.com/api/node/config
"""
import asyncio
import aiohttp
import discord
import wavelink
from discord.ext import commands, tasks

API_BASE_URL = "https://discord-music-link.onrender.com"
_RETRY_DELAY  = 30   # segundos entre reintentos
_MAX_RETRIES  = 5    # intentos máximos al arrancar


class LavalinkCog(commands.Cog, name="Lavalink"):

    def __init__(self, bot: commands.Bot):
        self.bot    = bot
        self._ready = asyncio.Event()

    # ── Ciclo de vida del cog ─────────────────────────────
    async def cog_load(self):
        """Lanzar conexión en background cuando el cog se carga."""
        asyncio.create_task(self._connect_when_ready(), name="lavalink-connect")

    async def cog_unload(self):
        """Cerrar nodos al descargar el cog."""
        try:
            for node in list(wavelink.Pool.nodes.values()):
                await node.close()
            print("[Lavalink] Nodos cerrados.")
        except Exception:
            pass

    # ── Esperar a que el bot esté listo y conectar ────────
    async def _connect_when_ready(self):
        await self.bot.wait_until_ready()

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                await self._connect()
                return
            except Exception as e:
                print(f"[Lavalink] ❌ Intento {attempt}/{_MAX_RETRIES} fallido: {e}")
                if attempt < _MAX_RETRIES:
                    print(f"[Lavalink] Reintentando en {_RETRY_DELAY}s...")
                    await asyncio.sleep(_RETRY_DELAY)

        print("[Lavalink] ❌ No se pudo conectar tras todos los intentos. "
              "Comprueba que tu servidor Lavalink esté activo.")

    async def _connect(self):
        """Pedir config a la API y conectar wavelink."""
        # Si ya hay nodos conectados, no reconectar
        if wavelink.Pool.nodes:
            print("[Lavalink] ✅ Ya conectado (nodos existentes).")
            return

        print(f"[Lavalink] Obteniendo config de {API_BASE_URL} ...")

        async with aiohttp.ClientSession() as session:
            # La API de Render puede tardar hasta 30s en despertar
            async with session.get(
                f"{API_BASE_URL}/api/node/config",
                timeout=aiohttp.ClientTimeout(total=45),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"API respondió {resp.status}: {body[:200]}"
                    )
                cfg = await resp.json()

        scheme = "https" if cfg.get("secure") else "http"
        uri    = f"{scheme}://{cfg['host']}:{cfg['port']}"

        node = wavelink.Node(uri=uri, password=cfg["password"])
        await wavelink.Pool.connect(nodes=[node], client=self.bot, cache_capacity=100)

        self.bot.lavalink_connected = True
        print(f"[Lavalink] ✅ Conectado al nodo  →  {uri}")
        print(f"[Lavalink] 🎵 Fuentes: {', '.join(cfg.get('sources', []))}")

    # ── Reconectar manualmente (desde !reconnect_lavalink) ─
    async def reconnect(self):
        """Cierra nodos existentes y reconecta."""
        for node in list(wavelink.Pool.nodes.values()):
            await node.close()
        # Limpiar caché interna de wavelink
        wavelink.Pool.nodes.clear()
        self.bot.lavalink_connected = False
        await self._connect()

    # ── Comandos de administración ────────────────────────
    @commands.command(name="lava_status", hidden=True)
    @commands.is_owner()
    async def lava_status(self, ctx: commands.Context):
        """Muestra el estado de los nodos Lavalink."""
        nodes = wavelink.Pool.nodes
        if not nodes:
            await ctx.send("⚠️ Sin nodos Lavalink conectados.")
            return
        lines = []
        for name, node in nodes.items():
            lines.append(f"`{name}` — {node.uri}")
        await ctx.send("**Nodos Lavalink:**\n" + "\n".join(lines))

    @commands.command(name="lava_reconnect", hidden=True)
    @commands.is_owner()
    async def lava_reconnect(self, ctx: commands.Context):
        """Reconecta wavelink al nodo Lavalink."""
        msg = await ctx.send("🔄 Reconectando...")
        try:
            await self.reconnect()
            await msg.edit(content="✅ Reconectado correctamente.")
        except Exception as e:
            await msg.edit(content=f"❌ Error: `{e}`")

    # ── Eventos wavelink ──────────────────────────────────
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"[Lavalink] Nodo listo: {payload.node.uri}  "
              f"(resumed={payload.resumed}, session={payload.session_id})")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        # Sobreescribe en tu cog de música si necesitas hacer algo al iniciar pista
        pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        # Sobreescribe en tu cog de música si necesitas manejar el fin de pista
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(LavalinkCog(bot))
