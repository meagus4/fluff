import discord
import json
import os
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import isadmin, ismanager
from helpers.embeds import stock_embed
from helpers.datafiles import get_guildfile, set_guildfile

'''
TODO: Rework this god awful system
'''

class Snippets(Cog):
    """
    Commands for easily explaining things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.guild_only()
    @commands.group(aliases=["snip"], invoke_without_command=True)
    async def rule(self, ctx, *, name=None):
        """This displays staff defined tags.

        Using this command by itself will show a list of tags.
        Giving a name will post that rule snippet in the chat.

        - `name`
        The name of the rule snippet to post. Optional."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if not name:
            embed = stock_embed(self.bot)
            embed.title = "Configured Snippets"
            embed.color = discord.Color.red()
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
            if not snippets:
                embed.add_field(
                    name="None",
                    value="There are no configured snippets.",
                    inline=False,
                )
            else:
                for name, snippet in list(snippets.items()):
                    if snippet in snippets:
                        continue
                    aliases = ""
                    for subname, subsnippet in list(snippets.items()):
                        if subsnippet == name:
                            aliases += f"\n➡️ " + subname
                        embed.add_field(
                        name=name,
                        value=(
                            "> "
                            + "\n> ".join(snippet[:200].split("\n"))
                            + "..."
                            + aliases
                            if len(snippet) > 200
                            else "> " + "\n> ".join(snippet.split("\n")) + aliases
                        ),
                        inline=False,
                    )
                            
            try:
                await ctx.reply(embed=embed, mention_author=False)
            except discord.errors.HTTPException as exception: # almost always too many embed fields
                if exception.code == 50035:
                    file_content = "" # GITHUB COPILOT CODE LOL
                    for name, snippet in list(snippets.items()):
                        if snippet in snippets:
                            continue
                        aliases = ""
                        for subname, subsnippet in list(snippets.items()):
                            if subsnippet == name:
                                aliases += f"\n➡️ " + subname
                        file_content += f"{name}:\n{snippet}\nAliases:{aliases}\n\n"

                    with open(f"temp/snippets-{ctx.guild.id}.txt", "w") as file:
                        file.write(file_content)

                    file_sent = await ctx.send(file=discord.File(f"temp/snippets-{ctx.guild.id}.txt"))
                    if file_sent:
                        os.remove(f"temp/snippets-{ctx.guild.id}.txt")
                    
                    
                
        else:
            if name.lower() not in snippets:
                return
            if snippets[name.lower()] in snippets:
                return await ctx.reply(
                    content=snippets[snippets[name.lower()]], mention_author=False
                )
            return await ctx.reply(content=snippets[name.lower()], mention_author=False)

    @commands.check(isadmin)
    @rule.command()
    async def create(self, ctx, name, *, contents):
        """This creates a new rule snippet.

        You can set the `contents` to be the name of another
        rule snippet to create an alias to that snippet. See the
        [documentation](https://3gou.0ccu.lt/as-a-moderator/the-snippet-system/) for more details.

        - `name`
        The name of the snippet to create.
        - `contents`
        The contents of the snippet."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if name.lower() in snippets:
            return await ctx.reply(
                content=f"`{name}` is already a snippet.",
                mention_author=False,
            )
        elif len(contents.split()) == 1 and contents in snippets:
            if snippets[contents] in snippets:
                return await ctx.reply(
                    content=f"You cannot create nested aliases.",
                    mention_author=False,
                )
            snippets[name.lower()] = contents
            set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
            await ctx.reply(
                content=f"`{name.lower()}` has been saved as an alias.",
                mention_author=False,
            )
        else:
            snippets[name.lower()] = contents
            set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
            await ctx.reply(
                content=f"`{name.lower()}` has been saved.",
                mention_author=False,
            )

    @commands.check(isadmin)
    @rule.command()
    async def delete(self, ctx, name):
        """This deletes a rule snippet.

        The name can be an alias as well. See the
        [documentation](https://3gou.0ccu.lt/as-a-moderator/the-snippet-system/) for more details.

        - `name`
        The name of the rule snippet to delete."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if name.lower() not in snippets:
            return await ctx.reply(
                content=f"`{name.lower()}` is not a snippet.",
                mention_author=False,
            )
        del snippets[name.lower()]
        set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
        await ctx.reply(
            content=f"`{name.lower()}` has been deleted.",
            mention_author=False,
        )

    @commands.check(isadmin)
    @rule.command()
    async def edit(self, ctx, name, *, new_content):
        """This edits a rule snippet."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if name.lower() not in snippets:
            return await ctx.reply(
                content=f"`{name.lower()}` is not a snippet.",
                mention_author=False,
            )
        snippets[name.lower()] = new_content
        set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
        await ctx.reply(
            content=f"'{name.lower()}' has been edited.",
            mention_author=False
        )
    
    @commands.check(ismanager)
    @rule.command()
    async def dump(self, ctx):
        """This dumps snippets."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        new_msg = await ctx.reply("Checking for snippets...", mention_author=False)
        if not snippets:
            new_msg.edit(content="There are no configured snippets to dump.")
        else:
            processed_snippets = {}
            for name, snippet in list(snippets.items()):
                if snippet in snippets:
                    processed_snippets[name] = {
                        "content": snippets[snippet],
                        "aliases": []
                    }
                    continue
                for subname, subsnippet in list(snippets.items()):
                    try:
                        if subsnippet == name and not isinstance(int(subname),int):
                            processed_snippets[name]["aliases"].append(str(subname))
                    except ValueError:
                        processed_snippets[name]["aliases"].append(str(subname))
                with open(f"temp/snippets-{ctx.guild.id}-dump.txt", "w") as file:
                    file.write(
                        json.dumps(processed_snippets, indent=4)
                    )
                
                file_sent = await ctx.send(file=discord.File(f"temp/snippets-{ctx.guild.id}-dump.txt"))
                if file_sent:
                    os.remove(f"temp/snippets-{ctx.guild.id}-dump.txt")
                    

                    

        

async def setup(bot):
    await bot.add_cog(Snippets(bot))