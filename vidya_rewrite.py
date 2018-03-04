import discord
from discord.ext import commands
import asyncio
import datetime
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageOps
from PIL import ImageDraw
import urllib.request
import sqlite3
from steamapiwrapper.Users import SteamUser
from steamIDconverter.SteamIDConverter import get_64bit_steam_id

description = "A bot with tools for organising videogame get-togethers"

_2B = commands.Bot(command_prefix='>>', description=description)

OWNER_ID = "132142420044414976"

lobbies = []

conn = sqlite3.connect('steam.db')
c = conn.cursor()
# Create table
c.execute('''CREATE TABLE IF NOT EXISTS users
            (name text, id64 text, server text)''')

c.execute('''CREATE TABLE IF NOT EXISTS games
            (game text, alias text)''')
# Save (commit) the changes
conn.commit()


def get_all(table):
    c.execute('SELECT * FROM %s' % table)
    return c.fetchall()


class Lobby:
    def __init__(self, game, original_time, days, hours, minutes, channel, created_by):
        self.game = game
        self.original_time = original_time
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.channel = channel
        self.created_by = created_by


@_2B.event
async def on_ready():
    print('Logged in as')
    print(_2B.user.name)
    print(_2B.user.id)
    print('------')
    for member in _2B.get_all_members():
        print(str(member) + " - " + str(member.id))
        for role in member.roles:
            if role.name != "@everyone":
                print(role.name)
        print("\n")

async def lobby_reminders():
    await _2B.wait_until_ready()

    while not _2B.is_closed:
        now = datetime.datetime.now()
        for lobby in lobbies:
            if now.day - lobby.days >= lobby.original_time.day:
                if now.hour - lobby.hours >= lobby.original_time.hour:
                    if now.minute - lobby.minutes >= lobby.original_time.minute:
                        author = lobby.created_by
                        role = discord.utils.get(author.guild.roles, name=lobby.game)
                        await lobby.channel.send("Time to play %s !" % role.mention)
                        lobbies.remove(lobby)
                        print(lobbies)
                        await asyncio.sleep(30)
                        await role.delete()

        await asyncio.sleep(15)  # task runs every n seconds


@_2B.command()
async def createlobby(ctx, game, days, hours, minutes):
    """Creates a reminder that will ping anyone that joins at the given
    time. Useful for vidya. - Usage: >>createlobby [name] [days] [hours] [minutes]"""
    author = ctx.message.author
    allowed = True
    for lobby in lobbies:
        if lobby.created_by == author:
            allowed = False
            await ctx.send("I'm sorry %s, there is a limit of one lobby per user, and you've already made the lobby "
                           "`%s`" % (author.display_name, lobby.game))

    if allowed:
        original_time = datetime.datetime.now()

        newlobby = Lobby(game, original_time, int(days), int(hours), int(minutes), ctx.message.channel, author)
        lobbies.append(newlobby)

        server = ctx.message.guild
        author = ctx.message.author
        await server.create_role(name=game, mentionable=True, reason="User created game lobby.")
        await ctx.send("Created lobby `%s`.\nI'll remind everyone in the lobby in:\n`%s Days`\n`%s Hours`\n`%s Minutes`"
                      "\nIf you want to join in, use `2b joinlobby [name]`." % (game, days, hours, minutes))


@_2B.command()
async def joinlobby(ctx, gamename):
    """Allows you to join a lobby so you will be reminded. - Usage: >>joinlobby [name]"""

    lobbynames = []

    for i in lobbies:
        lobbynames.append(i.game)

    if gamename in lobbynames:
        user = ctx.message.author
        role = discord.utils.get(user.guild.roles, name=gamename)
        await user.add_roles(role)
    await ctx.send("I've added you to the lobby `%s`, %s." % (gamename, ctx.message.author.display_name))


@_2B.command()
async def leavelobby(ctx, gamename):
    """Allows you to leave a lobby. - Usage: >>leavelobby [name]"""

    lobbynames = []

    for i in lobbies:
        lobbynames.append(i.game)

    if gamename in lobbynames:
        user = ctx.message.author
        role = discord.utils.get(user.guild.roles, name=gamename)
        await user.remove_roles(role)
    await ctx.send("I've removed you from the lobby `%s`, %s." % (gamename, ctx.message.author.display_name))


@_2B.command()
async def deletelobby(ctx, gamename):
    """Allows you to delete a lobby - Usage: >>deletelobby [name]"""

    lobbynames = []

    for i in lobbies:
        lobbynames.append(i.game)

    if gamename in lobbynames:
        author = ctx.message.author
        role = discord.utils.get(author.guild.roles, name=gamename)
        await role.delete()

    for i in lobbies:
        if gamename == i.game:
            lobbies.remove(i)

    print(lobbies)

    await ctx.send("I've deleted the lobby `%s`." % gamename)


@_2B.command()
async def logoff(ctx):
    """Only I can use this"""

    if ctx.message.author.id == OWNER_ID:
        await ctx.send("Logging off...")
        await _2B.close()


