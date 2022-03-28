# meta.py | commands about the bot
# Copyright (C) 2019-2021  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import typing

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import escape_markdown as esc

from bot.data import database, logger
from bot.functions import send_leaderboard


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # bot info command - gives info on bot
    @app_commands.command(
        name="botinfo",
        description="Gives info on bot, support server invite, stats",
    )
    async def botinfo(self, interaction: discord.Interaction):
        logger.info("command: botinfo")

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name="Bird ID - An Ornithology Bot")
        embed.add_field(
            name="Bot Info",
            value="This bot was created by EraserBird and person_v1.32 "
            + "for helping people practice bird identification for Science Olympiad.\n"
            + "**By adding this bot to a server, you are agreeing to our "
            + "[Privacy Policy](<https://github.com/tctree333/Bird-ID/blob/master/PRIVACY.md>) and "
            + "[Terms of Service](<https://github.com/tctree333/Bird-ID/blob/master/TERMS.md>)**.\n"
            + "Bird-ID is licensed under the [GNU GPL v3.0](<https://github.com/tctree333/Bird-ID/blob/master/LICENSE>).",
            inline=False,
        )
        embed.add_field(
            name="Credits",
            value="Images are from the Macaulay Library at the Cornell Lab of Ornithology.\n\n"
            + "The bot profile picture and server icon were drawn by naddle and Nin, respectively.",
            inline=False,
        )
        embed.add_field(
            name="Support",
            value="If you are experiencing any issues, have feature requests, "
            + "or want to get updates on bot status, join our support server below.",
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=f"This bot is in {len(self.bot.guilds)} servers. "
            + f"The WebSocket latency is {round((self.bot.latency*1000))} ms.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)
        await interaction.followup.send("https://discord.gg/2HbshwGjnm")

    # ping command - gives bot latency
    @app_commands.command(
        name="ping",
        description="Pings the bot and displays latency",
    )
    async def ping(self, interaction: discord.Interaction):
        logger.info("command: ping")
        lat = round(self.bot.latency * 1000)
        logger.info(f"latency: {lat}")
        await interaction.response.send_message(
            f"**Pong!** The WebSocket latency is `{lat}` ms."
        )

    # invite command - sends invite link
    @app_commands.command(name="invite", description="Get the invite link for this bot")
    async def invite(self, interaction: discord.Interaction):
        logger.info("command: invite")

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name="Bird ID - An Ornithology Bot")
        embed.add_field(
            name="Invite",
            value="To invite this bot to your own server, use the following invite links.\n"
            + "**Bird-ID:** https://discord.com/api/oauth2/authorize?client_id=601917808137338900&permissions=268486656&scope=bot\n\n"
            + "**By adding this bot to a server, you are agreeing to our `Privacy Policy` and `Terms of Service`**.\n"
            + "<https://github.com/tctree333/Bird-ID/blob/master/PRIVACY.md>, <https://github.com/tctree333/Bird-ID/blob/master/TERMS.md>",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)
        await interaction.followup.send("https://discord.gg/2HbshwGjnm")

    # ignore command - ignores a given channel
    @commands.command(
        brief="- Ignore all commands in a channel",
        help="- Ignore all commands in a channel. The 'manage guild' permission is needed to use this command.",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def ignore(self, ctx, channels: commands.Greedy[discord.TextChannel] = None):
        logger.info("command: invite")

        added = []
        removed = []
        if channels is not None:
            logger.info(f"ignored channels: {[c.name for c in channels]}")
            for channel in channels:
                if database.zscore("ignore:global", str(channel.id)) is None:
                    added.append(
                        f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                    )
                    database.zadd("ignore:global", {str(channel.id): ctx.guild.id})
                else:
                    removed.append(
                        f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                    )
                    database.zrem("ignore:global", str(channel.id))
        else:
            await ctx.send("**No valid channels were passed.**")

        ignored = "".join(
            (
                f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                for channel in map(
                    lambda c: ctx.guild.get_channel(int(c)),
                    database.zrangebyscore(
                        "ignore:global", ctx.guild.id - 0.1, ctx.guild.id + 0.1
                    ),
                )
            )
        )

        await ctx.send(
            (f"**Ignoring:**\n{''.join(added)}" if added else "")
            + (f"**Stopped ignoring:**\n{''.join(removed)}" if removed else "")
            + (
                f"**Ignored Channels:**\n{ignored}"
                if ignored
                else "**No channels in this server are currently ignored.**"
            )
        )

    # leave command - removes itself from guild
    @commands.command(
        brief="- Remove the bot from the guild",
        help="- Remove the bot from the guild. The 'manage guild' permission is needed to use this command.",
        aliases=["kick"],
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def leave(self, ctx, confirm: typing.Optional[bool] = False):
        logger.info("command: leave")

        if database.exists(f"leave:{ctx.guild.id}"):
            logger.info("confirming")
            if confirm:
                logger.info(f"confirmed. Leaving {ctx.guild}")
                database.delete(f"leave:{ctx.guild.id}")
                await ctx.send("**Ok, bye!**")
                await ctx.guild.leave()
                return
            logger.info("confirm failed. leave canceled")
            database.delete(f"leave:{ctx.guild.id}")
            await ctx.send("**Leave canceled.**")
            return

        logger.info("not confirmed")
        database.set(f"leave:{ctx.guild.id}", 0, ex=60)
        await ctx.send(
            "**Are you sure you want to remove me from the guild?**\n"
            + "Use `b!leave yes` to confirm, `b!leave no` to cancel. "
            + "You have 60 seconds to confirm before it will automatically cancel."
        )

    # ban command - prevents certain users from using the bot
    @commands.command(help="- ban command", hidden=True)
    @commands.is_owner()
    async def ban(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: ban")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zadd("banned:global", {str(user.id): 0})
        await ctx.send(f"Ok, {esc(user.name)} cannot use the bot anymore!")

    # unban command - prevents certain users from using the bot
    @commands.command(help="- unban command", hidden=True)
    @commands.is_owner()
    async def unban(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: unban")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zrem("banned:global", str(user.id))
        await ctx.send(f"Ok, {esc(user.name)} can use the bot!")

    # unban command - prevents certain users from using the bot
    @commands.command(help="- see answered birds command", hidden=True)
    @commands.is_owner()
    async def correct(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: correct")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        await send_leaderboard(
            ctx,
            f"Top Correct Birds ({esc(user.name)})",
            1,
            database_key=f"correct.user:{user.id}",
            items_per_page=25,
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, _):
        logger.info("command: sync")
        print(await self.bot.tree.sync())


async def setup(bot):
    await bot.add_cog(Meta(bot))
