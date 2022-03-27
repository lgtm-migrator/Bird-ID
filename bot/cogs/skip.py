# skip.py | commands for skipping birds
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

from discord.ext import commands

import bot.voice as voice_functions
from bot.data import database, get_wiki_url, logger
from bot.data_functions import streak_increment
from bot.filters import Filter
from bot.functions import CustomCooldown


class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Skip command - no args
    @commands.command(help="- Skip the current bird to get a new one", aliases=["sk"])
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.channel))
    async def skip(self, ctx):
        logger.info("command: skip")

        currentBird = database.hget(f"channel:{ctx.channel.id}", "bird").decode("utf-8")
        database.hset(f"channel:{ctx.channel.id}", "bird", "")
        database.hset(f"channel:{ctx.channel.id}", "answered", "1")
        if currentBird != "":  # check if there is bird
            url = get_wiki_url(ctx, currentBird)
            await ctx.send(f"Ok, skipping {currentBird.lower()}")
            await ctx.send(url)  # sends wiki page

            streak_increment(ctx, None)  # reset streak

            if database.exists(f"race.data:{ctx.channel.id}"):
                if Filter.from_int(
                    int(database.hget(f"race.data:{ctx.channel.id}", "filter"))
                ).vc:
                    await voice_functions.stop(ctx, silent=True)

                media = database.hget(f"race.data:{ctx.channel.id}", "media").decode(
                    "utf-8"
                )

                logger.info(f"auto sending next bird {media}")
                filter_int, taxon, state = database.hmget(
                    f"race.data:{ctx.channel.id}", ["filter", "taxon", "state"]
                )
                birds = self.bot.get_cog("Birds")
                await birds.send_bird_(
                    ctx,
                    media,
                    Filter.from_int(int(filter_int)),
                    taxon.decode("utf-8"),
                    state.decode("utf-8"),
                )
        else:
            await ctx.send("You need to ask for a bird first!")


async def setup(bot):
    await bot.add_cog(Skip(bot))
