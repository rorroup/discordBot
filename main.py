"""
    https://github.com/Rapptz/discord.py/blob/master/examples/reply.py
"""

# This example requires the 'message_content' privileged intent to function.

import discord
import credential
from permission import Permission

def get_TextChannel_by_name(channels, name):
    l = list(filter(lambda x: x.name.startswith(name) and isinstance(x, discord.TextChannel) and x.type == discord.ChannelType.text, channels))
    if not l:
        return None
    l.sort(key = lambda x: len(x.name))
    return l[0]

def parse_command_name(command):
    name = ""
    for c in command:
        if c.isspace():
            break
        else:
            name += c
    return name

def parse_command(command, parts):
    parsed = []
    found = 0
    current = ""
    for c in command:
        if found >= parts:
            current += c
        else:
            if c.isspace():
                if current != "":
                    parsed.append(current)
                    current = ""
            else:
                if current == "":
                    found += 1
                current += c
    parsed.append(current)
    print(parsed)
    return parsed

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
            guild_config.clear(channel.id)
            if not guild_config.channels:
                self.registered_guild.pop(channel.guild.id)
    
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        
        guild_config = self.registered_guild.get(message.guild.id, {})
        channel_permission = guild_config.get(message.channel.id, Permission.NONE)
        
        content = message.content.strip()
        
        if (channel_permission & Permission.SYSTEM):
            if content.lower() == "!exit":
                await self.exit(message)
                return
        
        if (channel_permission & Permission.CONFIGURATION) or guild_config == {}:
            command = parse_command_name(content).lower()
            if command == "!set":
                parsed = parse_command(content, 3)
                if len(parsed) >= 2:
                    type_ = Permission.permissions.get(parsed[1].lower(), Permission.NONE)
                    if (type_ & Permission.CONFIGURATION) or ((type_ & (Permission.SYSTEM | Permission.COMMAND | Permission.READ)) and guild_config != {}):
                        if len(parsed) == 3:
                            channel = get_TextChannel_by_name(message.guild.channels, parsed[2])
                        else:
                            channel = message.channel
                        if channel:
                            if guild_config == {}:
                                self.registered_guild[message.guild.id] = Permission(message.guild.id)
                            self.registered_guild[message.guild.id].add(channel.id, type_)
                            await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' enabled.")
                return
        
        if (channel_permission & Permission.CONFIGURATION):
            command = parse_command_name(content).lower()
            if command == "!delete":
                parsed = parse_command(content, 3)
                if len(parsed) >= 2:
                    type_ = Permission.permissions.get(parsed[1].lower())
                    if type_:
                        if len(parsed) == 3:
                            channel = get_TextChannel_by_name(message.guild.channels, parsed[2])
                        else:
                            channel = message.channel
                        if channel:
                            guild_config.delete(channel.id, type_)
                            if not guild_config.channels:
                                self.registered_guild.pop(message.guild.id)
                            await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' disabled.")
                return
            
            if command == "!clear":
                parsed = parse_command(content, 2)
                if len(parsed) >= 1:
                    if len(parsed) == 2:
                        channel = get_TextChannel_by_name(message.guild.channels, parsed[1])
                    else:
                        channel = message.channel
                    if channel:
                        guild_config.clear(channel.id)
                        if not guild_config.channels:
                            self.registered_guild.pop(message.guild.id)
                        await message.reply(f"'{channel.name}' is clear.")
                return
            
            if content.lower() == "!reset":
                self.registered_guild.pop(message.guild.id)
                await message.reply("This guild configuration has been erased.")
                return
            
            if command == "!show":
                parsed = parse_command(content, 2)
                if len(parsed) >= 1:
                    if len(parsed) == 2:
                        channel = get_TextChannel_by_name(message.guild.channels, parsed[1])
                    else:
                        channel = message.channel
                    if channel:
                        await message.reply(f"'{channel.name}' is '{', '.join(filter(lambda x: Permission.permissions[x] & guild_config.get_permission(channel.id), Permission.permissions.keys()))}'.")
                return
            
            if content.lower() == "!list":
                l = []
                for (i, p) in guild_config.channels.items():
                    channel = list(filter(lambda x: x.id == i and x.type == discord.ChannelType.text, message.guild.channels))
                    if len(channel) == 0:
                        guild_config.clear(i)
                    else:
                        l.append(f"'{channel[0].name}' is '{', '.join(filter(lambda x: Permission.permissions[x] & p, Permission.permissions.keys()))}'")
                s = '\n'.join(l)
                await message.reply(f"{s}")
                return
        
        if (channel_permission & Permission.COMMAND):
            command = parse_command_name(content).lower()
            if command == "!hello":
                await message.reply("Hello!", mention_author = True)
                return
        
        if (channel_permission & Permission.READ):
            await message.reply(content, mention_author = True)
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
