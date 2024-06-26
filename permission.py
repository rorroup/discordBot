import discord
from typing import Literal


# Component commands run on MyClient as every command, but may be implemented to extend Solver and operate on Components.

# Permission management group.
cmdgrp_configuration = discord.app_commands.Group(name = "configure", description = "Configure channel types.", guild_only = True)

@cmdgrp_configuration.command(description = "Add a channel permission.")
async def add(interaction: discord.Interaction, channel: discord.TextChannel, type: Literal["Read", "Write"]):
    if not isinstance(channel, discord.TextChannel) or channel.type != discord.ChannelType.text:
        await interaction.response.send_message("Could not add. Channel must be a plain text channel.")
        return
    permission = Permission.permissions_all.get(type.lower())
    if not permission:
        await interaction.response.send_message(f"Could not add. Invalid type '{type}'.")
        return
    interaction.client.registered_guild[interaction.guild_id].permission_add(channel.id, permission)
    await interaction.response.send_message(f"{channel.name} is '{type}' enabled.")

@cmdgrp_configuration.command(description = "Delete a channel permission.")
async def delete(interaction: discord.Interaction, channel: discord.TextChannel, type: Literal["Read", "Write", "All"]):
    if not isinstance(channel, discord.TextChannel) or channel.type != discord.ChannelType.text:
        await interaction.response.send_message("Could not delete. Channel must be a plain text channel.")
        return
    permission = Permission.permissions_all.get(type.lower())
    if not permission:
        await interaction.response.send_message(f"Could not delete. Invalid type '{type}'.")
        return
    interaction.client.registered_guild[interaction.guild_id].permission_delete(channel.id, permission)
    await interaction.response.send_message(f"{channel.name} is '{type}' disabled.")

@cmdgrp_configuration.command(description = "Show all assigned channel permissions.")
async def show(interaction: discord.Interaction):
    await interaction.response.send_message(interaction.client.registered_guild[interaction.guild_id].permission_show())


class Permission(object):
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
    }
    
    permissions_all = dict(permissions)
    permissions_all.update({"all": ALL,})
    
    def __init__(self, client, guild_id):
        super(Permission, self).__init__()
        self.channels = {}
        client.tree.add_command(cmdgrp_configuration, guild = discord.Object(id = guild_id), override = True)
    
    def uninstall(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.remove_command("configure", guild = guild_target)
        self.channels.clear()
    
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
        for (i, p) in self.channels.items():
            l.append((i, ', '.join([k for (k, v) in Permission.permissions.items() if (p & v)])))
        return l

# Basic 'hello' command.
@discord.app_commands.command(description = "Say Hello.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}")


class Hello(object):
    def __init__(self, client, guild_id):
        super(Hello, self).__init__()
        client.tree.add_command(hello, guild = discord.Object(id = guild_id), override = True)
    
    def uninstall(self, client, guild_id):
        guild_target = discord.Object(id = guild_id)
        client.tree.remove_command("hello", guild = guild_target)
