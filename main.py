"""
    https://github.com/Rapptz/discord.py/blob/master/examples/reply.py
"""

# This example requires the 'message_content' privileged intent to function.

import discord
import credential

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
        guild_config = self.registered_guild.get(channel.guild.id, {})
        if channel.id in guild_config:
            guild_config.pop(channel.id) # Delete channel from guild permissions.
        c = [x.id for x in channel.guild.channels if x.type == discord.ChannelType.text]
        l = list(filter(lambda x: x[0] in c and "configuration" in x[1], guild_config.items())) # Check that there still exists at least 1 'configuration' channel saved.
        if not l:
            self.registered_guild.pop(channel.guild.id)
    
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        
        guild_config = self.registered_guild.get(message.guild.id, {})
        
        channel_permission = set(("registration",))
        if guild_config:
            channel_permission = guild_config.get(message.channel.id, set(()))
        
        content = message.content.strip()
        
        if "system" in channel_permission:
            if content.lower() == "!exit":
                await self.exit(message)
                return
        
        if "registration" in channel_permission or "configuration" in channel_permission:
            command = parse_command_name(content).lower()
            if command == "!set":
                parsed = parse_command(content, 3)
                if len(parsed) >= 2:
                    type_ = parsed[1].lower()
                    if type_ == "configuration" or (type_ in ("system", "command", "listen") and "registration" not in channel_permission):
                        if len(parsed) == 3:
                            channel = get_TextChannel_by_name(message.guild.channels, parsed[2])
                        else:
                            channel = message.channel
                        if channel:
                            guild_config[channel.id] = guild_config.get(channel.id, set(()))
                            guild_config[channel.id].add(type_)
                            self.registered_guild[message.guild.id] = guild_config
                            await message.reply(f"Channel '{channel.name}' is '{type_}' enabled.")
                return
        
        if "configuration" in channel_permission:
            command = parse_command_name(content).lower()
            if command == "!delete":
                parsed = parse_command(content, 3)
                if len(parsed) >= 2:
                    type_ = parsed[1].lower()
                    if type_ in ("system", "configuration", "command", "listen"):
                        if len(parsed) == 3:
                            channel = get_TextChannel_by_name(message.guild.channels, parsed[2])
                        else:
                            channel = message.channel
                        if channel:
                            permission = guild_config.get(channel.id)
                            if permission:
                                permission.discard(type_)
                                if not permission:
                                    guild_config.pop(channel.id)
                            await message.reply(f"Channel '{channel.name}' is '{type_}' disabled.")
                return
            
            if command == "!clear":
                parsed = parse_command(content, 2)
                if len(parsed) >= 1:
                    if len(parsed) == 2:
                        channel = get_TextChannel_by_name(message.guild.channels, parsed[1])
                    else:
                        channel = message.channel
                    if channel:
                        if channel.id in guild_config:
                            guild_config.pop(channel.id)
                        await message.reply(f"'{channel.name}' is clear.")
                return
            
            if command == "!reset":
                parsed = parse_command(content, 2)
                if len(parsed) == 1:
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
                        await message.reply(f"'{channel.name}' is '{', '.join(guild_config.get(channel.id, set(())))}'.")
                return
            
            if content.lower() == "!list":
                l = []
                for (i, x) in guild_config.items():
                    channel = list(filter(lambda x: x.id == i and x.type == discord.ChannelType.text, message.guild.channels))
                    if len(channel) == 0:
                        guild_config.pop(i)
                    else:
                        l.append(f"'{channel[0].name}' is '{', '.join(x)}'")
                s = '\n'.join(l)
                await message.reply(f"{s}")
                return
        
        if "command" in channel_permission:
            command = parse_command_name(content).lower()
            if command == "!hello":
                await message.reply("Hello!", mention_author = True)
                return
        
        if "listen" in channel_permission:
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
