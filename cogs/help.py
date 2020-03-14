import discord
import colors

from discord.ext import commands

INVISBLE = '‏‏‎ ‎'

BRIEFS = {
    'snipe': 'Show the `i`th last deleted message in channel',
    'snipedit': 'Show the `i`th last edited message in channel',
    'snipelog': 'Show last 10 deleted messages in `channel`',
    'editlog': 'Show last 10 edited messages in `channel`',
    'life path': 'Get life path number from `DOB`',
    'lasotuvi': 'Get your **la so tu vi** from [tuvilyso.vn](https://tuvilyso.vn)',
    'avatar': 'Zoom in on someone\'s avatar before they yeet it',
    'do math': 'Compute big numbers for you',
    'whos': '*Who is this guy?*',
    'emotes': 'Lemme drop a Nitro emoji for you',
    'upsidedown': 'Write texts uʍop ǝpᴉsdn for your mates in the Southern Hemisphere.',
    'rps': 'Play a game of Rock Paper Scissors with your friend',
    'invite': 'Invite me to your server!',
    'mock': 'mOkK WhAt yOuR FrIeNd sAyS',
}

DEFAULT_HELP = '_Either DJ\'s too lazy or forget to write this_'

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(hidden=True)
    async def help(self, context):
        embed = colors.embed(title=f'{self.bot.user.name} Command List')
        embed.set_footer(text='Nag DJ for more features', icon_url=self.bot.user.avatar_url)

        done = []
        cogs_to_fields = {}
        for cog_name, cog in self.bot.cogs.items():
            fields = []
            for command in cog.walk_commands():
                if command.hidden: continue
                name = command.qualified_name

                if name in done:
                    continue
                done.append(name)
                
                for a in command.aliases:
                    name += '/' + a
                
                if command.clean_params:
                    params = []
                    for i, p in enumerate(command.clean_params):
                        params += [p]

                    params = ', '.join(params)
                    name += f' [{params}]'

                brief = BRIEFS.get(command.qualified_name, DEFAULT_HELP)
                fields += [(name, brief)]
            
            if fields:
                cogs_to_fields[cog_name] = fields
                
        for cog_name, fields in cogs_to_fields.items():
            lines = []
            for name, brief in fields:
                lines += [f'`{name}`\n{brief}']
            lines = '\n\n'.join(lines)

            embed.add_field(name=cog_name, value=lines, inline=False)

        await context.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))