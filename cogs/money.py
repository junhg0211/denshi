from discord import Interaction, User, Embed
from discord.app_commands import command, Group
from discord.ext.commands import Bot, Cog

import bank


UNIT = bank.get_unit()


class SettleSession:
    def __init__(self, dealer: User, multiplier: float):
        self.dealer = dealer
        self.multiplier = multiplier
        self.values: dict[int, tuple[float, User]] = dict()

    def join(self, member: User, value: float):
        self.values[member.id] = (value, member)

    def get_total(self) -> float:
        return sum(map(lambda x: x[0], self.values.values()))

    def get_moxes(self) -> dict[int, float]:
        result = dict()
        if len(self.values) <= 0:
            return result

        total = self.get_total()
        average = total / len(self.values)
        for value, member in self.values.values():
            result[member.id] = self.multiplier * (value - average)
        return result

    def get_embed(self) -> Embed:
        embed = Embed(title=f"`{self.dealer.name}`님의 정산 세션")
        embed.add_field(name="배수", value=f"{self.multiplier:,}배", inline=False)

        participants = list()
        moxes = self.get_moxes()
        for value, participant in sorted(
            self.values.values(), reverse=True, key=lambda x: x[0]
        ):
            mox = moxes.get(participant.id, None)
            participants.append(f"* {participant.mention}, {value:,}: {mox:,} {UNIT}")
        if participants:
            participants = "\n".join(participants)
        else:
            participants = "(없음)"
        embed.add_field(name="참여자", value=participants, inline=False)

        return embed

    def leave(self, member_id: int):
        self.values.pop(member_id)


