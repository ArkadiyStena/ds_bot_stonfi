import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands.context import Context

from time import sleep
from multiprocessing import Process
from os import remove

from config import *
from functions import *


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="?", intents=intents)

    # то что ниже надо будет раскомментить если вы будете настраивать нового бота/сервер
    # async def setup_hook(self):
    #     await self.tree.sync(guild=discord.Object(id=GUILD_ID))
    #     print(f"Synced slash commands for {self.user}.")


bot = Bot()


@bot.hybrid_command(name="connect", with_app_command=True, description="Connect your Tonkeeper")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def connect(ctx: Context):
    # print(bot.guilds)
    # print(list(map(lambda t: (t.name, t.id), ctx.guild.roles)))
    await ctx.defer(ephemeral=True)
    all_wallets = get_wallets_dict()
    author = ctx.author.__str__()
    last_refresh = last_refreshes.get(author, 0)

    if last_refresh > int(time()) - 30:
        await ctx.reply(f"Don't flood! Try again in {30 - int(time()) + last_refresh} seconds!")
    elif author in all_wallets:
        await ctx.reply(f"Your connected wallet:\n\n{all_wallets[ctx.author.__str__()]}\n\n"
                        f"To refresh data about your roles use /refresh")
    else:
        url, qr, connector = ton_connect()
        await ctx.reply(f"Your personal url for connecting Tonkeeper:\n {url}\n\n"
                        f"After finishing connection send command /refresh to get roles"
                        f"\nYou have only 3 minutes for connecting your wallet.",
                        file=discord.File(f"qr{qr}.png"))
        remove(f"qr{qr}.png")
        p = Process(target=get_address, args=(connector, author, ctx.author.id))
        p.start()


@bot.hybrid_command(name="refresh", with_app_command=True, description="Update info about your wallet")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def refresh(ctx: Context):
    await ctx.defer(ephemeral=True)
    author = ctx.author.__str__()
    all_wallets = get_wallets_dict()
    wallet = all_wallets.get(author, None)
    last_refresh = last_refreshes.get(author, 0)

    if last_refresh > int(time()) - 30:
        await ctx.reply(f"Don't flood! Try again in {30 - int(time()) + last_refresh} seconds!")
    elif not wallet:
        await ctx.reply("You haven't connected your wallet yet. Try /connect command")
    else:
        reply_text = f"Your wallet:\n\n{wallet}\n\n"
        msg = await ctx.reply(reply_text + "Checking your wallet...")

        user_roles = list(map(lambda t: (t.name, t.id), ctx.author.roles[1:]))

        possible_roles, conditions = check_wallet(wallet)
        reply_text += "Holding NFTs:"
        j = 0
        for i in conditions:
            if j == 3:
                reply_text += "\nMaking swaps:"
            reply_text += ("\n✅ " if conditions[i] else "\n❌ ") + i
            j += 1

        new_roles = []
        for role in possible_roles:
            if role not in user_roles:
                new_roles.append(role[0])
                await ctx.author.add_roles(ctx.guild.get_role(role[1]))
                # print(role[1], 'to user', ctx.author, 'added')

        if not new_roles and not all(conditions.values()):
            reply_text += "\n\nNo new roles found :("
        elif not new_roles:
            reply_text += "\n\nYou already have all the possible roles"
        else:
            reply_text += f"\n\nCongratulations! You got some new roles: {', '.join(new_roles)}!"
        await msg.edit(content=reply_text)
        last_refreshes[author] = int(time())


@bot.hybrid_command(name="disconnect", with_app_command=True, description="Disconnect wallet")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def disconnect(ctx: Context):
    await ctx.defer(ephemeral=True)
    all_wallets = get_wallets_dict()
    if ctx.author.__str__() in all_wallets:
        text = ''
        with open("wallets.csv") as f:
            t1 = f.read()
            t2 = t1.find(ctx.author.__str__())
            t3 = t1[t2:].find('\n')
            if t3 == -1:
                text += t1[:t2 - 1]
            else:
                text += t1[:t2 - 1] + t1[t2 + t3:]
        with open("wallets.csv", 'w') as f:
            f.write(text)
        await ctx.reply("Wallet successfully disconnected")
    else:
        await ctx.reply("You haven't connected wallet yet")


@bot.hybrid_command(name="refresh_all", with_app_command=True, description="Update info about all wallets")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def refresh_all(ctx: Context):
    await ctx.defer(ephemeral=True)
    user_roles = list(map(lambda t: t.name, ctx.author.roles[1:]))
    if "moderator" not in user_roles and "admin" not in user_roles and "STON.PRO" not in user_roles:
        await ctx.reply("You are not allowed to use this command")
        return

    f = open("wallets.csv")
    data = f.read().split('\n')[1:]
    f.close()
    deleted_roles = {}
    for i in range(len(data)):
        user_nick, user_id, wallet = data[i].split(';')
        user_roles = list(map(lambda t: (t.name, t.id), (await ctx.guild.fetch_member(user_id)).roles[1:]))
        possible_roles = check_wallet(wallet)[0]
        deleted_roles[user_nick] = []

        for role in user_roles:
            if role[0] in ROLE_IDS and role not in possible_roles:
                deleted_roles[user_nick].append(role[0])
                await ctx.author.remove_roles(ctx.guild.get_role(role[1]))

    await ctx.reply(f"checked {len(data)} wallets\n\nMore info about deleted roles:\n{deleted_roles}")
    # print(deleted_roles)


if __name__ == "__main__":
    last_refreshes = {}
    bot.run(TOKEN)
