import nextcord


class WarnLimit(nextcord.ui.View):
    def __init__(self, user: nextcord.Member):
        super().__init__(timeout=30)
        self.user = user
        self.click = False

    @nextcord.ui.button(label="Kick", style=nextcord.ButtonStyle.primary)
    async def kick(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Kick the user if this button is pressed"""
        await self.user.kick(reason="Warn limit exceeded")
        await interaction.response.send_message("Banned", ephemeral=True)
        self.click = True
        self.stop()

    @nextcord.ui.button(label="Ban", style=nextcord.ButtonStyle.red)
    async def ban(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Ban the user if this button is pressed"""
        await self.user.ban(reason="Warn limit exceeded")
        await interaction.response.send_message("Banned", ephemeral=True)
        self.click = True
        self.stop()
