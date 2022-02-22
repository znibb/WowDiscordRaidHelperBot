import discord
import gspread
import json
import os
from dotenv import load_dotenv
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

# Version
botVersion="1.0.7"

# Constants
googleKeyFile = 'google_key.json'
apiScope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
colours={
    "green": 0x00C09A,
    "blue": 0x0099E1,
    "purple": 0xA652BB,
    "pink": 0xFD0061,
    "yellow": 0xF8C300,
    "orange": 0xF93A2F,
    "gray": 0x91A6A6}

## Create bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)

## Load environment parameters
load_dotenv()
botCmdChannel_ID = os.getenv("BOT_CMD_CHANNEL_ID")
botAnnounceChannel_ID = os.getenv("BOT_ANNOUNCE_CHANNEL_ID")
discordToken = os.getenv("DISCORD_TOKEN")
spreadsheetUrl = os.getenv("SPREADSHEET_URL")

# Parameters
attendanceSheetName = "Attendance"
attendanceRowOffset = 4
rosterStatusCell = 'E7'
rosterNameRange = ['AM6:AM10','AM14:AM18','AM22:AM26','AM30:AM34','AM38:AM42']
rosterNoteRange = ['AO6:AO10','AO14:AO18','AO22:AO26','AO30:AO34','AO38:AO42']

### Helper functions
## Returns a new row for attendance sheet as a list of cells
def createNewAttendanceRow(name, dataColumn, colCount):
	newRow = [name]
	# Determine dataColumn numerical index
	(cellRow, cellCol) = gspread.utils.a1_to_rowcol(dataColumn+'1')
	# Pad empty cells
	newRow.append("")
	for x in range(2,colCount):
		if x == cellCol-1:
			newRow.append("1")
		else:
			newRow.append("0")

	return newRow

## Create Cell object with updated value
def createUpdateCell(name, names, values, dataColumn):
	# Get list-relative index
	index = names.index(name)
	# Determine incremented value
	newValue = str(int(values[index]) + 1)
	# Convert list index to cell row/col
	cellAddress = dataColumn + str(attendanceRowOffset+index)
	(cellRow, cellCol) = gspread.utils.a1_to_rowcol(cellAddress)
	# Create updated cell object
	cell = gspread.cell.Cell(cellRow, cellCol, value=newValue)

	return cell

## Fetch roster names
def fetchRosterNames(rosterSheet):
    namesRaw = rosterSheet.batch_get(rosterNameRange)
    # Due to complicated roster range rosterNamesRaw will be a list of lists of lists
    # Convert to a flat list of names
    names = []
    for i in namesRaw:
        for j in i:
            # Skip empty list items
            if j:
                # Also skip items that are just empty strings
                if j[0] != ' ':
                    names.append(properNameFormat(j[0]))

    return names

## Fetch signup names
def fetchSignupNames(signupSheet):
    # Fetch names of signups
    namesUnformatted = signupSheet.col_values(2)
    # Ensure proper name formatting
    names = []
    for name in namesUnformatted:
            names.append(properNameFormat(name))
    # Remove column header
    names.pop(0)
    # Remove duplicates
    names = list(set(names))
    # Remove empty rows
    names = list(filter(None, names))

    return names

## Fetch list of names and desired data column
def getAttendanceData(attendanceSheet, dataColumn):
	# Determine ranges
	numberOfEntries = attendanceSheet.get('B1')
	lastRowIndex = attendanceRowOffset + int(numberOfEntries[0][0]) - 1
	namesRange = 'A' + str(attendanceRowOffset) + ':A' + str(lastRowIndex)
	valuesRange = dataColumn + str(attendanceRowOffset) + ':' + dataColumn + str(lastRowIndex)

	# Fetch data
	namesRaw = attendanceSheet.get(namesRange)
	valuesRaw = attendanceSheet.get(valuesRange)

	# Parse list-of-lists into flat lists
	names = []
	for name in namesRaw:
		names.append(name[0])

	values = []
	for value in valuesRaw:
		values.append(value[0])

	return names, values

## Generate confirmed message
def generateConfirmedMessage(userName, raidName, raidDay, raidTime):
    return("Hello " + userName + "!\n\nYou have been confirmed for GrimSoul Pug's raid to " + raidName + " on " + raidDay + " at " + raidTime + ".\n\nPlease check assignments prior to raid and be available at invite time (30 min prior to raid start).")

## Generate standby message
def generateStandbyMessage(userName, raidName, raidDay, raidTime):
    return("Hello " + userName + "!\n\nThe roster for GrimSoul Pug's raid to " + raidName + " on " + raidDay + " at " + raidTime + " has now been locked and unfortunately you were not given a spot in the roster and have instead been placed on standby. This means that if we get any vacancies you'll be at the head of the line.\n\nIf you no longer wish to be considered as a replacement please unsign on our Discord server in #signup-changes.")

## Load config file
def loadConfig(bot):
    with open("config.json") as f:
        bot.config = json.load(f)
    f.close()

## Properly format names
def properNameFormat(name):
    return name.strip().capitalize()

