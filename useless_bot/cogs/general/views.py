import discord


class WarnLimit(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=30)
        self.user = user
        self.click = False

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.primary)
    async def kick(self, _: discord.ui.Button, interaction: discord.Interaction):
        """Kick the user if this button is pressed"""
        await self.user.kick(reason="Warn limit exceeded")
        await interaction.response.send_message("Banned", ephemeral=True)
        self.click = True
        self.stop()

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.red)
    async def ban(self, _: discord.ui.Button, interaction: discord.Interaction):
        """Ban the user if this button is pressed"""
        await self.user.ban(reason="Warn limit exceeded")
        await interaction.response.send_message("Banned", ephemeral=True)
        self.click = True
        self.stop()
