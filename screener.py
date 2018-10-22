import discord
from modules.botModule import *
import shlex
from tinydb import TinyDB, Query
from num2words import num2words
import random


class Screener(BotModule):
    name = 'screener'

    description = 'User screening for new users.'

    help_text = '`!screen [answer]` - respond to challenge given by the bot.'

    fail_limit = 5

    trigger_string = 'screen'

    module_version = '1.0.0'

    listen_for_member_join = True

    screen_channel = '186155941119524864' # Channel where new users will be waiting

    verified_role = 'verified' # Role to assign to new users once challenge is passed.

    moderation_roles = ['moderators', 'admins']

    challenge_responses = {}

    def generate_challenge(self, member):
        number_1 = random.randint(1, 10)
        number_2 = random.randint(1, 10)
        choice = random.randint(0, 1)

        self.challenge_responses[member.id] = number_1 + number_2
        if choice == 0:
            return "What is the sum of " + num2words(number_1) + " and " + num2words(number_2) + "?"
        elif choice == 1:
            return "What is " + num2words(number_1) + " plus " + num2words(number_2) + "?"

    async def verify(self, message, client):
        await client.add_roles(message.author, discord.utils.get(message.server.roles, name=self.verified_role))

    async def parse_command(self, message, client):
        if message.channel.id != self.screen_channel:
            pass
        msg = shlex.split(message.content)
        if len(msg) > 1 and msg[1].isdigit():
            response = int(msg[1])
            if self.challenge_responses[message.author.id] == response:
                await self.verify(message, client)

    async def on_member_join(self, member, client):
        # TODO: save a list of verified members in DB, skip verification if re-entry
        text = self.generate_challenge(member)
        send_message = "**Welcome to the SCUBA diving discord, " + member.mention + ".** \n" \
                       "For verification purposes please complete the challenge below. \n" \
                       + text + "\n " \
                       "You may respond with !screen [your answer]."
        await client.send_message(client.get_channel(self.screen_channel), send_message)