## Increment attendance for everyone who got confirmed
def updateConfirmed(rosterSheet, attendanceSheet, confirmedColumn):
	# Fetch list of roster names
    rosterNames = fetchRosterNames(rosterSheet)

    # Fetch data from attendance sheet
    attendanceNames, attendanceValues = getAttendanceData(attendanceSheet, confirmedColumn)

    # Parse signups and generate lists of cells to be updated/added
    listOfCellsToUpdate = []
    listOfRowsToAdd = []
    attendanceColCount = attendanceSheet.col_count
    for name in rosterNames:
        # If name is already present in the sheet
        if name in attendanceNames:
            # Created cell object with incremented value
            cell = createUpdateCell(name, attendanceNames, attendanceValues, confirmedColumn)
            # Add cell object to update list
            listOfCellsToUpdate.append(cell)

        # If name is not already in the sheet (should not happen unless a person is added to the roster without being signed up properly)
        else:
            # Create new row and add to job list
            newRow = createNewAttendanceRow(name, confirmedColumn, attendanceColCount)
            listOfRowsToAdd.append(newRow)

    # Write updates to sheet
    if listOfCellsToUpdate:
        attendanceSheet.update_cells(listOfCellsToUpdate, 'USER_ENTERED')
    if listOfRowsToAdd:
        attendanceSheet.append_rows(listOfRowsToAdd, 'USER_ENTERED')

    return

## Increment attendance for everyone who signed up
def updateSignups(signupSheet, attendanceSheet, signedColumn):
    # Fetch list of names from signup sheet
    signedNames = fetchSignupNames(signupSheet)

    # Fetch data from attendance sheet
    attendanceNames, attendanceValues = getAttendanceData(attendanceSheet, signedColumn)

    # Parse signups and generate lists of cells to be updated/added
    listOfCellsToUpdate = []
    listOfRowsToAdd = []
    attendanceColCount = attendanceSheet.col_count
    for name in signedNames:
        # If name is already present in the sheet
        if name in attendanceNames:
            # Created cell object with incremented value
            cell = createUpdateCell(name, attendanceNames, attendanceValues, signedColumn)
            # Add cell object to update list
            listOfCellsToUpdate.append(cell)

        # If name is not already in the sheet
        else:
            # Create new row and add to job list
            newRow = createNewAttendanceRow(name, signedColumn, attendanceColCount)
            listOfRowsToAdd.append(newRow)

    # Write updates to sheet
    if listOfCellsToUpdate:
        attendanceSheet.update_cells(listOfCellsToUpdate, 'USER_ENTERED')
    if listOfRowsToAdd:
        attendanceSheet.append_rows(listOfRowsToAdd, 'USER_ENTERED')

    return

## Reset roster sheet
def resetRoster(rosterSheet):
    # Prepare instructions batch
    batchList = []
    emptyColumn = [[''],[''],[''],[''],['']]

    # Name field
    for x in rosterNameRange:
        name = {
            'range': x,
            'values': emptyColumn
        }
        batchList.append(name)

    # Note field
    for x in rosterNoteRange:
        note = {
            'range': x,
            'values': emptyColumn
        }
        batchList.append(note)

    # Write updates to sheet
    rosterSheet.batch_update(batchList)

    return

## Reset signups
def resetSignups(signupSheet):
    # Find all occurances of the 'MOD' tag
    modList = signupSheet.findall('MOD', in_column=1)
    # Extract row number for the last occurance of 'MOD'
    if modList:
        row = modList[-1].row
    else:
        row = 1
    # Get total number of rows
    rowCount = signupSheet.row_count
    # Delete all regular signups
    signupSheet.delete_rows(row+1, rowCount-1)

### Bot events
## Bot joins
@bot.event
async def on_ready():
    # Load config from file
    loadConfig(bot)

    # Connect to Google Sheets
    credentials = ServiceAccountCredentials.from_json_keyfile_name(googleKeyFile, apiScope)
    client = gspread.authorize(credentials)
    bot.spreadsheet = client.open_by_url(spreadsheetUrl)

    # Prepare announcement channel object
    bot.announceChannel = bot.get_channel(int(botAnnounceChannel_ID))

    # Announce bot start
    print(bot.user.name + " has connected to Discord on server " + bot.guilds[0].name + "!")

## Command error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error: Missing argument. Try -help.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Error: Unknown command. Try -help.")
    elif isinstance(error, commands.CheckFailure):
        pass
    else:
        await ctx.send("Error: Unknown error. Check server logs for more info.")
        raise error

### Predicates
## Predicate for only listening in designated channel
def restrictChannel():
    def predicate(ctx):
        return ctx.channel.id == int(botCmdChannel_ID)
    return commands.check(predicate)

### Bot commands
@bot.command(name='listraids', brief="List raids", aliases=['lr'])
@restrictChannel()
async def listraids(ctx):
    embed=discord.Embed(title="Raids", color=colours["yellow"])
    for key,value in bot.config.items():
        embed.add_field(name=key, value=value["name"], inline=True)
    await ctx.send(embed=embed)

