import math
import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from table2ascii import table2ascii as t2a, PresetStyle, Alignment

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
class Answer:
    def __init__(self, answer: str = ""):
        self.answer = answer
        self.tileVal = 1 # will be set once score is calculated
        self.tileOnlyMult = 1 # manually set by user

        self.lengthBonus = 0 # will be set once score is calculated
        self.additionalBaseModifiers = 0 #defined as 0

        self.finalMult = 1 # manually set by user

        # Redefinable Vars
        # dict of bonuses added from having word length greater than 4
        self.lengthBonusDict = {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 5,
            "6": 5,
            "7": 5,
            "8": 10,
            "9": 10,
            "10": 15,
            "11": 15,
            "12": 20,
            "13": 20,
            "14": 20,
            "15": 25,
            "16": 25,
            "17": 25,
            "18": 30,
            "19": 40,
            "20": 50
        }
        # dict of tile base values, taking Scrabble as the source
        self.tileDict = {
            "a": 1,
            "b": 3,
            "c": 3,
            "d": 2,
            "e": 1,
            "f": 4,
            "g": 2,
            "h": 4,
            "i": 1,
            "j": 8,
            "k": 5,
            "l": 1,
            "m": 3,
            "n": 1,
            "o": 1,
            "p": 3,
            "q": 10,
            "r": 1,
            "s": 1,
            "t": 1,
            "u": 1,
            "v": 4,
            "w": 4,
            "x": 8,
            "y": 4,
            "z": 10,
            "!": 0
        }

    def tileOnlyScore(self):
        sumVal = 0
        lengthBonus = 0
        length = len(self.answer)
        for letter in self.answer:
            sumVal += self.tileDict[letter]

        for x in range(5, 21):
            if length >= x:
                lengthBonus += self.lengthBonusDict[str(x)]
            else:
                break
        self.tileVal = sumVal
        self.lengthBonus = lengthBonus

    @property
    def tile_score_after_tile_mult(self):
        return math.ceil(self.tileVal * self.tileOnlyMult)

    @property
    # returns the base value which is:
    # the tile only score, multiplied by any tile multipliers
    def baseVal(self):
        return self.tile_score_after_tile_mult + self.lengthBonus + self.additionalBaseModifiers

    @property
    def finalVal(self):
        return math.ceil(self.baseVal * self.finalMult)

    def set_word(self, answer: str):
        self.answer = answer
        if "!" in self.answer:
            self.tileDict["!"] = 16 - len(answer)

# instantiate the answer
wordplayAnswer = Answer()

# Add the guild ids in which the slash command will appear.
# If it should be in all, remove the argument, but note that
# it will take some time (up to an hour) to register the
# command if it's for all guilds.
@tree.command(
    name="wordplay_score",
    description="Find the scoring for a particular word",
    guild=discord.Object(id=DISCORD_GUILD)
)
@app_commands.describe(word="The word you want to score",
                       tile_mult="Any multiplier that applies only to the tile value. Default is 1.",
                       final_mult="Any multiplier that applies to the final score. Default is 1.",
                       base_mod="Any flat modifiers to be added to the base score. Default is 0.")
async def wordplay_score(interaction: discord.Interaction,
                         word: str,
                         tile_mult: float = 1.0,
                         final_mult: float = 1.0,
                         base_mod: int = 0):

    wordplayAnswer.set_word(word) # changes word and recalculates vals
    wordplayAnswer.tileOnlyScore()

    # process user optional inputs
    wordplayAnswer.tileOnlyMult = tile_mult if tile_mult else 1
    wordplayAnswer.finalMult = final_mult if final_mult else 1
    wordplayAnswer.additionalBaseModifiers = base_mod if base_mod else 0

    # generate lists for display, using word length to determine table size
    word_length = len(word)

    length_list_full = list(wordplayAnswer.lengthBonusDict.values())
    length_list = length_list_full[0:word_length]

    length_list.append("Length Bonus")
    length_list.append("")
    length_list.append(wordplayAnswer.lengthBonus)

    tile_list = list(word.upper())

    tile_list.append("Base Mod")
    tile_list.append("")
    tile_list.append(wordplayAnswer.additionalBaseModifiers)

    tile_value = [wordplayAnswer.tileDict[char] for char in word]
    tile_value.append("Tiles x Mult")
    entry = f'{wordplayAnswer.tileVal} x {wordplayAnswer.tileOnlyMult}'
    tile_value.append(entry)
    tile_value.append(wordplayAnswer.tile_score_after_tile_mult)

    base_row = [""] * len(word)
    base_row.append("Base Value")
    base_row.append("")
    base_row.append(wordplayAnswer.baseVal)

    dash_row = [""] * (len(word)+2)
    dash_row.append("---")

    final_row = [""] * len(word)
    final_row.append("Base x Mult")
    final_entry = f'{wordplayAnswer.baseVal} x {wordplayAnswer.finalMult}'
    final_row.append(final_entry)
    final_row.append(wordplayAnswer.finalVal)


    output = t2a(
        body = [length_list,
                tile_list,
                tile_value,
                dash_row,
                base_row,
                dash_row,
                final_row],
        style = PresetStyle.thin_compact,
        last_col_heading=True,
        alignments=[Alignment.LEFT] * len(word) + [Alignment.RIGHT, Alignment.RIGHT, Alignment.RIGHT]

    )

    await interaction.response.send_message(f"```\n{output}\n```")


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=DISCORD_GUILD))

client.run(DISCORD_TOKEN)




