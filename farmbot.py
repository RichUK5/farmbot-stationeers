import discord, json, os, re, subprocess, sys, time
from anyio import open_file
from discord import option
from discord.ext import tasks
#from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

config = json.load(open('config.json'))
intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)

def write_userconfig():
    with open('userconfig.json', 'w') as f:
        json.dump(userconfig, f, indent=2)


def restart_stationeers():
    status = subprocess.check_output("sudo systemctl restart stationeers".split())
    return(status.decode())


def start_stationeers():
    status = subprocess.check_output("sudo systemctl start stationeers".split())
    return(status.decode())


def stop_stationeers():
    status = subprocess.check_output("sudo systemctl stop stationeers".split())
    return(status.decode())


def status_stationeers():
    command = subprocess.run("systemctl status stationeers".split(), capture_output=True, text=True)
    if command.stderr != '':
        status = command.stderr
    else:
        status = command.stdout
    StatusCleanList = []
    for line in status.split('\n'):
        if re.search(r'^\s*CGroup:|ServerPassword|ServerAuthSecret', line):
            break
        StatusCleanList.append(line)
    return('\n'.join(StatusCleanList))


global ConsoleLogPosition
ConsoleLogPosition = -1
async def read_stationeers_log():
    global ConsoleLogPosition
    if ConsoleLogPosition == os.stat('/opt/Stationeers/server.log').st_size:
        return None
    elif ConsoleLogPosition > os.stat('/opt/Stationeers/server.log').st_size:
        ConsoleLogPosition = 0
    Output = ''
    async with await open_file('/opt/Stationeers/server.log') as f:
        if ConsoleLogPosition == -1:
            await f.seek(0, 2)
        else:
            await f.seek(ConsoleLogPosition, 0)
        async for line in f:
            Output = Output + line
        ConsoleLogPosition = await f.tell()
    return Output.split('\n')


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    stationeers_log_check.start()


@bot.slash_command(guild_ids=config['guilds'], description="test command")
async def hello(ctx):
    await ctx.respond("hello")


@bot.slash_command(guild_ids=config['guilds'], description="Start Stationeers server")
async def startstationeers(ctx):
    RequiredPermissionLevel = 5
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    await ctx.respond("Starting Stationeers")
    start_stationeers()
    time.sleep(10)
    await ctx.respond(f"```\n{status_stationeers()}\n```")


@bot.slash_command(guild_ids=config['guilds'], description="Stop Stationeers server")
async def stopstationeers(ctx):
    RequiredPermissionLevel = 5
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    await ctx.respond("Stopping Stationeers")
    stop_stationeers()
    time.sleep(1)
    await ctx.respond(f"```\n{status_stationeers()}\n```")


@bot.slash_command(guild_ids=config['guilds'], description="Restart Stationeers server")
async def restartstationeers(ctx):
    RequiredPermissionLevel = 5
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    await ctx.respond("Restarting Stationeers")
    restart_stationeers()
    time.sleep(10)
    await ctx.respond(f"```\n{status_stationeers()}\n```")


@bot.slash_command(guild_ids=config['guilds'], description="Show Stationeers server status")
async def statusstationeers(ctx):
    RequiredPermissionLevel = 1
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    await ctx.respond(f"```\n{status_stationeers()}\n```")



@bot.slash_command(guild_ids=config['guilds'], description="Enable channel log notifications")
async def enablelognotifications(ctx):
    RequiredPermissionLevel = 10
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    if ctx.channel.id not in userconfig['log_channels']:
        Channel = bot.get_channel(ctx.channel.id)
        if Channel.can_send:
            userconfig['log_channels'].append(ctx.channel.id)
            write_userconfig()
            await ctx.respond("Log notifications enabled.")
        else:
            await ctx.respond("Cannot send messages to this channel, please fix permissions and try again.")
    else:
        await ctx.respond("Log notifications were already enabled, no changes made.")


@bot.slash_command(guild_ids=config['guilds'], description="Disable channel log notifications")
async def disablelognotifications(ctx):
    RequiredPermissionLevel = 10
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    if ctx.channel.id in userconfig['log_channels']:
        userconfig['log_channels'].remove(ctx.channel.id)
        write_userconfig()
        await ctx.respond("Log notifications disabled.")
    else:
        await ctx.respond("Log notifications were not enabled, no changes made.")


@bot.slash_command(guild_ids=config['guilds'], description="Enable channel update notifications")
async def enableupdatenotifications(ctx):
    RequiredPermissionLevel = 10
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    if ctx.channel.id not in userconfig['notification_channels']:
        Channel = bot.get_channel(ctx.channel.id)
        if Channel.can_send:
            userconfig['notification_channels'].append(ctx.channel.id)
            write_userconfig()
            await ctx.respond("Update notifications enabled")
        else:
            await ctx.respond("Cannot send messages to this channel, please fix permissions and try again")
    else:
        await ctx.respond("Update notifications were already enabled, no changes made")


