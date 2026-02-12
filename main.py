import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from flask import Flask
from threading import Thread

# ------------------ KEEP ALIVE ------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot activo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# -----------------------------------------------

# ------------------ BOT DISCORD -----------------
TOKEN = os.environ['DISCORD_TOKEN']  # Asegúrate de poner tu token en Railway

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------- ARCHIVOS --------
for file in ["warnings.json", "levels.json"]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

MUTE_ROLE_ID = 123456789012345678  # PON TU ROL MUTE

LEVEL_ROLES = {
    1: 1469620510961963092,
    5: 1469620736732958793,
    10: 1469621074999377972,
    15: 1469623837070196746,
    20: 1469624056490889298,
    25: 1469627684140093441,
    30: 1469624395223011462,
    35: 1469624560096645120,
    40: 1469624751633862818,
    45: 1469624893468577945,
    50: 1469625094535118950,
    55: 1469625251913666743,
    60: 1469625378074132500,
    65: 1469625590976872540,
    70: 1469626056846741514,
    75: 1469626360098979923,
    80: 1469626493968711735,
    85: 1469626667596251136,
    90: 1469626863063400571,
    95: 1469627013336797327,
    100: 1469627222351548540
}

# -------- READY --------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot listo como {bot.user}")

# -------- LEVEL SYSTEM --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    with open("levels.json", "r") as f:
        data = json.load(f)

    uid = str(message.author.id)

    if uid not in data:
        data[uid] = {"xp": 0, "level": 0}

    data[uid]["xp"] += 5

    level = data[uid]["level"]
    xp = data[uid]["xp"]

    if xp >= (level + 1) * 100:
        data[uid]["level"] += 1
        new_level = data[uid]["level"]

        if new_level in LEVEL_ROLES:
            role = message.guild.get_role(LEVEL_ROLES[new_level])
            if role:
                await message.author.add_roles(role)

        await message.channel.send(f"🎉 {message.author.mention} subió a nivel {new_level}")

    with open("levels.json", "w") as f:
        json.dump(data, f)

    await bot.process_commands(message)

# -------- NIVEL --------
@bot.tree.command(name="nivel")
async def nivel(interaction: discord.Interaction):
    with open("levels.json", "r") as f:
        data = json.load(f)

    uid = str(interaction.user.id)
    level = data.get(uid, {}).get("level", 0)
    xp = data.get(uid, {}).get("xp", 0)

    await interaction.response.send_message(f"Nivel: {level} | XP: {xp}")

# -------- LEADERBOARD --------
@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    with open("levels.json", "r") as f:
        data = json.load(f)

    sorted_users = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)

    text = ""
    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(int(uid))
        text += f"{i}. {user.name} - Nivel {info['level']}\n"

    await interaction.response.send_message(f"🏆 TOP 10\n{text}")

# -------- SETLEVEL --------
@bot.tree.command(name="setlevel")
async def setlevel(interaction: discord.Interaction, usuario: discord.Member, nivel: int):
    with open("levels.json", "r") as f:
        data = json.load(f)

    data[str(usuario.id)] = {"xp": nivel * 100, "level": nivel}

    with open("levels.json", "w") as f:
        json.dump(data, f)

    await interaction.response.send_message(f"Nivel de {usuario.mention} cambiado a {nivel}")

# -------- RESET WARNS --------
@bot.tree.command(name="resetwarns")
async def resetwarns(interaction: discord.Interaction, usuario: discord.Member):
    with open("warnings.json", "r") as f:
        data = json.load(f)

    data[str(usuario.id)] = 0

    with open("warnings.json", "w") as f:
        json.dump(data, f)

    await interaction.response.send_message("Warns reiniciados.")

# -------- UNMUTE --------
@bot.tree.command(name="unmute")
async def unmute(interaction: discord.Interaction, usuario: discord.Member):
    role = interaction.guild.get_role(MUTE_ROLE_ID)
    await usuario.remove_roles(role)
    await interaction.response.send_message(f"{usuario.mention} desmuteado.")

# -------- CLEAR --------
@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"{cantidad} mensajes borrados.", ephemeral=True)

# -------- LOCK / UNLOCK --------
@bot.tree.command(name="lock")
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Canal bloqueado.")

@bot.tree.command(name="unlock")
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Canal desbloqueado.")

# -------- SLOWMODE --------
@bot.tree.command(name="slowmode")
async def slowmode(interaction: discord.Interaction, segundos: int):
    await interaction.channel.edit(slowmode_delay=segundos)
    await interaction.response.send_message(f"Slowmode activado: {segundos}s")

# -------- SAY --------
@bot.tree.command(name="say")
async def say(interaction: discord.Interaction, mensaje: str):
    await interaction.response.send_message("Enviado.", ephemeral=True)
    await interaction.channel.send(mensaje)

# -------- EMBED --------
@bot.tree.command(name="embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str):
    em = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    await interaction.response.send_message(embed=em)

# -------- AUTOROLE AL ENTRAR --------
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(1469620510961963092)
    if role:
        await member.add_roles(role)

# -------- DROPS --------
class DropButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = False

    @discord.ui.button(label="🎁 Reclamar Drop", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            await interaction.response.send_message("Ya fue reclamado.", ephemeral=True)
            return

        self.claimed = True
        await interaction.response.send_message(f"{interaction.user.mention} ganó el drop!")

@bot.tree.command(name="drops")
async def drops(interaction: discord.Interaction):
    view = DropButton()
    await interaction.response.send_message("🎉 ¡Primer en pulsar gana!", view=view)

# ------------------ RUN BOT -----------------
bot.run(TOKEN)
