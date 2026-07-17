"""
Cog de Música — comandos de reproducción vía Wavelink v3 + Lavalink.
Fuente: SoundCloud (el nodo de discord-music-link solo soporta SC por ahora).
"""
import asyncio
import discord
import wavelink
from discord.ext import commands


class MusicCog(commands.Cog, name="Música"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Helpers ───────────────────────────────────────────
    def _player(self, ctx: commands.Context) -> wavelink.Player | None:
        return ctx.voice_client  # type: ignore

    async def _ensure_voice(self, ctx: commands.Context) -> wavelink.Player | None:
        """Conecta el bot al canal del usuario si hace falta, o devuelve el player existente."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Primero únete a un canal de voz.")
            return None

        player = self._player(ctx)
        if player is None:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.disabled
            except Exception as e:
                await ctx.send(f"❌ No pude conectarme al canal: `{e}`")
                return None

        if player.channel != ctx.author.voice.channel:
            await ctx.send("❌ Ya estoy en otro canal de voz.")
            return None

        return player

    # ── !play ─────────────────────────────────────────────
    @commands.hybrid_command(name="play", aliases=["p"], description="Reproduce o encola una canción de SoundCloud.")
    async def play(self, ctx: commands.Context, *, query: str):
        """Busca en SoundCloud y reproduce. Uso: !play <nombre o URL>"""
        player = await self._ensure_voice(ctx)
        if player is None:
            return

        await ctx.defer()

        # Buscar en SoundCloud
        try:
            results = await wavelink.Playable.search(query, source=wavelink.TrackSource.SoundCloud)
        except Exception as e:
            await ctx.send(f"❌ Error buscando: `{e}`")
            return

        if not results:
            await ctx.send("❌ No encontré resultados en SoundCloud.")
            return

        # Si es playlist, encolar todo
        if isinstance(results, wavelink.Playlist):
            tracks = results.tracks
            for t in tracks:
                t.extras = {"requester": ctx.author.display_name}
            await player.queue.put_wait(tracks)
            await ctx.send(
                f"📋 Playlist **{results.name}** añadida — `{len(tracks)}` canciones."
            )
        else:
            track = results[0]
            track.extras = {"requester": ctx.author.display_name}
            if player.playing:
                await player.queue.put_wait(track)
                await ctx.send(f"🎵 Encolado: **{track.title}** — `{track.author}`")
            else:
                await player.play(track)
                await ctx.send(
                    f"▶️ Reproduciendo: **{track.title}** — `{track.author}`"
                )

    # ── !pause ────────────────────────────────────────────
    @commands.hybrid_command(name="pause", description="Pausa la reproducción.")
    async def pause(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player or not player.playing:
            await ctx.send("❌ No hay nada reproduciéndose.")
            return
        await player.pause(True)
        await ctx.send("⏸️ Pausado.")

    # ── !resume ───────────────────────────────────────────
    @commands.hybrid_command(name="resume", aliases=["r"], description="Reanuda la reproducción.")
    async def resume(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player or not player.paused:
            await ctx.send("❌ No está pausado.")
            return
        await player.pause(False)
        await ctx.send("▶️ Reanudado.")

    # ── !skip ─────────────────────────────────────────────
    @commands.hybrid_command(name="skip", aliases=["s"], description="Salta a la siguiente canción.")
    async def skip(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player or not player.playing:
            await ctx.send("❌ No hay nada reproduciéndose.")
            return
        await player.skip(force=True)
        await ctx.send("⏭️ Saltado.")

    # ── !queue ────────────────────────────────────────────
    @commands.hybrid_command(name="queue", aliases=["q"], description="Muestra la cola de reproducción.")
    async def queue(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal de voz.")
            return

        embed = discord.Embed(title="🎵 Cola de reproducción", color=discord.Color.blurple())

        if player.current:
            embed.add_field(
                name="▶️ Ahora sonando",
                value=f"**{player.current.title}** — `{player.current.author}`",
                inline=False,
            )

        if player.queue.is_empty:
            embed.add_field(name="Cola", value="Vacía", inline=False)
        else:
            lines = []
            for i, track in enumerate(list(player.queue)[:10], 1):
                lines.append(f"`{i}.` **{track.title}** — `{track.author}`")
            if len(player.queue) > 10:
                lines.append(f"*... y {len(player.queue) - 10} más*")
            embed.add_field(name=f"En cola ({len(player.queue)})", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    # ── !nowplaying ───────────────────────────────────────
    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Muestra la canción actual.")
    async def nowplaying(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player or not player.current:
            await ctx.send("❌ No hay nada reproduciéndose.")
            return

        track = player.current
        duration = track.length // 1000  # ms → s
        position = player.position // 1000

        bar_len = 20
        filled = int(bar_len * position / max(duration, 1))
        bar = "▓" * filled + "░" * (bar_len - filled)

        def fmt(s: int) -> str:
            m, sec = divmod(s, 60)
            return f"{m}:{sec:02d}"

        embed = discord.Embed(
            title="🎵 Ahora sonando",
            description=f"**{track.title}**\n`{track.author}`",
            color=discord.Color.green(),
        )
        embed.add_field(name="Progreso", value=f"`{fmt(position)}` [{bar}] `{fmt(duration)}`", inline=False)
        if hasattr(track, "extras") and track.extras.get("requester"):
            embed.set_footer(text=f"Pedido por {track.extras['requester']}")

        await ctx.send(embed=embed)

    # ── !volume ───────────────────────────────────────────
    @commands.hybrid_command(name="volume", aliases=["vol"], description="Ajusta el volumen (0-100).")
    async def volume(self, ctx: commands.Context, vol: int):
        player = self._player(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal de voz.")
            return
        if not 0 <= vol <= 100:
            await ctx.send("❌ El volumen debe estar entre 0 y 100.")
            return
        await player.set_volume(vol)
        await ctx.send(f"🔊 Volumen ajustado a `{vol}%`.")

    # ── !disconnect ───────────────────────────────────────
    @commands.hybrid_command(name="disconnect", aliases=["dc"], description="Desconecta el bot del canal de voz.")
    async def disconnect(self, ctx: commands.Context):
        player = self._player(ctx)
        if not player:
            await ctx.send("❌ No estoy en ningún canal de voz.")
            return
        await player.disconnect()
        await ctx.send("👋 Desconectado y cola borrada.")

    # ── Evento: track ended → reproducir siguiente ────────
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if player is None:
            return
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    # ── Evento: inactividad → desconectar ─────────────────
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        await player.disconnect()


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