@bot.slash_command(guild_ids=config['guilds'], description="Disable channel update notifications")
async def disableupdatenotifications(ctx):
    RequiredPermissionLevel = 10
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    if ctx.channel.id in userconfig['notification_channels']:
        if userconfig['automatic_updates'] and len(userconfig['notification_channels']) == 1:
            await ctx.respond("Automatic updates are enabled, and no other channels have notifications enabled. Please disable automatic updates first, or enable notifications on a different channel.")
            return()
        userconfig['notification_channels'].remove(ctx.channel.id)
        write_userconfig()
        await ctx.respond("Update notifications disabled.")
    else:
        await ctx.respond("Update notifications were not enabled, no changes made.")




@bot.slash_command(guild_ids=config['guilds'], description="Register a farmbot user for yourself")
async def registerfarmbotuser(ctx):
    FbUser = get_farmbot_user(ctx.author.id)
    if FbUser:
        await ctx.respond(f"Farmbot user for {FbUser['name']} already exists, aborting."); return

    NewFbUser = {
        'id': ctx.author.id,
        'global_name': ctx.author.global_name,
        'name': ctx.author.name,
        'permission_level': 1
    }
    userconfig['farmbot_users'].append(NewFbUser)
    write_userconfig()
    await ctx.respond(f"Farmbot user created for {ctx.author.name} with permission level 1")


def clean_tagged_user(User):
    if not re.match(r'^<@\d+>$', User):
        raise ValueError
    return int(re.sub(r'[<>@]', '', User))


def get_discord_user(ctx, UserId):
    Users = [ m for m in ctx.guild.members if m.id == UserId ]
    if len(Users) > 1:
        raise LookupError
    elif len(Users) == 1:
        return Users[0]
    else:
        return None


def get_farmbot_user(UserId: int):
    Users = [ u for u in userconfig['farmbot_users'] if u['id'] == UserId ]
    if len(Users) > 1:
        raise LookupError
    elif len(Users) == 1:
        return Users[0]
    else:
        return None


def get_farmbot_user_index(UserId: int):
    try:
        Index = [ x['id'] for x in userconfig['farmbot_users'] ].index(UserId)
    except ValueError:
        Index = -1
    return Index


async def test_farmbot_user_permission_level(ctx, RequiredPermissionLevel):
    try:
        FbUser = get_farmbot_user(ctx.author.id)
    except LookupError:
        await ctx.respond("Permissions check failed: multiple users found. Aborting."); return
    if FbUser and FbUser['permission_level'] >= RequiredPermissionLevel:
        return True
    else:
        await ctx.respond("Permission denied")
        return False


@bot.slash_command(guild_ids=config['guilds'], description="Create farmbot user")
@option(
    "user",
    str,
    description="@Tagged user to create",
    required=True
)
@option(
    "permission_level",
    int,
    description="Permission level to be given to user, 0-15. 15 is full admin, 0 is banned.",
    min_value=0,
    max_value=15
)
async def createfarmbotuser(ctx, user: str, permission_level: int = 1):
    RequiredPermissionLevel = 15
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return

    try:
        UserId = clean_tagged_user(user)
    except ValueError:
        await ctx.respond("Invalid request, please @tag a user"); return

    try:
        DiscordUser = get_discord_user(ctx, UserId)
    except LookupError:
        await ctx.respond("Discord user lookup failed: multiple users found. Aborting."); return
    if not DiscordUser:
        await ctx.respond("Discord user not found, aborting."); return

    FbUser = get_farmbot_user(UserId)
    if FbUser:
        await ctx.respond(f"Farmbot user for {FbUser['name']} already exists, aborting."); return

    NewFbUser = {
        'id': UserId,
        'global_name': DiscordUser.global_name,
        'name': DiscordUser.name,
        'permission_level': permission_level
    }
    userconfig['farmbot_users'].append(NewFbUser)
    write_userconfig()
    await ctx.respond(f"Farmbot user created for {user} with permission level {NewFbUser['permission_level']}")


@bot.slash_command(guild_ids=config['guilds'], description="Show farmbot user permission level")
@option(
    "user",
    str,
    description="@Tagged user to create",
    required=True
)
async def showfarmbotuser(ctx, user):
    RequiredPermissionLevel = 10
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return
    FbUser = get_farmbot_user(clean_tagged_user(user))
    if FbUser:
        await ctx.respond(f"```json\n{json.dumps(FbUser, indent=2)}\n```")
    else:
        await ctx.respond(f"FarmBot user for {user} not found")


