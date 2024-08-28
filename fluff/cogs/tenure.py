import discord
import json
from discord.ext.commands import Cog
from discord.ext import commands
from helpers.sv_config import get_config
from helpers.datafiles import get_guildfile, set_guildfile
from helpers.checks import ismanager, isadmin
from datetime import datetime, timedelta, UTC
from config import logchannel
class Tenure(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Tenure isn't configured for this server.."
    
    async def check_joindelta(self, member: discord.Member):
        return (datetime.now(UTC) - member.joined_at)
    
    def get_tenureconfig(self, guild: discord.Guild):
        return {
            "role": self.bot.pull_role(guild, get_config(guild.id, "tenure", "role")),
            "threshold": get_config(guild.id, "tenure", "threshold"),
        }
    
    def enabled(self, guild: discord.Guild):
        return all(
        (
            self.bot.pull_role(guild, get_config(guild.id, "tenure", "role")),
            get_config(guild.id, "tenure", "threshold"),
        )
        )
    
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.group(invoke_without_command=True)
    async def tenure(self, ctx):
        """This shows the user their tenure in the server.
        
        Any guild channel that has Tenure configured.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        
        tenure_dt = await self.check_joindelta(ctx.author)
        tenure_days = tenure_dt.days
        tenure_threshold = get_config(ctx.guild.id, "tenure", "threshold")
        tenure_role = self.bot.pull_role(ctx.guild, get_config(ctx.guild.id, "tenure", "role"))
        tenure = get_guildfile(ctx.guild.id, "tenure")
        tenure_bl = None
        if "bl" in tenure:
            tenure_bl = tenure["bl"]
        else:
            tenure["bl"]  = []
            tenure_bl = tenure["bl"]

        if str(ctx.author.id) in tenure_bl:
            return await ctx.reply("You're blacklisted from being Tenured, go away! *thump*", mention_author=False)

        if tenure_threshold < tenure_days:
           if tenure_role not in ctx.author.roles:
            await ctx.author.add_roles(tenure_role, reason="Fluff Tenure")
            return await ctx.reply(f"You joined around {tenure_days} (to be more exact, `{tenure_dt} (UTC)`) days ago! You've been here long enough to be assigned the {tenure_role.name} role!",mention_author=False)
           else:
            await ctx.reply(f"You joined around {tenure_days}  (to be more exact, `{tenure_dt} (UTC)`) days ago, and you've already been assigned the {tenure_role.name} role!",mention_author=False)
        else:
            await ctx.reply(f"You joined around {tenure_days} (to be more exact, `{tenure_dt} (UTC)`) days ago! Not long enough, though.. try again in {(timedelta(days=tenure_threshold)-tenure_dt).days} days!",mention_author=False)
    
    @commands.check(ismanager)
    @commands.cooldown(1, 43200, commands.BucketType.guild)
    @tenure.command()
    async def force_sync(self,ctx):
       """THIS WILL FORCEFULLY SYNCHRONIZE THE SERVER MEMBERS WITH THE TENURE ROLE.

       THIS IS VERY TIME CONSUMING.

       RUN ONCE, NEVER AGAIN.
       """
       if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
       tenure_config = self.get_tenureconfig(ctx.guild)
       tenure_threshold = tenure_config["threshold"]
       tenure_role = tenure_config["role"]

       await ctx.reply("Oh boy..", mention_author=False)

       for member in ctx.guild.members:
            tenure_dt = await self.check_joindelta(member)
            tenure_days = tenure_dt.days
            print(f"{member.global_name} ({member.id}) joined {tenure_days} days ago")
            if tenure_threshold < tenure_days:
                if tenure_role not in member.roles:
                    print(f"Assigning {tenure_role.name} to {member.global_name}, as they have enough tenure")
                    await member.add_roles(tenure_role, reason="Fluff Tenure")
                else:
                    return

    @tenure.command(aliases=["disable", "bl", "ignore"])
    @commands.check(isadmin)
    async def blacklist(self, ctx, users: commands.Greedy[discord.Member]):
        """This will blacklist users from being tenured.

        - `users`
        A list of users to blacklist from being tenured."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        
        tenure = get_guildfile(ctx.guild.id, "tenure")
        tenure_bl = None
        if "bl" in tenure:
            tenure_bl = tenure["bl"]
        else:
            tenure["bl"]  = []
            tenure_bl = tenure["bl"]

        for user in users:
            if user.id not in tenure_bl:
                tenure_bl.append(str(user.id))
        
        set_guildfile(ctx.guild.id, "tenure", json.dumps(tenure))
        await ctx.reply("Users blacklisted from being tenured.", mention_author=False)

    @tenure.command(aliases=["enable", "wl", "allow"])
    @commands.check(isadmin)
    async def whitelist(self, ctx, users: commands.Greedy[discord.Member]):
        """This will whitelist users to be tenured.

        - `users`
        A list of users to whitelist for being tenured."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        
        tenure = get_guildfile(ctx.guild.id, "tenure")
        tenure_bl = None
        if "bl" in tenure:
            tenure_bl = tenure["bl"]
        else:
            tenure["bl"]  = []
            tenure_bl = tenure["bl"]

        for user in users:
            if user.id in tenure_bl:
                tenure_bl.remove(str(user.id))
        
        set_guildfile(ctx.guild.id, "tenure", json.dumps({"bl": tenure_bl}))
        await ctx.reply("Users whitelisted for being tenured.", mention_author=False)


    @Cog.listener()
    async def on_message(self, msg):
        await self.bot.wait_until_ready()

        if (
            msg.author.bot
            or msg.is_system()
            or not msg.guild
        ):
            return
        
        if not self.enabled(msg.guild):
            return
        
        tenureconfig = self.get_tenureconfig(msg.guild)
        tenure_dt = await self.check_joindelta(msg.author)
        tenure_days = tenure_dt.days
        logchannel_cached = self.bot.get_channel(logchannel)
        tenure = get_guildfile(msg.guild.id, "tenure")
        tenure_bl = None
        if "bl" in tenure:
            tenure_bl = tenure["bl"]
        else:
            tenure["bl"]  = []
            tenure_bl = tenure["bl"]

        if msg.author.id in tenure_bl:
            return False
        
        if tenureconfig["threshold"] < tenure_days:
            if tenureconfig["role"] not in msg.author.roles:
                await msg.author.add_roles(tenureconfig["role"], reason="Fluff Tenure")
                if logchannel_cached:
                    await logchannel_cached.send(f":infinity: **{msg.guild.name}** {msg.author.mention} has been assigned the {tenureconfig['role'].name} role.")

        

async def setup(bot: discord.Client):
    await bot.add_cog(Tenure(bot))