@bot.command(name='loadconfig', brief="Load config", aliases=['lc'])
@restrictChannel()
async def loadconfig(ctx):
    loadConfig(bot)
    await ctx.send("Config loaded from file")

@bot.command(name='lock', brief="Lock roster", usage="<raidID>", aliases=['l'])
@restrictChannel()
async def lock(ctx, raidID):
    if raidID not in bot.config.keys():
        await ctx.send("ID " + raidID + " not found.")
        return
    else:
        # Prepare sheet objects
        rosterSheet = bot.spreadsheet.worksheet(bot.config[raidID]["rosterSheet"])
        signupSheet = bot.spreadsheet.worksheet(bot.config[raidID]["signupSheet"])

        # Update displayed roster status to "LOCKED"
        rosterSheet.update(rosterStatusCell, "LOCKED")

        # Fetch list of signup names
        signedNames = fetchSignupNames(signupSheet)

        # Fetch list of roster names
        rosterNames = fetchRosterNames(rosterSheet)

        # Calculate standby list
        standbyNames = list(set(signedNames) - set(rosterNames))

        # Prepare message template info
        raidName =  bot.config[raidID]["name"]
        raidDay =   bot.config[raidID]["day"]
        raidTime =  bot.config[raidID]["time"]

        # Retrieve signup data for cross-referencing names and usernames
        signupData = signupSheet.get_all_records()

        # Message confirmed players
        for name in rosterNames:
            entry = next(row for row in signupData if properNameFormat(row["Character name"]) == name)
            username = entry["Discord handle"]
            try:
                user = await commands.UserConverter().convert(ctx, username)
            except:
                await ctx.send("User not found: " + name)
            else:
                try:
                    await user.send(generateConfirmedMessage(name, raidName, raidDay, raidTime))
                except:
                    await ctx.send("Unable to message user: " + name)
        
        # Message standby players
        for name in standbyNames:
            entry = next(row for row in signupData if properNameFormat(row["Character name"]) == name)
            username = entry["Discord handle"]
            try:
                user = await commands.UserConverter().convert(ctx, username)
            except:
                await ctx.send("User not found: " + name)
            else:
                await user.send(generateStandbyMessage(name, raidName, raidDay, raidTime))

        # Announce publicly
        await bot.announceChannel.send("Roster for " + raidName + " has been **LOCKED**. <@&" + bot.config[raidID]["role"] + ">")

        # Indicate job is done
        await ctx.send("Locking done")

@bot.command(name='printconfig', brief="Print config", aliases=['pc'])
@restrictChannel()
async def printconfig(ctx):
    listOfColours = list(colours)
    for key in bot.config:
        embed=discord.Embed(title=key, description=bot.config[key]["name"], color=colours[listOfColours[int(key)]])
        embed.add_field(name="Day", value=bot.config[key]["day"], inline=True)
        embed.add_field(name="Time", value=bot.config[key]["time"], inline=True)
        embed.add_field(name="Roster sheet", value=bot.config[key]["rosterSheet"], inline=True)
        embed.add_field(name="Signup sheet", value=bot.config[key]["signupSheet"], inline=True)
        embed.add_field(name="Signed column", value=bot.config[key]["attendanceSignedColumn"], inline=True)
        embed.add_field(name="Confirmed column", value=bot.config[key]["attendanceConfirmedColumn"], inline=True)
        await ctx.send(embed=embed)

@bot.command(name='reset', brief="Reset signups", usage="<raidID", aliases=['r'])
@restrictChannel()
async def reset(ctx, raidID):
    if raidID not in bot.config.keys():
        await ctx.send("ID " + raidID + " not found.")
        return
    else:
        # Prepare sheet objects
        rosterSheet = bot.spreadsheet.worksheet(bot.config[raidID]["rosterSheet"])
        signupSheet = bot.spreadsheet.worksheet(bot.config[raidID]["signupSheet"])
        attendanceSheet = bot.spreadsheet.worksheet(attendanceSheetName)

        # Update attendance sheet based on signup data
        updateSignups(signupSheet, attendanceSheet, bot.config[raidID]["attendanceSignedColumn"])

        # Update attendance sheet based on confirmed data
        updateConfirmed(rosterSheet, attendanceSheet, bot.config[raidID]["attendanceConfirmedColumn"])

        # Reset signups
        resetSignups(signupSheet)

        # Reset the roster
        resetRoster(rosterSheet)

        # Change roster status back to "PENDING"
        rosterSheet.update(rosterStatusCell, "PENDING")

        # Announce publicly
        await bot.announceChannel.send("Signups for " + bot.config[raidID]["name"] + " has been **RESET**. <@&" + bot.config[raidID]["role"] + ">")

        # Indicate job is done
        await ctx.send("Reset done")

@bot.command(name='version', brief="Show running version", aliases=['v'])
@restrictChannel()
async def version(ctx):
	await ctx.send("Running version: " + botVersion)

### Run bot
bot.run(discordToken)
