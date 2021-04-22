import discord
import os
import asyncio
import youtube_dl
from youtube_dl import YoutubeDL
from discord.ext import commands
from config import settings
from discord.utils import get
from ttt import TicTacToe
import random
from riotwatcher import LolWatcher, ApiError
import pandas as pd
# определяем префикс и настройки
bot = commands.Bot(command_prefix = settings['prefix'])
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'False'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
svc = {}
bot.remove_command('help')
api_key = 'RGAPI-2a6fc68a-8e58-41f3-8b34-683e3c8f7697'
watcher = LolWatcher(api_key)

@bot.command()
async def help(param):
    embed = discord.Embed(title="Помощь", description="?join - присоединение бота к голосовому каналу\n ?leave - отключение от голосового чата\n ?play и ссылка - команда чтобы проиграть музыку в голосовом канале\n ?tictactoe и упоминуть кого-нибудь - команда чтобы сыграть с ним в крестики-нолики. Чтобы ставить крестик или нолик используйте команду ?place 'строка', 'колонка'", color=0xffffff)
    await param.send(embed=embed)
@bot.command()
async def hello(ctx):
    author = ctx.message.author
    await ctx.send(f'Hello, {author.mention}!')

@bot.command()
@commands.has_permissions(administrator = True)
async def clear(ctx, amount = 10):
    await ctx.channel.purge( limit = amount)

@bot.command()
@commands.has_permissions(administrator = True)
async def kick(ctx, member: discord.Member, *, reason = None ):
    await member.kick(reason = reason)

@bot.command()
@commands.has_permissions(administrator = True)
async def ban(ctx, member: discord.Member, *, reason = None ):
    await member.ban(reason = reason)

@bot.command()
async def pardon(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')
    for ban_entry in banned_users:
        user = ban_entry.banned_users
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
              
@bot.command()
@commands.has_permissions(administrator = True)
async def mute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.message.guild.roles, name = "Muted")
    await member.add_roles(mute_role)
    await ctx.send(f"У { member.mention }, ограничение чата")

@bot.command()
@commands.has_permissions(administrator = True)
async def unmute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.message.guild.roles, name = "Muted")
    await member.remove_roles(mute_role)
    await ctx.send(f"У { member.mention } снято ограничение чата")


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@bot.command()
async def join(ctx):
    global svc
    channel = ctx.author.voice.channel
    if channel not in svc.keys():
        svc[channel] = [await channel.connect(), [], False, False]

@bot.command()
async def leave(ctx):
    global svc
    channel = ctx.author.voice.channel
    await ctx.voice_client.disconnect()
    del svc[channel]

@bot.command()
async def skip(ctx):
    global svc
    channel = ctx.author.voice.channel
    svc[channel][0].stop()
    await play(ctx, None)

@bot.command()
async def play(ctx, url, wrapped=False):
    global svc   
    channel = ctx.author.voice.channel
    if channel not in svc.keys():
        svc[channel] = [await channel.connect(), [], False, False]   
    # проверяем содержит ли url ссылку или название
    if url != None and "https://www.youtube.com/" not in url and url != "Repeatable":
        search = url
        s = "https://www.youtube.com/results?search_query=" + search
        sp = []
        resp = requests.get(s).content.decode('utf-8').split(":")
        cp = []
        for i in resp:
            cp.extend(i.split(","))
        resp = []
        for i in cp:
            resp.extend(i.split(","))
        for i in resp:
            if "watch?v=" in i:
                sp.append(i)
        url = "https://www.youtube.com" + sp[0][1:-1]
        svc[channel][1].append(url)
    elif url == None:
        pass
    else:
        svc[channel][1].append(url)
    music = svc[channel][1][0]
    if url != None and url != "Repeatable":
        embed = discord.Embed(title="Музыка", description=f"Поставлена в очередь на {len(svc[channel][1])} место: " + music, color=0xffffff)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Музыка", description=f"Теперь играет: " + music, color=0xffffff)
        await ctx.send(embed=embed)
    if svc[channel][2] != True or wrapped:
        svc[channel][2] = True
        # играем музыку
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(music, download=False)
        URL = info['formats'][0]['url']
        svc[channel][0].play(discord.FFmpegPCMAudio(executable="ffmpeg", source = URL, **FFMPEG_OPTIONS))
        # удаяем из плейлиста проигранную музыку
        try:
            del svc[channel][1][0]
        except Exception:
            pass
        while svc[channel][0].is_playing() and not svc[channel][-1]:
            await asyncio.sleep(1)
        svc[channel][-1] = False
        if svc[channel][1] != []:
            await play(ctx, None, wrapped=True)
        svc[channel][0].stop()
        await svc[channel][0].disconnect()
        del svc[channel]



#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
g_list = []
win = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]

@bot.command()
async def tictactoe(ctx, p2: discord.Member):
    global g_list
    p1 = ctx.message.author
    g = g_list
    for i in g:
        if (not i.p1 == p1 and not i.p2 == p2) and (not i.p1 == p2 and not i.p2 == p1):
            del g[g.index(i)]
    if len(g) == 0:
        gc = TicTacToe(p1, p2)
        for x in range(len(gc.board)): #вывод доски
            if x == 2 or x == 5 or x == 8:
                gc.line += " " + gc.board[x]
                await ctx.send(gc.line)
                gc.line = ""
            else:
                gc.line += " " + gc.board[x]
        
        num = random.randint(1, 2) # определение кто первый
        if num == 1:
            await ctx.send("Это ход <@" + str(gc.p1.id) + ">")
        elif num == 2:
            gc.change_turn()
            await ctx.send("Это ход <@" + str(gc.p2.id) + ">")
        g_list.append(gc)
    else:
        await ctx.send("Игра уже началась! ")
    
