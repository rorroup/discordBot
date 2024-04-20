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
    
    def install(self, component):
        if not self.permission and (component.lower() == "configuration" or component.lower() == "all"):
            self.permission = Permission(self.bot, self.id)
        if not self.hello and (component.lower() == "hello" or component.lower() == "all"):
            self.hello = Hello(self.bot, self.id)
    
    def uninstall(self, component):
        if self.permission and (component.lower() == "configuration" or component.lower() == "all"):
            self.permission.uninstall(self.bot, self.id)
            self.permission = None
        if self.hello and (component.lower() == "hello" or component.lower() == "all"):
            self.hello.uninstall(self.bot, self.id)
            self.hello = None
    
    def is_configured(self):
        return self.permission != None or self.hello != None
    
    def describe(self):
        s = ""
        if self.permission:
            s += "Permissions:\n" + self.permission_show()
        if self.hello:
            s += "Slash Commands:\nHello"
        return s
    
    def permission_add(self, channel_id, permission):
        self.permission.add(channel_id, permission)
        self.bot.save_registered_guild()
    
    def permission_delete(self, channel_id = None, permission = None):
        if not channel_id:
            self.permission.clear()
            self.bot.save_registered_guild()
            return
        if not permission:
            self.permission.erase(channel_id)
            self.bot.save_registered_guild()
            return
        self.permission.delete(channel_id, permission)
        self.bot.save_registered_guild()
    
    def permission_show(self):
        if self.permission:
            l = [f"{self.bot.get_guild(self.id).get_channel(i).name} is '{p}'" for (i, p) in self.permission.get_names()]
            return '\n'.join(l)
        return ""
    
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
