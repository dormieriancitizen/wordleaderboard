import discord, os, json
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='w!', intents=intents)

guilds_counts = {} 

@bot.event
async def on_ready():
    # Check if guilds_counts is empty
    if not guilds_counts:
        # Load data from JSON files
        for filename in os.listdir("guilds"):
            if filename.endswith(".json"):
                guild_id = int(filename.split(".")[0])
                with open(os.path.join("guilds", filename), "r") as file:
                    guilds_counts[guild_id] = json.load(file)

@bot.command(name="leaderboard")
async def _create_leaderboard(ctx,arg):
    board = await ctx.send(f"## Word Leaderboard: {arg}")
    if os.path.isfile(f"guilds/{ctx.guild.id}.json"):
        with open(f"guilds/{ctx.guild.id}.json","r+") as file:
            leaderboard = json.loads(file.read())
            leaderboard[arg] = {
                    "leaderboard_id":board.id,
                    "leaderboard_channel":board.channel.id,
                    "counts":{}
                }
            file.seek(0)
            file.write(json.dumps(leaderboard))
            file.truncate()
            guilds_counts[ctx.guild.id] = leaderboard
        return
    else:
        with open(f"guilds/{ctx.guild.id}.json","x") as file:
            leaderboard_template = {
                arg:{
                    "leaderboard_id":board.id,
                    "leaderboard_channel":board.channel.id,
                    "counts":{}
                }
            }
            guilds_counts[ctx.guild.id] = leaderboard_template
            file.write(json.dumps(leaderboard_template))
        return

@bot.command(name="remove_leaderboard")
async def _remove_leaderboard(ctx,arg):
    with open(f"guilds/{ctx.guild.id}.json","w") as file:
        await (await bot.get_channel(guilds_counts[ctx.guild.id][arg]["leaderboard_channel"]).fetch_message(guilds_counts[ctx.guild.id][arg]["leaderboard_id"])).delete()
        del guilds_counts[ctx.guild.id][arg]
    await ctx.send("Removed leaderboard"+arg)
    return

@bot.listen("on_message")    
async def _update_message_counts(ctx):
    if ctx.author.id == bot.user.id:
        return

    if ctx.guild.id not in guilds_counts:
        return
    
    try:
        string = [str(ele) for ele in guilds_counts[ctx.guild.id].keys() if str(ele) in ctx.content][0]
    except IndexError:
        return

    if str(ctx.author.id) not in guilds_counts[ctx.guild.id][string]["counts"]:     
        guilds_counts[ctx.guild.id][string]["counts"][str(ctx.author.id)] = 1
    else:
        guilds_counts[ctx.guild.id][string]["counts"][str(ctx.author.id)] += 1
    
    with open(f"guilds/{ctx.guild.id}.json","w") as file:
        file.write(json.dumps(guilds_counts[ctx.guild.id]))
    
    if guilds_counts[ctx.guild.id][string]["counts"][str(ctx.author.id)] % 5 == 0:
        await update_leaderboard(ctx.guild.id,string)

async def update_leaderboard(guild,word):
    word_counts = guilds_counts[guild][word]
    message = (await bot.get_channel(word_counts["leaderboard_channel"]).fetch_message(word_counts["leaderboard_id"]))

    reply = f"## Word Leaderboard {word} \n"
    for key in sorted(word_counts["counts"], key=word_counts["counts"].get, reverse=True):
        reply += f"- `{key}` sent word `{word_counts['counts'][key]}` times \n"

    await message.edit(content=reply)

bot.run(os.getenv("TOKEN"))