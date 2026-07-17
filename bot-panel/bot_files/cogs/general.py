"""
Cog de ejemplo — comandos generales.
Renombra, edita o borra este archivo como quieras.
"""
import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog, name="General"):
    """Comandos generales del bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Slash puro ────────────────────────────────────
    @app_commands.command(name="hola", description="El bot te saluda.")
    async def hola(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"¡Hola, {interaction.user.mention}! 👋", ephemeral=True
        )

    # ── Híbrido (slash + prefix) ──────────────────────
    @commands.hybrid_command(name="avatar", description="Muestra el avatar de un usuario.")
    @app_commands.describe(usuario="El usuario del que ver el avatar (por defecto tú).")
    async def avatar(self, ctx: commands.Context, usuario: discord.Member = None):
        target = usuario or ctx.author
        embed = discord.Embed(title=f"Avatar de {target.display_name}", color=target.color)
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    # ── Prefix puro ───────────────────────────────────
    @commands.command(name="servidores")
    @commands.is_owner()
    async def servidores(self, ctx: commands.Context):
        """Lista los servidores donde está el bot (solo owner)."""
        guilds = "\n".join(f"• {g.name} ({g.id})" for g in self.bot.guilds)
        await ctx.send(f"```\n{guilds or 'Ninguno'}\n```")


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