@bot.slash_command(guild_ids=config['guilds'], description="Show farmbot user permission level")
@option(
    "user",
    str,
    description="@Tagged user to create",
    required=True
)
async def showmyfarmbotuser(ctx):
    FbUser = get_farmbot_user(ctx.author.id)
    if FbUser:
        await ctx.respond(f"```json\n{json.dumps(FbUser, indent=2)}\n```")
    else:
        await ctx.respond(f"FarmBot user for {ctx.author.name} not found")


@bot.slash_command(guild_ids=config['guilds'], description="Edit farmbot user permission level")
@option(
    "user",
    str,
    description="@Tagged user to edit",
    required=True
)
@option(
    "permission_level",
    int,
    description="Permission level to be given to user, 0-15. 15 is full admin, 0 is banned.",
    min_value=0,
    max_value=15,
    required=True
)
async def setfarmbotuserpermissionlevel(ctx, user: str, permission_level: int):
    RequiredPermissionLevel = 15
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return

    try:
        UserId = clean_tagged_user(user)
    except ValueError:
        await ctx.respond("Invalid request, please @tag a user"); return

    try:
        DiscordUser = get_discord_user(ctx, UserId)
    except LookupError:
        await ctx.respond("Discord user lookup failed: multiple users found. Aborting."); return
    if not DiscordUser:
        await ctx.respond("Discord user not found, aborting."); return

    FbUserIndex = get_farmbot_user_index(UserId)
    if FbUserIndex == -1:
        await ctx.respond(f"Farmbot user for {user} does not exist, aborting."); return

    userconfig['farmbot_users'][FbUserIndex]['global_name'] = DiscordUser.global_name
    userconfig['farmbot_users'][FbUserIndex]['name'] = DiscordUser.name
    userconfig['farmbot_users'][FbUserIndex]['permission_level'] = permission_level
    write_userconfig()
    await ctx.respond(f"Farmbot user updated for {user} with permission level {userconfig['farmbot_users'][FbUserIndex]['permission_level']}")


async def removefarmbotuser(ctx, user: str, permission_level: int):
    RequiredPermissionLevel = 15
    if await test_farmbot_user_permission_level(ctx, RequiredPermissionLevel) != True:
        return

    try:
        UserId = clean_tagged_user(user)
    except ValueError:
        await ctx.respond("Invalid request, please @tag a user"); return

    FbUserIndex = get_farmbot_user_index(UserId)
    if FbUserIndex == -1:
        await ctx.respond(f"Farmbot user for {user} does not exist, aborting."); return

    userconfig['farmbot_users'][FbUserIndex].remove()
    write_userconfig()
    await ctx.respond(f"Farmbot user removed for {user}")


async def send_notification(string):
    for Id in userconfig['notification_channels']:
        Channel = bot.get_channel(Id)
        if Channel.can_send:
            await Channel.send(string)
        else:
            print(f"Cannot send update notification to channel {Id} due to permissions")


async def send_log(string):
    for Id in userconfig['log_channels']:
        Channel = bot.get_channel(Id)
        if Channel.can_send:
            await Channel.send(string, silent=True)
        else:
            print(f"Cannot send update notification to channel {Id} due to permissions")


LogRegex = re.compile(r'^\d{2}:\d{2}:\d{2}: (Version|file:|WorldSetting:|World Loaded|StartSession|Client: \w+ \(\d+\). Connected.|Client \w+ \(\d+\) is ready|Client disconnected:|No clients connected|Starting AutoSave|Saving - file created)')
@tasks.loop(seconds=1)
async def stationeers_log_check():
    LogLines = await read_stationeers_log()
    if LogLines:
        for Line in LogLines:
            Match = re.match(LogRegex, Line)
            if Match:
                print(f"Log:{Line}")
                await send_log(f"```\n{Line}\n```")


global userconfig

if os.path.isfile('userconfig.json'):
    userconfig = json.load(open('userconfig.json'))
else:
    userconfig = {}

if 'notification_channels' not in userconfig:
    userconfig['notification_channels'] = []
if 'log_channels' not in userconfig:
    userconfig['log_channels'] = []
if 'notified_version' not in userconfig:
    userconfig['notified_version'] = ''
if 'automatic_updates' not in userconfig:
    userconfig['automatic_updates'] = False
if 'farmbot_users' not in userconfig:
    userconfig['farmbot_users'] = []
for Admin in config['farmbot_default_admin_discord_users']:
    if not userconfig['farmbot_users'] or Admin['id'] not in [ u['id'] for u in userconfig['farmbot_users'] ]:
        NewFbUser = {
            'id': Admin['id'],
            'global_name': Admin['global_name'],
            'name': Admin['name'],
            'permission_level': 15
        }
        userconfig['farmbot_users'].append(NewFbUser)

write_userconfig()


bot.run(config['token'])
