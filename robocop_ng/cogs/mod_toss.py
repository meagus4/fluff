# This Cog contains code from Tosser2, which was made by OblivionCreator.
import discord
import json
import os
import config
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import userlog

toss_role = config.toss_role_id

class ModToss(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_list(self, ctx, user_ids):
        user_id_list = []
        invalid_ids = []

        if user_ids.isnumeric():
            tmp_user = ctx.guild.get_member(int(user_ids))
            if tmp_user is not None:
                user_id_list.append(tmp_user)
            else:
                invalid_ids.append(user_ids)
        else:
            if ctx.message.mentions:
                for u in ctx.message.mentions:
                    user_id_list.append(u)
            user_ids_split = user_ids.split()
            for n in user_ids_split:
                if n.isnumeric():
                    user = ctx.guild.get_member(int(n))
                    if user is not None:
                        user_id_list.append(user)
                    else:
                        invalid_ids.append(n)

        return user_id_list, invalid_ids

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def toss(self, ctx, *, user_ids):
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        name_list = ""
        for us in user_id_list:
            if us.id == ctx.author.id:
                await ctx.reply("For your own safety and the safety of others, please refrain from tossing yourself.")
                continue

            if us.id == self.bot.application_id:
                await ctx.reply(f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that.", mention_author=False)
                continue
                
            temp_role_list = []
            roles = []
            role_ids = []
            for rx in us.roles:
                if rx.name != '@everyone' and rx.name != toss_role:
                    roles.append(rx)
                    role_ids.append(rx.id)
                    
            try:
                with open(rf"data/toss/{us.id}.json", "x") as file:
                    file.write(json.dumps(role_ids))
            except FileExistsError:
                if ctx.guild.get_role(toss_role) in us.roles:
                    await ctx.reply(f"{us.name} is already tossed.")
                    continue
                else:
                    with open(rf"data/toss/{us.id}.json", 'w') as file:
                        file.write(json.dumps(role_ids))
                        
            prev_roles = ""

            for r in roles:
                temp_role_list.append(r.id)
                prev_roles = f"{prev_roles} `{r.name}`"
            
            try:
                await us.add_roles(ctx.guild.get_role(toss_role), reason='User tossed.')
                if len(roles)>0:
                    bad_no_good_terrible_roles = []
                    for rr in roles:
                        try:
                            await us.remove_roles(rr, reason=f'User tossed by {ctx.author} ({ctx.author.id})')
                        except Exception as e:
                            bad_no_good_terrible_roles.append(rr.name)

                bad_roles_msg = ""
                if len(bad_no_good_terrible_roles)>0:
                    bad_roles_msg = f"\nI was unable to remove the following role(s): **{', '.join(bad_no_good_terrible_roles)}**"
                await ctx.reply(f"**{us.name}**#{us.discriminator} has been tossed.\n"
                                f"**ID:** {us.id}\n"
                                f"**Created:** <t:{int(us.created_at.timestamp())}:R> (<t:{int(us.created_at.timestamp())}>)\n"
                                f"**Joined:** <t:{int(us.joined_at.timestamp())}:R> (<t:{int(us.joined_at.timestamp())}>)\n"
                                f"**Previous Roles:** {prev_roles}{bad_roles_msg}")
            except commands.MissingPermissions:
                invalid_ids.append(us.name)
            name_list = f"{us.name}, {name_list}"
            
        invalid_string = ""
        if len(invalid_ids) > 0:
            for iv in invalid_ids:
                invalid_string = f"{invalid_string}, {iv}"
            invalid_string = f"\nI was unable to toss these users: {invalid_string[2:]}"
            
        #if len(name_list[0:-2]) > 0:
        #    await ctx.reply(f"{name_list[0:-2]} has been tossed.{invalid_string}")
        if len(invalid_string) > 0:
            await ctx.reply(invalid_string)
            
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def untoss(self, ctx, *, user_ids):
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        name_list = ""
        
        for us in user_id_list:
            if us.id == self.bot.application_id:
                await ctx.reply("Leave me alone.")
                continue

            if us.id == ctx.author.id:
                await ctx.reply("This is not an option.")
                continue

            try:
                with open(rf"data/toss/{us.id}.json") as file:
                    raw_d = file.read()
                    roles = json.loads(raw_d)
                    print(roles)
                os.remove(rf"data/toss/{us.id}.json")
            except FileNotFoundError:
                await ctx.reply(f"{us.name} is not currently tossed.")
            roles_actual = []
            restored = ""
            for r in roles:
                temp_role = ctx.guild.get_role(r)
                if temp_role is not None:
                    roles_actual.append(temp_role)
            for rr in roles_actual:
                try:
                    await us.add_roles(rr, reason=f"Untossed by {ctx.author} ({ctx.author.id})")
                except Exception:
                    roles_actual.remove(rr)

            for rx in roles_actual:
                restored = f"{restored} `{rx.name}`"

            await us.remove_roles(ctx.guild.get_role(toss_role), reason=f"Untossed by {ctx.author} ({ctx.author.id})")
            await ctx.reply(f"**{us.name}**#{us.discriminator} has been untossed.\n**Roles Restored:** {restored}")
            name_list = f"{us.name}, {name_list}"

        invalid_string = ""

        if len(invalid_ids) > 0:
            for iv in invalid_ids:
                invalid_string = f"{invalid_string}, {iv}"
            invalid_string = f"\nI was unable to untoss these users: {invalid_string[2:]}"

        #if len(name_list[0:-2]) > 0:
        #    await ctx.reply(f"{name_list[0:-2]} has been untossed.{invalid_string}")
        if len(invalid_string) > 0:
            await ctx.reply(invalid_string)
            
async def setup(bot):
    await bot.add_cog(ModToss(bot))
