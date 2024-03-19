from asyncio import run
from discord import Intents
from discord.ext.commands import Bot
from os import listdir

from const import get_secret

bot = Bot("$$", intents=Intents.default())


@bot.event
async def on_ready():
    await bot.tree.sync()


async def load_cogs():
    for filename in listdir("./cogs"):
        if not filename.endswith(".py"):
            continue
        await bot.load_extension(f"cogs.{filename[:-3]}")
        print(f"코그 cogs.{filename[:-3]}이/가 로드되었습니다.")


def main():
    run(load_cogs())

    # start bot
    token = get_secret("bot_token")
    if token is None:
        print("토큰이 발견되지 않았습니다.")
        return
    bot.run(token)


if __name__ == "__main__":
    main()