class MoneyCog(Cog):
    settle_group = Group(name="정산", description="정산 세션을 시작합니다.")

    def __init__(self, bot: Bot):
        self.bot = bot

        self.sessions = dict()

    @command(name="돈", description="소지금을 확인합니다.")
    async def money(self, ctx: Interaction):
        having = bank.get_money(ctx.user.id)
        await ctx.response.send_message(
            f"__{ctx.user.display_name}__님의 소지금은 __**{having:,} {UNIT}**__입니다.",
            ephemeral=True,
        )

    @settle_group.command(name="시작", description="정산 세션을 시작합니다.")
    async def start(self, ctx: Interaction, multiplier: float):
        # check not duplicated
        if ctx.user.id in self.sessions:
            await ctx.response.send_message(
                ":x: 이미 자신을 딜러로 하여 진행중인 세션이 있습니다.\n"
                "* `/정산 정보`를 통해 정산 세션 정보를 확인하고,\n"
                "* `/정산 확정`를 통해 정산을 확정(종료),\n"
                "* `/정산 취소`을 통해 정산을 취소할 수 있습니다.",
                ephemeral=True,
            )
            return

        # start session
        assert isinstance(ctx.user, User)
        self.sessions[ctx.user.id] = SettleSession(ctx.user, multiplier)
        await ctx.response.send_message(
            f"{ctx.user.mention}님이 배수를 __**{multiplier:,}배수**__로 하여 "
            f"정산 세션을 시작했습니다.\n"
            f"* 정산 세션에는 `/정산 참여` 명령어로 참여하고,\n"
            f"* `/정산 종료` 명령어로 정산 세션을 확정(종료)할 수 있습니다.\n"
            f"정산 세션은 봇이 종료되면 __돈을 지급하지 않고 초기화__되므로 빠르게 진행해주세요."
        )

    @settle_group.command(name="정보", description="정산 세션 정보를 확인합니다.")
    async def info(self, ctx: Interaction, dealer: User, ephemeral: bool = True):
        # check session existing
        if dealer.id not in self.sessions:
            await ctx.response.send_message(
                f":x: {dealer.mention}님이 딜러인 정산 세션이 존재하지 않습니다.",
                ephemeral=True,
            )
            return

        session = self.sessions[dealer.id]
        embed = session.get_embed()
        await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

    @settle_group.command(name="참여", description="정산 세션에 참여합니다.")
    async def join(self, ctx: Interaction, dealer: User, value: float):
        # check session existing
        if dealer.id not in self.sessions:
            await ctx.response.send_message(
                f":x: {dealer.mention}님이 딜러인 정산 세션이 존재하지 않습니다.",
                ephemeral=True,
            )
            return

        session = self.sessions[dealer.id]
        session.join(ctx.user, value)

        embed = session.get_embed()
        await ctx.response.send_message(
            f"{ctx.user.mention}님이 `{dealer.name}`님의 정산에 참여했습니다.",
            embed=embed,
        )

    @settle_group.command(name="퇴장", description="정산 세션에서 퇴장합니다.")
    async def leave(self, ctx: Interaction, dealer: User):
        # check session existing
        if dealer.id not in self.sessions:
            await ctx.response.send_message(
                f":x: {dealer.mention}님이 딜러인 정산 세션이 존재하지 않습니다.",
                ephemeral=True,
            )
            return

        session = self.sessions[dealer.id]
        # check if in it
        if ctx.user.id not in session.values:
            await ctx.response.send_message(
                f":x: 이 정산 세션에 참여하고 있지 않습니다.", ephemeral=True
            )
            return

        session.leave(ctx.user.id)

        embed = session.get_embed()
        await ctx.response.send_message(
            f"{ctx.user.mention}님이 `{dealer.name}`님의 정산에서 퇴장했습니다.",
            embed=embed,
        )

    @settle_group.command(name="취소", description="정산 세션을 취소합니다.")
    async def cancel(self, ctx: Interaction):
        # check session existing
        if ctx.user.id not in self.sessions:
            await ctx.response.send_message(
                f":x: {ctx.user.mention}님이 딜러인 정산 세션이 존재하지 않습니다.",
                ephemeral=True,
            )
            return

        self.sessions.pop(ctx.user.id)
        await ctx.response.send_message(
            f"{ctx.user.mention}님이 정산 세션을 취소했습니다."
        )

    @settle_group.command(name="종료", description="정산 세션을 종료합니다.")
    async def confirm(self, ctx: Interaction):
        # check session existing
        if ctx.user.id not in self.sessions:
            await ctx.response.send_message(
                f":x: {ctx.user.mention}님이 딜러인 정산 세션이 존재하지 않습니다.",
                ephemeral=True,
            )
            return

        session = self.sessions[ctx.user.id]

        if len(session.values) <= 1:
            await ctx.response.send_message(
                f"참여자가 1명 이하이므로 정산 없이 정산 세션이 종료되었습니다.",
                embed=session.get_embed(),
            )
            return

        logs = list()
        moxes = session.get_moxes()
        for user_id, mox in moxes.items():
            mox = round(mox)
            having = bank.get_money(user_id)
            if having + mox >= 0:
                bank.set_money(user_id, having + mox)
            else:
                bank.set_money(user_id, 0)

            user = self.bot.get_user(user_id)
            if user is None:
                continue

            if mox >= 0:
                logs.append(
                    f"* {user.mention}님에게 __{mox:,} {UNIT}__를 지급했습니다."
                )
            else:
                logs.append(
                    f"* {user.mention}님에게서 __{-mox:,} {UNIT}__를 징수했습니다."
                )

        logs = "\n".join(logs)
        self.sessions.pop(ctx.user.id)
        await ctx.response.send_message(
            f"{ctx.user.mention}님의 정산 세션을 마무리했습니다.\n{logs}",
            embed=session.get_embed(),
        )

    @command(name="송금", description="다른 사람에게 돈을 송금합니다.")
    async def transfer(self, ctx: Interaction, to: User, amount: int):
        if amount < 0:
            await ctx.response.send_message(
                "0원 미만은 송금할 수 없습니다.", ephemeral=True
            )
            return

        me_having = bank.get_money(ctx.user.id)
        """
        if amount > me_having:
            await ctx.response.send_message(
                "가지고 있는 돈보다 더 많이 송금할 수 없습니다.", ephemeral=True
            )
            return
        """

        to_having = bank.get_money(to.id)
        bank.set_money(ctx.user.id, me_having - amount)
        bank.set_money(to.id, to_having + amount)
        await ctx.response.send_message(
            f"{ctx.user.mention}님이 {to.mention}님에게 __**{amount:,} {UNIT}**__을(를) 송금했습니다."
        )


async def setup(bot: Bot):
    await bot.add_cog(MoneyCog(bot))