@bot.command()
async def place(ctx, pos1: int, pos2: int):
    global g_list
    global win
    pos = 3 *(pos1 - 1) + pos2
    for i in g_list:
        if i.p1 == ctx.message.author or i.p2 == ctx.message.author:
            gc = i
    if not gc.gameOver:
        mark = ""
        if gc.turn == ctx.author:
            if gc.turn == gc.p1:
                mark = ":regional_indicator_x:"
            elif gc.turn == gc.p2:
                mark = ":o2:"
            if 1 <= pos1 <= 3 and 1 <= pos2 <= 3 and gc.board[pos - 1] == ":white_large_square:":
                gc.board[pos - 1] = mark
                gc.count += 1
                # вывод доски
                gc.line = ""
                for x in range(len(gc.board)):
                    if x == 2 or x == 5 or x == 8:
                        gc.line += " " + gc.board[x]
                        await ctx.send(gc.line)
                        gc.line = ""
                    else:
                        gc.line += " " + gc.board[x]       
                for condition in win:
                    if gc.board[condition[0]] == mark and gc.board[condition[1]] == mark and gc.board[condition[2]] == mark:
                        gc.gameOver = True

                if gc.gameOver == True:
                    await ctx.send(mark + " победил!")
                    del g_list[g_list.index(gc)]
                elif gc.count >= 9:
                    del g_list[g_list.index(gc)]
                    await ctx.send("Ничья")

                # смена ходов
                if gc.gameOver != True:
                    gc.change_turn()
                    del g_list[g_list.index(gc)]
                    g_list.append(gc)
            else:
                await ctx.send("Обязательно выберите два числа меньше трёх и пустую клетку")
        else:
            await ctx.send("Это не ваш ход")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@bot.command()
async def profile(ctx, name, server):
    server = server.lower()
    # print(name, server)
    try:
        me = watcher.summoner.by_name(server, name)
        # print(me)
        rs = watcher.league.by_summoner(server, me['id'])
        # print(rs)
        my_matches = watcher.match.matchlist_by_account(server, me['accountId'])
        last_match = my_matches['matches'][0]
        match_detail = watcher.match.by_id(server, last_match['gameId'])
        name = me["name"]
        # print(name)
        rank = "Unranked"
        tier = ""
        level = ""
        lp = ""
        w = ""
        l = ""
        winrate = ""
        if len(rs) != 0:
            rs = rs[0]
            if rs["tier"] == "CHALLENGER" or rs["tier"] == "GRANDMASTER" or rs["tier"] == "MASTER":
                tier = rs["tier"].lower()
                tier = tier.capitalize()
                rank = f'{tier}'
                # print(rank)
            elif rs["tier"] != "CHALLENGER" and rs["tier"] != "GRANDMASTER" and rs["tier"] != "MASTER":
                tier = rs["tier"].lower()
                tier = tier.capitalize()
                rank = f'{tier} {rs["rank"]}'
                # print(rank)
            lp = rs["leaguePoints"]
            w = rs["wins"]
            l = rs["losses"]
            winrate = round(w / (w + l) * 100, 1)
        level = me["summonerLevel"]
        pid = -1
        stats = {}
        for i in match_detail["participantIdentities"]:
            if i["player"]["summonerName"] == name:
                pid = i["participantId"]
        for i in match_detail["participants"]:
            if i["participantId"] == pid:
                stats = i["stats"]
                champ = i["championId"]
        if len(stats.keys()) != 0:
            kda = f"{stats['kills']}/{stats['deaths']}/{stats['assists']}"
            cs = stats['totalMinionsKilled'] + stats['neutralMinionsKilled']
            win = "victory" if stats["win"] else "defeat"
        game_type = "Normal"
        fields = [("Level/Region:", f"{level}/{server.upper()}", True)]
        if rank != "Unranked":
            fields.append(("Ranked Stats:", f"{rank} {lp}LP\n{w}W {l}L\n{winrate}% winrate", True))
        else:
            fields.append(("Ranked Stats:", "Unranked", True))
        fields.append(("Last Game:", f"{win.capitalize()} with KDA {kda}", False))
        embed = discord.Embed(title=f"LOL Profile: {name}", color=0xffffff)
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await ctx.send(embed=embed)
    except ApiError:
        await ctx.send("Призывателя с таким именем не существует!\nЕсли имя содержит пробелы заключите его в кавычки.")

@tictactoe.error
async def tictactoe_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Пожалуйста, укажите игрока для этой команды.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Не забудьте упомянуть игрока (ie. <@688534433879556134>).")

@place.error
async def place_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Пожалуйста убедитесь, что вы правильно ввели позицию.")
    if isinstance(error, commands.BadArgument):
        await ctx.send("Убедитесь, что вы ввели целые числа.")
@bot.event
async def on_command_error(ctx, error):
    print(error)
    if ("You are missing Administrator permission(s) to run this command." in str(error)):
        await ctx.send("У вас недостаточно прав для использования данной команды! :)")
    if ("RuntimeError" in str(error)):
        await ctx.send("Музыка временно недоступна. Мы работаем над решением этой проблемы.")
    if ("Already playing audio" not in str(error)
        and "KeyError: <VoiceChannel" not in str(error)
        and "pos2 is a required argument that is missing" not in str(error)
        and 'Converting to "int" failed for parameter "pos' not in str(error)
        and "list index out of range" not in str(error)
        and "RuntimeError" not in str(error)):
        await ctx.send("Я не знаю таких команд, для доп. информации введите ?help")

bot.run(settings['token'])
