"""
    https://github.com/Rapptz/discord.py/blob/master/examples/reply.py
"""

# This example requires the 'message_content' privileged intent to function.
# This example requires the 'guilds' privileged intent to function.

import discord
import credential
from solver import Solver
from typing import Literal
from storage import Storage


class MyClient(discord.Client):
    def __init__(self, privileged_id, *args, **kwargs):
        super(MyClient, self).__init__(*args, **kwargs)
        self.privileged_id = privileged_id
        self.tree = discord.app_commands.CommandTree(self, fallback_to_global = False)
        self.system_guild = set(())
        self.registered_guild = {}
        self.storage = Storage("saved", "system", "guilds")
    
    async def on_ready(self):
        self.load_system_guild()
        self.load_registered_guild()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def setup_hook(self):
        await self.tree.sync(guild = None)
    
    async def on_guild_channel_delete(self, channel):
        guild_solver = self.registered_guild.get(channel.guild.id)
        if guild_solver:
            guild_solver.on_guild_channel_delete(channel)
    
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        
        guild_solver = self.registered_guild.get(message.guild.id)
        
        if guild_solver:
            guild_solver.on_message(message)
    
    async def exit(self):
        await self.close()
    
    async def component_install(self, guild, component, user):
        if component.lower() not in ("configuration", "hello", "all"):
            return f"Unknown component '{component}'."
        if guild.id not in self.registered_guild:
            self.registered_guild[guild.id] = Solver(self, guild)
        self.registered_guild.get(guild.id).install(component)
        await self.tree.sync(guild = discord.Object(id = guild.id))
        self.save_registered_guild()
        return f"Component '{component}' installed."
    
    async def component_uninstall(self, guild, component, user):
        if component.lower() not in ("configuration", "hello", "all"):
            return f"Unknown component '{component}'."
        if guild.id not in self.registered_guild:
            return "This guild has no components installed."
        self.registered_guild.get(guild.id).uninstall(component)
        await self.tree.sync(guild = discord.Object(id = guild.id))
        if self.registered_guild.get(guild.id).is_configured():
            self.save_registered_guild()
            return f"Component '{component}' uninstalled."
        self.registered_guild.pop(guild.id)
        self.save_registered_guild()
        return "No installed components left for this guild."
    
    async def component_show(self, guild):
        guild_solver = self.registered_guild.get(guild.id)
        if guild_solver:
            return f"Installed components: {guild_solver.describe()}."
        else:
            return "No components installed for this guild."
    
    def load_system_guild(self):
        self.system_guild.clear()
        try:
            for guild_id in self.storage.load_system_guild()["guilds"]:
                self.tree.add_command(cmdgrp_system, guild = discord.Object(id = guild_id), override = True)
                self.system_guild.add(guild_id)
        except:
            pass
    
    def save_system_guild(self):
        self.storage.save_system_guild({"guilds": list(self.system_guild)})
    
    def load_registered_guild(self):
        self.registered_guild.clear()
        try:
            for guild in self.storage.load_registered_guild()["guilds"]:
                self.registered_guild[guild["guild_id"]] = Solver(self, self.get_guild(guild["guild_id"]))
                if "hello" in guild:
                    if guild["hello"]:
                        self.registered_guild[guild["guild_id"]].install("hello")
                if "configuration" in guild:
                    self.registered_guild[guild["guild_id"]].install("configuration")
                    for channel in guild["configuration"]:
                        self.registered_guild[guild["guild_id"]].permission_add(channel[0], channel[1])
        except:
            pass
    
    def save_registered_guild(self):
        guilds = []
        for (id, solver) in self.registered_guild.items():
            d = {"guild_id": id}
            if solver.hello:
                d["hello"] = True
            if solver.permission:
                d["configuration"] = list(solver.permission.channels.items())
            guilds.append(d)
        self.storage.save_registered_guild({"guilds": guilds})


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = MyClient(credential.USER_ID, intents = intents)

# Global commands generally run on the same level as MyClient.

# System commands group. To be installed in a guild with '/system Install' and execute on MyClient.
cmdgrp_system = discord.app_commands.Group(name = "system", description = "Manage bot.", guild_only = True)

# /system exit
@cmdgrp_system.command(description = "Shut down this bot.")
async def exit(interaction: discord.Interaction):
    await interaction.response.send_message("Terminating...")
    await interaction.client.exit()

# /system reload
@cmdgrp_system.command(description = "Reload bot configuration.")
async def reload(interaction: discord.Interaction):
    interaction.client.load_system_guild()
    interaction.client.load_registered_guild()
    await interaction.response.send_message("Bot configuration reloaded.")

# System commands installation command.
@client.tree.command(description = "Install system commands.", guild = None)
async def system(interaction: discord.Interaction, type: Literal["Install", "Uninstall"]):
    if interaction.user.id != interaction.client.privileged_id:
        await interaction.response.send_message(f"You do not have authorization to modify this component.")
        return
    if type.lower() == "install":
        if interaction.guild_id in interaction.client.system_guild:
            await interaction.response.send_message("System already installed.")
        else:
            guild_target = discord.Object(id = interaction.guild_id)
            interaction.client.tree.add_command(cmdgrp_system, guild = guild_target, override = True)
            await interaction.client.tree.sync(guild = guild_target)
            interaction.client.system_guild.add(interaction.guild_id)
            await interaction.response.send_message("System commands installed.")
        interaction.client.save_system_guild()
        return
    if type.lower() == "uninstall":
        if interaction.guild_id in interaction.client.system_guild:
            guild_target = discord.Object(id = interaction.guild_id)
            interaction.client.tree.remove_command("cmdgrp_system", guild = guild_target)
            await interaction.client.tree.sync(guild = guild_target)
            interaction.client.system_guild.discard(interaction.guild_id)
            await interaction.response.send_message("System commands uninstalled.")
        else:
            await interaction.response.send_message("System is not installed.")
        interaction.client.save_system_guild()
        return

# Component installation group. Components are held inside a guild Solver.
cmdgrp_install = discord.app_commands.Group(name = "component", description = "Manage bot components.", guild_only = True)

# /install add '<component>'
@cmdgrp_install.command(description = "Add a bot component to this guild.")
async def add(interaction: discord.Interaction, component: Literal["Configuration", "Hello", "All"]):
    await interaction.response.send_message(await interaction.client.component_install(interaction.guild, component, interaction.user))
    print(f"Install Add command called. Guild: '{interaction.guild.name}' ({interaction.guild_id}). Component '{component}'.")

# /install delete '<component>'
@cmdgrp_install.command(description = "Delete a bot component from this guild.")
async def delete(interaction: discord.Interaction, component: Literal["Configuration", "Hello", "All"]):
    await interaction.response.send_message(await interaction.client.component_uninstall(interaction.guild, component, interaction.user))
    print(f"Install Delete command called. Guild: '{interaction.guild.name}' ({interaction.guild_id}). Component '{component}'.")

# /install show
@cmdgrp_install.command(description = "Show guild installed bot components.")
async def show(interaction: discord.Interaction):
    await interaction.response.send_message(await interaction.client.component_show(interaction.guild))
    print(f"Show command called. Guild: '{interaction.guild.name}' ({interaction.guild_id}).")


client.tree.add_command(cmdgrp_install, guild = None, override = True)

client.run(credential.TOKEN)
