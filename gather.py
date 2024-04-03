import discord
import re
import json

TOKEN = "YOUR DISCORD BOT TOKEN HERE"
File_Channel = 123456789123456789
intents = discord.Intents.all()
client = discord.Client(intents=intents)

async def gather_addresses(channel_id):
    channel = client.get_channel(channel_id)
    if channel is None:
        return

    whitelist = {"WhiteList": []}
    removed = {"Removed": []}
    unique_addresses = set()  # To track unique addresses across all users
    user_entries = {}  # To ensure one entry per user, keyed by user ID

    async for message in channel.history(limit=500):  # Adjust limit as necessary
        match = re.search(r'bc1[0-9A-Za-z]{25,39}', message.content)
        if match:
            address = match.group(0)
            user_name = message.author.display_name
            user_id = message.author.id

            # Skip if the user has already posted an address (only keep the first)
            if user_id in user_entries:
                continue

            # Add to user entries and check if it's a duplicate address from different users
            if address not in unique_addresses:
                unique_addresses.add(address)
                user_entries[user_id] = {"Name": user_name, "ID": user_id, "Address": address}
            else:
                # If it's a duplicate address from different users, add to removed list
                removed["Removed"].append({"Name": user_name, "ID": user_id, "Address": address})

    # After processing, add non-duplicate user entries to the whitelist
    whitelist['WhiteList'].extend(user_entries.values())

    # Save the whitelisted addresses
    with open('whitelist.json', 'w') as file:
        json.dump(whitelist, file, indent=4)

    # Save the removed addresses
    if removed['Removed']:  # Only save if there are removed addresses
        with open('removed.json', 'w') as file:
            json.dump(removed, file, indent=4)

    return whitelist, removed

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    # Check if the message is from the bot itself
    if message.author == client.user:
        return

 # Check for !gather_addresses first, because it's more specific
    if message.content.startswith('!gather_addresses'):
        whitelist, _ = await gather_addresses(File_Channel)  # Use the correct channel ID
        await create_address_list_txt(whitelist)
        await message.channel.send(file=discord.File('addresses.txt'))
    elif message.content.startswith('!gather'):
        whitelist, removed = await gather_addresses(File_Channel)  # Use the correct channel ID
        await message.channel.send("Whitelist:", file=discord.File('whitelist.json'))
        if removed['Removed']:
            await message.channel.send("Removed addresses due to duplicates from different users:", file=discord.File('removed.json'))
            
client.run(TOKEN)
