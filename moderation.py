import discord
from modules.botModule import *
import shlex
import time
from tinydb import TinyDB, Query


class Moderation(BotModule):
    name = 'moderation'

    description = 'Moderation tools for moderators.'

    help_text = '**These tools are only available for moderators/admins.** \n' \
                '`!mod warn [user_mention] [reason] - to issue a warning to a user. \n ' \
                '`!mod seal [user_mention] [reason] - to seal an incident. That incident will no longer count ' \
                'towards the user\'s total infractions, but will still be viewable. \n ' \
                '`!mod incident [incident_id] - to look up a specific incident. \n'

    infraction_limit = 3

    silent_mode = True # With silent mode on, no alerts will be issued. This does nothing right now

    trigger_string = 'mod'

    module_version = '1.0.0'

    listen_for_reaction = False

    logging_channel = '186155941119524864'

    moderation_roles = ['moderators', 'admins'] # Only people with these roles can issue a warning

    def total_infractions(self, id):
        table = self.module_db.table('warnings')
        target = Query()
        count = 0
        search = table.search(target.accusedid == id)
        if not search:
            return count
        for entry in table.search(target.accusedid == id):
            if entry['sealed']:
                pass
            else:
                count += 1
        return count

    def is_allowed(self, server, user):
        server_roles = server.roles
        server_roles_str = [x.name for x in server_roles]
        role = [i for i, x in enumerate(server_roles_str) if x in self.moderation_roles] # Straight from roles.py
        if len(role) == 0:
            return False
        else:
            return True

    @staticmethod
    def has_one_mention(message):
        if len(message.mentions) == 1:
            return True
        else:
            return False

    async def parse_command(self, message, client):
        logging_channel = message.server.get_channel(self.logging_channel)
        if logging_channel is None:
            send_message = "[!] I can't find the logging channel. I won't be processing this incident, " \
                           "please fix before continuing."
            await client.send_message(message.channel, send_message)
            return 0
        target = Query()
        if not self.is_allowed(message.server, message.author):
            send_message = "[!] Sorry, moderation tools are only available for moderators."
            await client.send_message(message.channel, send_message)
            return 0
        msg = shlex.split(message.content)
        mod_name = str(message.author)
        if msg[1] == 'warn':
            table = self.module_db.table('warnings')
            if len(msg) >= 3 and self.has_one_mention(message):
                try:
                    reason = msg[3]
                except IndexError:
                    reason = "No reason given..."
                cached_name = str(message.mentions[0])
                incident_id = table.insert({'modid': message.author.id, 'accusedid': message.mentions[0].id,
                                            'cachedname': cached_name, 'reason': msg[3],
                                            'time': time.time(), 'sealed': False, 'sealed_reason': '', 'seal_modid': ''})
                embed = discord.Embed(title="Case #" + str(incident_id), description="Incident report",
                                      color=0xffff00)
                embed.add_field(name="User", value=cached_name, inline=True)
                embed.add_field(name="Mod responsible", value=mod_name, inline=True)
                embed.add_field(name="Reason given", value=msg[3], inline=True)
                total_infractions_count = self.total_infractions(message.mentions[0].id)
                embed.set_footer(text="Infractions: " + str(total_infractions_count))
                await client.send_message(logging_channel, embed=embed)
                warn_message = message.mentions[0].mention + ", you have received a warning. Reason: " + msg[3]
                await client.send_message(message.channel, warn_message)
                if total_infractions_count >= self.infraction_limit:
                    limit_message = "**Alert:** User " + cached_name + " has exceeded the infraction limit."
                    await client.send_message(logging_channel, limit_message)
            else:
                send_message = "[!] Missing arguments."
                await client.send_message(message.channel, send_message)
                return 0
        elif msg[1] == 'seal':
            table = self.module_db.table('warnings')
            if len(msg) >= 3:
                if not table.contains(doc_ids=[int(msg[2])]):
                    send_message = "[!] Could not find incident."
                    await client.send_message(message.channel, send_message)
                    return 0
                try:
                    reason = msg[3]
                except IndexError:
                    reason = "No reason given..."
                if table.get(doc_id=int(msg[2]))['sealed']:
                    send_message = "[!] Record is already sealed."
                    await client.send_message(message.channel, send_message)
                    return 0
                table.update({'sealed': True, 'sealed_reason': reason, 'seal_modid': message.author.id},
                             doc_ids=[int(msg[2])])
                send_message = "[:ok_hand:] Sealed record."
                await client.send_message(message.channel, send_message)
                seal_message = "Incident #" + msg[2] + " was sealed by " + str(message.author) + ". Reason: " + reason
                await client.send_message(logging_channel, seal_message)
            else:
                send_message = "[!] Invalid arguments."
                await client.send_message(message.channel, send_message)
                return 0
        elif msg[1] == 'incident':
            table = self.module_db.table('warnings')
            entry = table.get(doc_id=int(msg[2]))
            if len(msg) == 3:
                if not entry:
                    send_message = "[!] Could not find incident."
                    await client.send_message(message.channel, send_message)
                    return 0
                if entry['sealed']:
                    col = 0x00ff00
                else:
                    col = 0xffff00
                embed = discord.Embed(title="Case #" + msg[2], description="Incident report (lookup)",
                                      color=col)
                embed.add_field(name="User", value=entry['cachedname'], inline=True)
                embed.add_field(name="Mod responsible",
                                value=str(await client.get_user_info(entry['modid'])), inline=True)
                embed.add_field(name="Reason given", value=entry['reason'], inline=True)
                if entry['sealed']:
                    embed.add_field(name="Reason incident was sealed", value=entry['sealed_reason'], inline=True)
                embed.set_footer(text="Infractions: "
                                      + str(self.total_infractions(entry['accusedid'])))
                await client.send_message(message.channel, embed=embed)
            else:
                send_message = "[!] Invalid arguments."
                await client.send_message(message.channel, send_message)
                return 0
        else:
            pass
