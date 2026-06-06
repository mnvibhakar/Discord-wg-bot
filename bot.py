from discord.ext import commands
from discord.utils import get as get
import discord as ds
import pandas as pd
import json as js
import re
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))
TIMEOUT = 60.0

bot = commands.Bot(command_prefix="%",
                   intents=ds.Intents.all(),
                   chunk_guilds_at_startup=False,
                   member_cache_flags=ds.MemberCacheFlags.none())


@bot.command()
async def hello(ctx):
    await ctx.send("hi!! :sparkling_heart:")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def update_members(ctx):
    global specs, MEMBER_LIST
    
    await ctx.send(f"### Using following specifications:\n- role: {specs["MEMBER ROLE"]}\n- membership list: {MEMBER_LIST}\n- column: {specs["COLUMN TITLE"]}\n### proceed? (y/n)")
    try:
        user_response = await bot.wait_for("message", check=lambda msg: msg.author==ctx.author and msg.channel==ctx.channel, timeout=TIMEOUT)
    except:
        await ctx.send("session timed out :pensive:")
        return
    if user_response.content.lower() == "n":
        await ctx.send("OK, you can update the specifications using **update_bot**")
        return
    
    mistake_list = []
    role = get(ctx.guild.roles, name=specs["MEMBER ROLE"])
    member_list = pd.read_csv(MEMBER_LIST)[specs["COLUMN TITLE"]]
    members = [m async for m in ctx.guild.fetch_members(limit=None)]
    member_map = {}
    for m in members:
        member_map[m.name] = m

    for name in member_list:
        member = member_map.get(name)
        if member is not None:
            await member.add_roles(role)
        else:
            mistake_list.append(name)

    await ctx.send(f"### Updated member roles :saluting_face:")
    if len(mistake_list) != 0:
        await ctx.send(f"Unable to find members: {mistake_list}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def update_bot(ctx):

    global specs, MEMBER_LIST, channel

    user = ctx.author

    await user.send("## Can't wait for my update! Type next to skip to the next prompt")
    await user.send(f"### Current specifications:\n- role: {specs["MEMBER ROLE"]}\n- spreadsheet: {MEMBER_LIST}\n- home channel: {channel.name}")

    #the role for update_members
    try:
        await user.send("### What is the new **role name** for update_members?")
        user_response = await bot.wait_for("message", check=lambda msg: msg.author==user and msg.guild==None, timeout=TIMEOUT)
        if user_response.content.lower()!="next":
            test_role = get(ctx.guild.roles, name = user_response.content)
            if test_role is None:
                await user.send("role not found")
            else:
                specs["MEMBER ROLE"] = user_response.content
                
        else:
            await user.send("ok, skipping to next step")
    except:
        await user.send("timeout reached")
        return
    
    updated = False #track if the next 2 items were updated, if so uopdate the member list otherwise skip that step
    #The spreadsheet ID
    try:
        await user.send("### What is the new **Spreadsheet ID?**\n(found in the share link between **.../d/** and **/edit?...)**")
        user_response = await bot.wait_for("message", check=lambda msg: msg.author==user and msg.guild == None, timeout=TIMEOUT)
        if user_response.content.lower()!="next":
            MEMBER_LIST_ID = user_response.content
            updated = True
        else:
            await user.send("ok, skipping to next step")
    except:
        await user.send("timeout reached")
        return
    
    #The sheet name
    try:
        await user.send("### What is the new **Sheet name?**\n(found at the bottom of the spreadsheet, not the file name. eg 'sheet1')")
        user_response = await bot.wait_for("message", check=lambda msg: msg.author==user and msg.guild==None, timeout=TIMEOUT)
        if user_response.content.lower()!="next":
            MEMBER_LIST_SHEET = user_response.content
            updated = True
        else:
            await user.send("ok, skipping to next step")
    except:
        await user.send("timeout reached")
        return
    
    if updated: 
        try:
            TEST_LIST = f"https://docs.google.com/spreadsheets/d/{MEMBER_LIST_ID}/gviz/tq?tqx=out:csv&sheet={MEMBER_LIST_SHEET}"
            await user.send(TEST_LIST)
            test_read = pd.read_csv(TEST_LIST)
            specs["MEMBER LIST ID"] = MEMBER_LIST_ID
            specs["MEMBER LIST SHEET"] = MEMBER_LIST_SHEET
            MEMBER_LIST = f"https://docs.google.com/spreadsheets/d/{specs["MEMBER LIST ID"]}/gviz/tq?tqx=out:csv&sheet={specs["MEMBER LIST SHEET"]}"
        except:  
            await user.send("membership list not found :pensive: Please check location or retry entry")
        
    #The column name
    try:
        await user.send("### What is the new **column name?**\n(for the column to take the usernames from)")
        user_response = await bot.wait_for("message", check=lambda msg: msg.author==user and msg.guild==None, timeout=TIMEOUT)
        if user_response.content.lower()!="next":
            specs["COLUMN TITLE"] = user_response.content
        else:
            await user.send("ok, skipping to next step")
    except:
        await user.send("timeout reached")
        return
    
    #home channel id
    try:
        await user.send("### What is the new **home channel id**\n(for the channel I should send maintenance updates to)")
        user_response = await bot.wait_for("message",check=lambda msg: msg.author==user and msg.guild==None, timeout=TIMEOUT)
        if user_response.content.lower()!="next":
            specs["HOME CHANNEL"] = user_response.content
        else:
            await user.send("ok, skipping to next step")
    except:
        await user.send("timeout reached")
        return

    try:
        update_json()
    except:
        await user.send("update failed :pensieve_face, please check code :fearful:")
    await user.send("### Thanks for the update :cowboy:\ni'm all ready to go, use check to view my specs anytime!")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def check(ctx):
    global specs, MEMBER_LIST
    await ctx.send(f"### Here are my current specifications:\n- role: {specs["MEMBER ROLE"]}\n- membership list: {MEMBER_LIST}\n- column: {specs["COLUMN TITLE"]}\n- home channel: {channel.name}")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    KEYWORD_MAPPING = {
        "kys": "🦞",
        "kill yourself": "🦞",
        "kill your self": "🦞"
    }
    for word, react in KEYWORD_MAPPING.items():
        if re.search(rf'\b{word}\b', msg.content, re.IGNORECASE):
            await msg.add_reaction(react)
    await bot.process_commands(msg)

@bot.event
async def on_command_error(ctx, error):
    global channel
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRole):
        await ctx.reply(f"You don't have permission for that :rage:\n<@&{ADMIN_ROLE_ID}>")
    else:
        await ctx.send("An error occurred, sorry :worried:")

def update_json():
    global specs

    with open("wg_bot_specs.json", mode="w", encoding="utf-8") as write_file:
        js.dump(specs, write_file)

@bot.event
async def on_ready():
    global specs, MEMBER_LIST, channel
    with open("wg_bot_specs.json", mode="r", encoding="utf-8") as read_file:
        specs = js.load(read_file)
    MEMBER_LIST = f"https://docs.google.com/spreadsheets/d/{specs["MEMBER LIST ID"]}/gviz/tq?tqx=out:csv&sheet={specs["MEMBER LIST SHEET"]}"

    channel = bot.get_channel(int(specs["HOME CHANNEL"]))
    await channel.send("ready for action :saluting_face:")

bot.run(BOT_TOKEN)