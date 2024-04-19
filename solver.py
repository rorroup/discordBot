import discord
from permission import Permission, Hello
from typing import Literal


class Solver(object):
    """
        Class to contain and concentrate all configurations related to a particular Guild.
        This way the Guild's behaviour may be completely determined thus requests can be appropriately managed and resolved.
        Slash commands are generally solved within the command itself. They may configure the Solver to behave differently.
    """
    
    def __init__(self, bot, guild):
        self.bot = bot
        self.id = guild.id
        self.permission = None
        self.hello = None
    
    async def install(self, component, installation = False):
        if not self.permission and (component.lower() == "configure" or component.lower() == "all"):
            self.permission = Permission()
            if installation:
                await self.permission.install(self.bot, self.id)
        if not self.hello and (component.lower() == "hello" or component.lower() == "all"):
            self.hello = Hello()
            if installation:
                await self.hello.install(self.bot, self.id)
    
    async def uninstall(self, component):
        if self.permission and (component.lower() == "configure" or component.lower() == "all"):
            self.permission = await self.permission.uninstall(self.bot, self.id)
        if self.hello and (component.lower() == "hello" or component.lower() == "all"):
            self.hello = await self.hello.uninstall(self.bot, self.id)
    
    def is_configured(self):
        return self.permission != None or self.hello != None
    
    def describe(self):
        s = ""
        if self.permission:
            s += "Permissions:\n" + self.permission_show(self.bot.get_guild(self.id))
        if self.hello:
            s += "Slash Commands:\nHello"
        return s
    
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
    
    def permission_show(self):
        l = []
        l.append(f"{self.bot.get_guild(self.id).get_channel(i).name} is '{p}'" for (i, p) in self.permission.get_names())
        return '\n'.join(l)
    
    async def on_guild_channel_delete(self, channel):
        if self.permission:
            self.permission_delete(channel.id)
    
    async def on_message(self, message):
        if self.permission:
            content = message.content.strip()
            
            channel_permission = self.permission.get(message.channel.id)
        
            if (channel_permission & Permission.READ):
                await message.reply("I have read your message.", mention_author = True)
                
                channel_write_id = self.permission.get_channel_write()
                if channel_write_id:
                    message.guild.get_channel(channel_write_id).send(content)
                
                return True
        
        return False