@_2B.command()
async def ideal(ctx):
    """Generates an ideal gf meme using random quotes - Usage: >>ideal @[user]"""
    name = ctx.message.clean_content[8:]

    mentioned_user = ctx.message.mentions[0]
    quotelist = []

    async for possible_quote in ctx.message.channel.history(limit=1000):
        if possible_quote.content != "" and possible_quote.author == mentioned_user \
                and len(possible_quote.clean_content) <= 24 \
                and "2b" not in possible_quote.clean_content \
                and "!mugi" not in possible_quote.clean_content:
            quotelist.append('"' + possible_quote.clean_content + '"')

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                        'Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)

    url = mentioned_user.avatar_url
    local = 'avatar.jpg'
    urllib.request.urlretrieve(url, local)

    positions = [(20, 300), (250, 190), (580, 550), (70, 600), (170, 700)]

    img = Image.open("1000-800.png").convert('RGB')
    draw = ImageDraw.Draw(img)

    font1 = ImageFont.truetype("cour.ttf", 52)
    font2 = ImageFont.truetype("cour.ttf", 28)

    draw.text((100, 0), name + " GF", (0, 0, 0), font=font1)

    if len(quotelist) >= 5:
        randomizer = random.sample(range(len(quotelist)), 5)
        for i in range(5):
            draw.text(positions[i], quotelist[randomizer[i]], (0, 0, 0), font=font2)
    elif len(quotelist) < 5:
        randomizer = random.sample(range(len(quotelist)), len(quotelist))
        for i in range(len(quotelist)):
            draw.text(positions[i], quotelist[randomizer[i]], (0, 0, 0), font=font2)

    # load orignal avatar and mask
    avatar_img = Image.open('avatar.jpg', 'r')
    mask = Image.open('mask.png').convert('L')

    # resize
    avatar_img = avatar_img.resize((54, 54), Image.ANTIALIAS)

    # apply mask and save
    output = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    output.save('cropped_avi.png')

    # load masked image
    cropped_avi = Image.open('cropped_avi.png', 'r')

    # add masked image to output image
    img.paste(cropped_avi, (475, 325), cropped_avi)

    img.save('gf-out.jpg')

    await ctx.message.channel.send('', file=discord.File('gf-out.jpg', 'ideal_%s.jpg' % ctx.message.author))


@_2B.command()
async def registerme(ctx, vanityname):
    """Register your steam profile for use with other functions - Usage: >>registerme [username]
    Make sure to use your actual steam username, not just the nickname on your profile"""
    username = ctx.message.author.display_name
    server = ctx.message.author.guild
    id64 = get_64bit_steam_id('http://steamcommunity.com/id/%s' % vanityname)

    names_and_ids = get_all('users')
    id_list = []

    for item in names_and_ids:
        id_list.append(item[1])

    if id64 in id_list:
        await ctx.send("That ID is already registered. If you believe this is in error, I suggest you contact my "
                      "operator.")

    elif id64.isdigit() and len(id64) == 17:
        t = (username,)
        # delete the old record
        c.execute('DELETE FROM users WHERE name=?', t)
        # insert new record
        c.execute("INSERT INTO users VALUES ('%s', '%s', '%s')" % (username, id64, server))
        conn.commit()

        await ctx.send("Successfully registered user `%s` with ID `%s`" % (ctx.message.author.display_name, id64))

    else:
        await ctx.send("That isn't a valid ID. Try `2b help registerme` for more info.")


@_2B.command()
async def registergame(ctx, game, alias):
    """Register a game. Usage: >>registergame [gamename] [alias]
    The game's name must be in quotes, and must be *exactly* how it appears on the Steam store page"""
    roles = ctx.message.author.roles
    rolenames = []
    for role in roles:
        rolenames.append(role.name)

    if "🌸 Third-Years" in rolenames:
        t = (alias,)
        c.execute('DELETE FROM games WHERE alias=?', t)

        game = game.replace("'", "''")

        c.execute("INSERT INTO games VALUES ('%s', '%s')" % (game, alias))
        conn.commit()
        await ctx.send("I've registered `%s` as `%s`" % (game, alias))
    else:
        await ctx.send("I'm sorry %s, it appears you're not authorized to use that command." % ctx.message.author.display_name)


@_2B.command()
async def games(ctx):
    """Lists all registered games. Usage: >>games"""
    gamelist = get_all('games')
    output = "```REGISTERED GAMES\n"

    for record in gamelist:
        output += "\n%s = %s" % (record[0], record[1])

    output += "```"

    await ctx.send(output)


@_2B.command()
async def whohas(ctx, alias):
    """Returns a list of everyone who has a certain game. Usage: >>whohas [game alias]
    For a list of registered games, use >>games."""
    t = (alias,)
    c.execute('SELECT game FROM games WHERE alias=?', t)

    game_to_find = str(c.fetchone())
    game_to_find = game_to_find[2:-3]

    users_list = get_all('users')
    # user[0] = name
    # user[1] = id64
    # user[2] = server

    has_game = []

    this_server = ctx.message.author.guild
    members_in_this_server = this_server.members

    names_in_this_server = []
    for member in members_in_this_server:
        names_in_this_server.append(member.display_name)

    for user in users_list:
        display_name = str(user[0])
        if display_name in names_in_this_server:
            steamprofile = SteamUser(user[1], '0826010DFE9E1DA375FD4E20BCE54F22')
            all_games = steamprofile.get_games()
            for game in all_games:
                if game['name'] == game_to_find:
                    has_game.append(user[0])

    output = "Here's a list of everyone who owns %s:\n```" % game_to_find

    count = 0
    for name in has_game:
        output += name
        output += "\n"
        count += 1

    output += "```"

    if count > 0:
        await ctx.send(output)
    else:
        await ctx.send("There are no registered users who own %s" % game_to_find)


@_2B.event
async def on_message(message):

    wordlist = open("prohibited_emotions.txt").read().splitlines()

    if message.content.startswith("2b"):

        has_emotion = False
        for word in wordlist:
            if word in message.content:
                has_emotion = True

        if has_emotion:
            await message.channel.send("Emotions are prohibited.")

        if "ma'am" in message.content:
            await message.channel.send("Stop calling me ma'am, it's unnecessary.")

    await _2B.process_commands(message)


tokenfile = open("H:/PythonProjects/2bottoken.txt", 'r')
token = tokenfile.read()

_2B.loop.create_task(lobby_reminders())
_2B.run(token)
