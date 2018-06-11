import discord
from modules.botModule import *
import shlex
import time

class Moderation(BotModule):
    name = 'moderation'

    description = 'Moderation tools for moderators.'

    help_text = '**These tools are only available for moderators/admins. \n' \
                '`!mod warn [userid] [reason] [evidence] - to issue a warning to a user. \n ' \
                '`!mod ban [userid] [reason] [time] - to issue a **temporary** ban to a user. To issue a permaban, use builtin Discord tools. \n '

    infraction_limit = 10

    silent_mode = True # With silent mode on, no alerts will be issued.

    trigger_string = 'mod'

    module_version = '1.0.0'

    listen_for_reaction = False

    logging_channel = '123456789012345678'

    def safe_cached_name(self, server, id): # Only use this function to refresh during an incident recall
        refresh = server.get_member(id)
        if refresh is None:
            return 0
        else:
            return refresh

    def total_infractions(self, id):
        table = self.module_db.table('warnings')
        target = Query()
        return table.count(target.accusedid == id)


    async def parse_command(self, message, client):
        target = Query()
        msg = shlex.split(message.content)
        mod_name = server.get_member(message.author.id)
        if msg[1] == 'warn':
            table = self.module_db.table('warnings')
            if len(msg) >= 4:
                cached_name = message.server.get_member(msg[2])
                incident_id = table.insert({'modid': message.author.id, 'accusedid': msg[2], 'cachedname': cached_name, 'reason': msg[3], 'evidence': msg[4], 'time': time.time()})
                embed = discord.Embed(title="Case #" + incident_id, description="Incident report",
                                      color=0xffff00)
                embed.add_field(name="User", value=cached_name, inline=True)
                embed.add_field(name="Mod responsible", value=mod_name, inline=True)
                embed.add_field(name="Reason given", value=msg[3], inline=True)
                embed.add_field(name="Mod responsible", value=mod_name, inline=True)
                embed.set_footer(text="Infractions: " + total_infractions(msg[2]))
                await client.send_message(message.channel, embed=embed)
            else:
                send_message = "[!] Missing arguments."
                await client.send_message(message.channel, send_message)
        elif msg[1] == 'ban':
            table = self.module_db.table('warnings')
        else:
            pass
