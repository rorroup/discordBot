import discord
from permission import Permission


class Register(object):
    """
        Placeholder class for when there is no Solver set.
    """
    
    def __init__(self):
        self.permission = Permission()
    
    def channel_is_system(self, channel_id):
        return Permission.NONE
    
    async def discord_receive(self, message, discord_client):
        content = message.content.strip()
        parsed = self.parse_command(content, 3)
        if parsed:
            command = parsed[0].lower()
            if command == "!set":
                if len(parsed) < 2:
                    await message.reply(f"!set command requires at least one argument.")
                    return True
                type_ = Permission.permissions.get(parsed[1].lower())
                if not type_:
                    await message.reply(f"'{parsed[1]}' is not a valid type.")
                    return True
                if not (type_ & Permission.CONFIGURATION):
                    await message.reply(f"Disabled guilds must register a configuration channel.")
                    return True
                channel = self.get_TextChannel_by_name(message.guild.channels, parsed[2]) if len(parsed) >= 3 else message.channel
                if not channel:
                    await message.reply(f"No text channel named '{parsed[2]}'.")
                    return True
                discord_client.registered_guild.update({message.guild.id: Solver(message.guild.id, channel.id)})
                await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' enabled.")
                return True
    
    @staticmethod
    def get_TextChannel_by_name(channels, name):
        l = [c for c in channels if c.name.startswith(name) and isinstance(c, discord.TextChannel) and c.type == discord.ChannelType.text]
        if not l:
            return None
        l.sort(key = lambda x: len(x.name))
        return l[0]
    
    @staticmethod
    def parse_command_name(command):
        name = ""
        for c in command:
            if c.isspace():
                break
            else:
                name += c
        return name
    
    @staticmethod
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
    
    @staticmethod
    def default():
        return RegisterSingleton

RegisterSingleton = Register()


class Solver(Register):
    """
        Class to contain and concentrate all configurations related to a particular Guild.
        This way the Guild's behaviour may be completely determined thus requests can be appropriately managed and resolved.
    """
    
    def __init__(self, guild_id, channel_id):
        super(Solver, self).__init__()
        self.id = guild_id
        self.permission.add(channel_id, Permission.CONFIGURATION)
    
    def is_configured(self):
        return len(self.permission.channels) > 0
    
    def channel_is_system(self, channel_id):
        return self.permission.get(channel_id) & Permission.SYSTEM
    
    def permission_add(self, channel_id, permission):
        self.permission.add(channel_id, permission)
    
    def permission_delete(self, channel_id = None, permission = None):
        if not channel_id:
            self.permission.clear()
            return
        if not permission:
            self.permission.erase(channel_id)
            return
        self.permission.delete(channel_id, permission)
    
    async def discord_receive(self, message, discord_client):
        content = message.content.strip()
        channel_permission = self.permission.get_enabled(message.channel.id)
        
        if (channel_permission & Permission.CONFIGURATION):
            command = self.parse_command_name(content).lower()
            
            if command == "!set":
                parsed = self.parse_command(content, 3)
                if len(parsed) < 2:
                    await message.reply(f"!set command requires at least one argument.")
                    return True
                type_ = Permission.permissions.get(parsed[1].lower())
                if not type_:
                    await message.reply(f"'{parsed[1]}' is not a valid type.")
                    return True
                if not self.permission.configuration and not (type_ & Permission.CONFIGURATION):
                    await message.reply(f"Disabled guilds must register a configuration channel.")
                    return True
                channel = self.get_TextChannel_by_name(message.guild.channels, parsed[2]) if len(parsed) >= 3 else message.channel
                if not channel:
                    await message.reply(f"No text channel named '{parsed[2]}'.")
                    return True
                self.permission_add(channel.id, type_)
                await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' enabled.")
                return True
            
            if command == "!delete":
                parsed = self.parse_command(content, 3)
                if len(parsed) < 2:
                    await message.reply(f"!delete command requieres at least 1 argument.")
                    return True
                type_ = Permission.permissions.get(parsed[1].lower())
                if not type_:
                    await message.reply(f"{parsed[1]} is not a valid type.")
                    return True
                channel = self.get_TextChannel_by_name(message.guild.channels, parsed[2]) if len(parsed) >= 3 else message.channel
                if not channel:
                    await message.reply(f"There is no text channel named {parsed[2]}.")
                    return True
                self.permission_delete(channel.id, type_)
                if not self.is_configured():
                    discord_client.registered_guild.pop(self.id)
                    await message.reply(f"Guild has been unregistered.")
                elif not self.permission.channels:
                    await message.reply(f"Guild permissions are empty. Please register a configuration channel.")
                elif not self.permission.configuration:
                    await message.reply(f"Guild permissions have been disabled. Please register a configuration channel.")
                else:
                    await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' disabled.")
                return True
            
            if command == "!erase":
                parsed = self.parse_command(content, 2)
                channel = self.get_TextChannel_by_name(message.guild.channels, parsed[1]) if len(parsed) >= 2 else message.channel
                if not channel:
                    await message.reply(f"There is no text channel named {parsed[1]}.")
                    return True
                self.permission_delete(channel.id)
                if not self.is_configured():
                    discord_client.registered_guild.pop(self.id)
                    await message.reply(f"Guild has been unregistered.")
                elif not self.permission.channels:
                    await message.reply(f"Guild permissions have are now empty. Please register a configuration channel.")
                elif not self.permission.configuration:
                    await message.reply(f"Guild has been disabled disabled. Please register a configuration channel.")
                else:
                    await message.reply(f"Channel '{channel.name}' is '{parsed[1]}' disabled.")
                return True
            
            if content.lower() == "!clear":
                self.permission_delete()
                if self.is_configured():
                    await message.reply("Guild permissions have are now empty. Please register a configuration channel.")
                else:
                    discord_client.registered_guild.pop(self.id)
                    await message.reply(f"Guild has been unregistered.")
                return True
            
            if content.lower() == "!unregister":
                discord_client.registered_guild.pop(self.id)
                await message.reply("Guild has been unregistered.")
                return True
            
            if command == "!show":
                parsed = self.parse_command(content, 2)
                channel = self.get_TextChannel_by_name(message.guild.channels, parsed[1]) if len(parsed) >= 2 else message.channel
                if not channel:
                    await message.reply(f"There is no text channel named {parsed[1]}.")
                    return True
                await message.reply(f"'{channel.name}' is '{', '.join(Permission.get_names(self.permission.get(channel.id)))}'.")
                return True
            
            if content.lower() == "!list":
                l = []
                for (i, p) in self.permission.channels.items():
                    l.append(f"'{message.guild.get_channel(i).name}' is '{', '.join(Permission.get_names(p))}'")
                s = '\n'.join(l)
                await message.reply(f"{s}")
                return True
        
        if (channel_permission & Permission.COMMAND):
            command = self.parse_command_name(content).lower()
            if command == "!hello":
                await message.reply("Hello!", mention_author = True)
                return True
        
        if (channel_permission & Permission.READ):
            await message.reply(content, mention_author = True)
            return True
        
        return False
