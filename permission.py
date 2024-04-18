import discord
from typing import Literal

class Component(object):
    async def install(self, client, guild_id):
        return self
    
    async def uninstall(self, client, guild_id):
        return None


# Component commands run on MyClient as every command, but may be implemented to extend Solver and operate on Components.

# Permission management group.
cmdgrp_configuration = discord.app_commands.Group(name = "configure", description = "Configure channel types.", guild_only = True)

@cmdgrp_configuration.command(description = "Add a channel permission.")
async def add(interaction: discord.Interaction, channel: discord.TextChannel, type: Literal["Read", "Write"]):
    if not isinstance(channel, discord.TextChannel) or channel.type != discord.ChannelType.text:
        await interaction.response.send_message("Could not add. Channel must be a plain text channel.")
        return
    permission = Permission.permissions.get(type.lower())
    if not permission:
        await interaction.repsonse.send_message(f"Could not add. Invalid type '{type}'.")
        return
    interaction.client.registered_guild[interaction.guild_id].permission_add(channel.id, permission)
    await interaction.repsonse.send_message(f"{channel.name} is '{type}' enabled.")

@cmdgrp_configuration.command(description = "Delete a channel permission.")
async def delete(interaction: discord.Interaction, channel: discord.TextChannel, type: Literal["Read", "Write", "All"]):
    if not isinstance(channel, discord.TextChannel) or channel.type != discord.ChannelType.text:
        await interaction.response.send_message("Could not delete. Channel must be a plain text channel.")
        return
    permission = Permission.permissions.get(type.lower())
    if not permission:
        await interaction.response.send_message(f"Could not delete. Invalid type '{type}'.")
        return
    interaction.client.registered_guild[interaction.guild_id].permission_delete(channel.id, permission)
    await interaction.response.send_message(f"{channel.name} is '{type}' disabled.")

@cmdgrp_configuration.command(description = "Show all assigned channel permissions.")
async def show(interaction: discord.Interaction):
    await interaction.response.send_message(interaction.client[interaction.guild_id].permission_show(interaction.guild))


class Permission(Component):
    """
        Hold Guild permissions on a per channel basis.
    """
    
    NONE            = 0x00
    READ            = 0x01
    WRITE           = 0x02
    ALL             = NONE | READ | WRITE
    
    permissions = {
        "read":     READ,
        "write":    WRITE,
        "all":      ALL,
    }
    
    def __init__(self):
        super(Permission, self).__init__()
        self.channels = {}
    
    async def install(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.add_command(cmdgrp_configuration, guild = guild_target)
        await client.tree.sync(guild = guild_target)
        self.permission.clear()
        return self
    
    async def uninstall(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.remove_command(cmdgrp_configuration, guild = guild_target)
        await client.tree.sync(guild = guild_target)
        self.permission.clear()
        return None
    
    @classmethod
    async def install(cls, client, guild_id):
        x = cls()
        return await x.install(client, guild_id)
    
    def get(self, channel_id):
        return self.channels.get(channel_id, Permission.NONE)
    
    def add(self, channel_id, permission):
        self.channels.update({channel_id: self.get(channel_id) | permission})
    
    def delete(self, channel_id, permission):
        if channel_id in self.channels:
            p = self.get(channel_id) & ~permission
            if p:
                self.channels.update({channel_id: p})
            else:
                self.channels.pop(channel_id)
    
    def erase(self, channel_id):
        self.channels.pop(channel_id)
    
    def clear(self):
        self.channels.clear()
    
    def get_channel_write(self):
        l = [i for (i, p) in self.channels.items() if (p & Permission.WRITE)]
        if l:
            return l[0]
        return None
    
    def get_names(self):
        l = []
        for (i, p) in self.channels.get_all():
            l.append((i, ', '.join([k for (k, v) in Permission.permissions.items() if (p & v)])))
        return l

# Basic 'hello' command.
@discord.app_commands.command(description = "Say Hello.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}")


class Hello(Component):
    def __init__(self):
        super(Hello, self).__init__()
    
    async def install(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.add_command(hello, guild = guild_target)
        await client.tree.sync(guild = guild_target)
        return self
    
    async def uninstall(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.remove_command(hello, guild = guild_target)
        await client.tree.sync(guild = guild_target)
        return None
    
    @classmethod
    async def install(cls, client, guild_id):
        x = cls()
        return await x.install(client, guild_id)
