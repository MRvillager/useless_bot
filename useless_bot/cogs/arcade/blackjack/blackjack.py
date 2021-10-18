import logging
from random import shuffle
from typing import Union, Optional

from nextcord import ButtonStyle, Interaction, Message, Embed, Member, User
from nextcord.ext.commands import Context
from nextcord.ui import Button, View

from useless_bot.core.bank_core import BankCore
from useless_bot.core.errors import BalanceOverLimitError, BalanceUnderLimitError
from .objects import Dealer
from .objects import Status, Player

logger = logging.getLogger("useless_bot.cog.arcade.blackjack")


class HitButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Hit", row=0, disabled=True)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view
        try:
            player: Player = view.players[interaction.user.id]
        except KeyError:
            await interaction.response.send_message("You are not playing in this session", ephemeral=True)
        else:
            if player.status == Status.Stand:  # if the player is standing, he cannot get new cards
                await interaction.response.send_message("You are in stand. You must wait the end of the game",
                                                        ephemeral=True)
            else:
                player.append(self.view.deck.pop())

        await view.check_game(interaction)


class StandButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Stand", row=0, disabled=True)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view
        try:
            player: Player = view.players[interaction.user.id]
        except KeyError:
            await interaction.response.send_message("You are not playing in this session", ephemeral=True)
        else:
            player.status = Status.Stand

        await view.check_game(interaction)


class JoinButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(label="Join", row=1)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view

        if interaction.user.id not in view.players.keys():
            player: Player = Player.from_discord(interaction.user)
            view.players[interaction.user.id] = player
            await view.start_page(interaction)


class LeaveButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(label="Leave", row=1)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view

        try:
            del view.players[interaction.user.id]
            content = "You have left the session"
        except KeyError:
            content = "You are not playing in the session"

        await interaction.response.send_message(content, ephemeral=True)

        if len(view.players) == 0:
            await interaction.message.delete(delay=3)
            view.stop()
        else:
            if interaction.user == view.author:
                view.author = view.bot.fetch_user(list(view.players.keys())[0])
            await view.start_page(interaction)


class CancelButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(label="Cancel Game", row=1)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view
        if interaction.user == view.author:
            await interaction.response.send_message("Cancelling", ephemeral=True)
            await interaction.message.delete(delay=3)
            view.stop()
        else:
            await interaction.response.send_message("You are not the owner of this session", ephemeral=True)


class StartButton(Button['Blackjack']):
    def __init__(self):
        super().__init__(style=ButtonStyle.primary, label="Start Game", row=2)

    # This function is called whenever this particular button is pressed
    async def callback(self, interaction: Interaction):
        if self.view is None:
            return

        view: Blackjack = self.view
        if interaction.user == view.author:
            await view.start(interaction)
        else:
            await interaction.response.send_message("You are not the owner of this session", ephemeral=True)


class Blackjack(View):
    deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] * 4
    ending = False

    def __init__(self, ctx: Context, bank: BankCore, game_cost: int = 5):
        super().__init__()

        self.bot = ctx.bot
        self.bank = bank
        self.bet = game_cost
        self.max_players = 4

        self.author: Union[User, Member] = ctx.author
        self.users: dict[str, tuple[str, int]] = {}

        shuffle(self.deck)

        self.dealer = Dealer()
        self.players: dict[int, Player] = {self.author.id: Player.from_discord(self.author)}

        # buttons
        self.add_item(HitButton())
        self.add_item(StandButton())
        self.add_item(JoinButton())
        self.add_item(LeaveButton())
        self.add_item(CancelButton())
        self.add_item(StartButton())

    async def on_timeout(self):
        self.stop()

    async def start_page(self, interaction: Optional[Interaction] = None, message: Optional[Message] = None):
        embed = Embed()
        embed.title = "Blackjack"
        embed.description = (
            f"The session owner is {self.author.name}"
        )
        for i, (user_id, player) in enumerate(self.players.items()):
            embed.add_field(name=f"Player {i + 1}", value=f"{player.name} - <@{user_id}>\nBet: {player.bet}",
                            inline=False)

        if interaction is None:
            await message.edit(embed=embed)
        elif message is None:
            await interaction.message.edit(embed=embed)
        else:
            raise AttributeError

    # noinspection PyUnresolvedReferences
    async def start(self, interaction: Interaction):
        # enable actions
        for i in range(3):
            self.remove_item(self.children[i])

        for i in range(3, 7):
            self.children[i].disabled = True

        # update view
        await interaction.response.edit_message(view=self)

        # deal the cards
        self.deal()

        # show game page
        await self.game_page(interaction)

    def deal(self):
        for _ in range(2):
            self.dealer.append(self.deck.pop())

            for player in self.players.values():
                player.append(self.deck.pop())

    async def check_game(self, interaction: Interaction):
        for player in self.players.values():
            if player.status == Status.Continue:
                await self.game_page(interaction)
                return

        # set the game status to ending
        self.ending = True

        # disable all buttons
        for i in range(3):
            # noinspection PyUnresolvedReferences
            self.children[i].disabled = True

        # update view
        await interaction.response.edit_message(view=self)

        # when all players have played
        # give cards to the dealer
        while self.dealer.hand_value < 17:
            self.dealer.append(self.deck.pop())

        # refresh status for dealer and all players
        for player in self.players.values():
            self._check_final_player_status(player=player)

        # elaborate bets
        self.bets()

        # refresh game page
        await self.game_page(interaction)

        # stop game
        self.stop()

    def bets(self):
        for user_id, player in self.players.items():
            player_status = player.status

            try:
                if player_status == Status.Win:
                    self.bank.deposit(user=user_id, value=self.bet * 2)
                elif player_status in (Status.Lost, Status.Bust):
                    self.bank.withdraw(user=user_id, value=self.bet)
            except (BalanceUnderLimitError, BalanceOverLimitError):
                continue

    async def game_page(self, interaction: Interaction):
        """Update the embed with the current game status"""
        embed = Embed()
        embed.title = "Blackjack"
        embed.description = "Game started"

        # dealer field
        if self.ending:
            hand = " + ".join(self.dealer.hand)  # 10 + 10 + 10
            hand_str = f"{hand} = {self.dealer.hand_value}\n"  # 10 + 10 + 10 = 30\n
        else:
            hand = list(self.dealer.hand)
            hand_str = f"{hand[0]} + ? = ?\n"  # 10 + ? = ?\nPlay

        embed.add_field(name="Dealer", value=hand_str, inline=False)

        # players fields
        for user in self.players.values():
            hand = " + ".join(user.hand)
            text = f"{hand} = {user.hand_value}"
            text += f"\n{user.status.name}"

            embed.add_field(
                name=f"{user.name}",
                value=text,
                inline=False,
            )

        await interaction.message.edit(embed=embed)

    def _check_final_player_status(self, player: Player):
        points = player.hand_value

        if self.ending and player.status != Status.Bust:
            dealer_points = self.dealer.hand_value

            if self.dealer.status == Status.Bust:
                player.status = Status.Win
            elif dealer_points > points:
                player.status = Status.Lost
            elif dealer_points == points:
                player.status = Status.Push
            elif dealer_points < points:
                player.status = Status.Win
