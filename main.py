"""
    https://github.com/Rapptz/discord.py/blob/master/examples/reply.py
"""

# This example requires the 'message_content' privileged intent to function.

import discord
import credential
from solver import Solver, Register


class MyClient(discord.Client):
    def __init__(self, privileged_id, *args, **kwargs):
        super(MyClient, self).__init__(*args, **kwargs)
        self.privileged_id = privileged_id
        self.registered_guild = {}
    
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_guild_channel_delete(self, channel):
        guild_config = self.registered_guild.get(channel.guild.id)
        if guild_config:
            guild_config.permission_delete(channel.id)
            if not guild_config.is_configured():
                self.registered_guild.pop(guild_config.id)
    
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        
        guild_config = self.registered_guild.get(message.guild.id, Register.default())
        
        content = message.content.strip()
        
        if guild_config.channel_is_system(message.channel.id):
            if content.lower() == "!exit":
                await self.exit(message)
                return
        
        solved = await guild_config.discord_receive(message, self)
        if solved:
            return
        
        if message.author.id == self.privileged_id:
            if content.lower() == "!exit":
                await self.exit(message)
                return
    
    async def exit(self, message):
        await message.reply("Terminating...", mention_author = True)
        await self.close()


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = MyClient(credential.USER_ID, intents = intents)
client.run(credential.TOKEN)
