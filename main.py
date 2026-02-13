 import discord
from discord.ext import commands, tasks
from discord.ui import View, Select, Button
import asyncio
from datetime import datetime
import os
import json
import random

# ==================== CONFIGURACIÓN ====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Archivos de datos
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

LEVEL_FILE = os.path.join(DATA_DIR, "levels.json")
WARN_FILE = os.path.join(DATA_DIR, "warnings.json")
DROP_FILE = os.path.join(DATA_DIR, "drops.json")
TICKET_FILE = os.path.join(DATA_DIR, "tickets.json")

# Crear archivos si no existen
for file in [LEVEL_FILE, WARN_FILE, DROP_FILE, TICKET_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# Funciones para leer/escribir JSON
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# Cargar datos
levels_data = load_json(LEVEL_FILE)
warns_data = load_json(WARN_FILE)
drops_data = load_json(DROP_FILE)
tickets_data = load_json(TICKET_FILE)

# Roles (ajusta según tu server)
MUTE_ROLE_ID = 123456789012345678
LEVEL_ROLES = {
    1: 1469620510961963092,
    5: 1469620736732958793,
    10: 1469621074999377972,
    15: 1469623837070196746,
    20: 1469624056490889298,
    25: 1469627684140093441,
    30: 1469624395223011462,
}

ROLES = {
    "helper": "Helper",
    "mod": "Moderador",
    "admin": "Admin",
    "mm_bajo": "MM Bajo",
    "mm_medio": "MM Medio",
    "mm_alto": "MM Alto",
    "mm_jefe": "MM Jefe"
}

# ==================== EVENTOS ====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} está listo!")

@bot.event
async def on_member_join(member):
    # Autorole
    role = member.guild.get_role(LEVEL_ROLES[1])
    if role:
        await member.add_roles(role)

    # Mensaje de bienvenida
    channel = None
    for ch in member.guild.text_channels:
        if "bienvenida" in ch.name.lower() or "welcome" in ch.name.lower():
            channel = ch
            break
    if not channel:
        channel = member.guild.system_channel

    if channel:
        embed = discord.Embed(
            title=f"🎉 Bienvenido {member.name}!",
            description=f"{member.mention} se ha unido al servidor.",
            color=discord.Color.green()
        )
        embed.add_field(name="👥 Miembros", value=member.guild.member_count)
        embed.add_field(name="📅 Cuenta creada", value=member.created_at.strftime("%d/%m/%Y"))
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Sistema de niveles
    uid = str(message.author.id)
    if uid not in levels_data:
        levels_data[uid] = {"xp": 0, "level": 0}

    levels_data[uid]["xp"] += 5
    level = levels_data[uid]["level"]
    xp = levels_data[uid]["xp"]

    if xp >= (level + 1) * 100:
        levels_data[uid]["level"] += 1
        new_level = levels_data[uid]["level"]
        if new_level in LEVEL_ROLES:
            role = message.guild.get_role(LEVEL_ROLES[new_level])
            if role:
                await message.author.add_roles(role)
        await message.channel.send(f"🎉 {message.author.mention} subió a nivel {new_level}")

    save_json(LEVEL_FILE, levels_data)
    await bot.process_commands(message)

# ==================== COMANDOS DE NIVELES ====================
@bot.tree.command(name="nivel", description="Muestra tu nivel")
async def nivel(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    level = levels_data.get(uid, {}).get("level", 0)
    xp = levels_data.get(uid, {}).get("xp", 0)
    await interaction.response.send_message(f"Nivel: {level} | XP: {xp}")

@bot.tree.command(name="leaderboard", description="TOP 10 de niveles")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(levels_data.items(), key=lambda x: x[1]["level"], reverse=True)
    text = ""
    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(int(uid))
        text += f"{i}. {user.name} - Nivel {info['level']}\n"
    await interaction.response.send_message(f"🏆 TOP 10\n{text}")

# ==================== WARNS ====================
@bot.tree.command(name="resetwarns", description="Reinicia los warns de un usuario")
async def resetwarns(interaction: discord.Interaction, usuario: discord.Member):
    warns_data[str(usuario.id)] = 0
    save_json(WARN_FILE, warns_data)
    await interaction.response.send_message("Warns reiniciados.")

# ==================== MODERACIÓN ====================
@bot.tree.command(name="mute", description="Mutea a un usuario")
async def mute(interaction: discord.Interaction, usuario: discord.Member, tiempo: int=60, razón: str="Sin razón"):
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted")
        for ch in interaction.guild.channels:
            await ch.set_permissions(mute_role, send_messages=False)
    await usuario.add_roles(mute_role)
    await interaction.response.send_message(f"🔇 {usuario.mention} muteado por {tiempo} min. Razón: {razón}")
    await asyncio.sleep(tiempo*60)
    await usuario.remove_roles(mute_role)
    await interaction.channel.send(f"🔊 {usuario.mention} ha sido desmuteado automáticamente.")

@bot.tree.command(name="unmute", description="Desmutea a un usuario")
async def unmute(interaction: discord.Interaction, usuario: discord.Member):
    role = interaction.guild.get_role(MUTE_ROLE_ID)
    await usuario.remove_roles(role)
    await interaction.response.send_message(f"{usuario.mention} desmuteado.")

@bot.tree.command(name="ban", description="Banea a un usuario")
async def ban(interaction: discord.Interaction, usuario: discord.Member, razón: str="Sin razón"):
    await usuario.ban(reason=razón)
    await interaction.response.send_message(f"✅ {usuario.mention} ha sido baneado. Razón: {razón}")

@bot.tree.command(name="clear", description="Borra mensajes del canal")
async def clear(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"{cantidad} mensajes borrados.", ephemeral=True)

@bot.tree.command(name="lock", description="Bloquea el canal")
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Canal bloqueado.")

@bot.tree.command(name="unlock", description="Desbloquea el canal")
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Canal desbloqueado.")

@bot.tree.command(name="slowmode", description="Activa slowmode en el canal")
async def slowmode(interaction: discord.Interaction, segundos: int):
    await interaction.channel.edit(slowmode_delay=segundos)
    await interaction.response.send_message(f"Slowmode activado: {segundos}s")

@bot.tree.command(name="say", description="Envía un mensaje con el bot")
async def say(interaction: discord.Interaction, mensaje: str):
    await interaction.response.send_message("Enviado.", ephemeral=True)
    await interaction.channel.send(mensaje)

@bot.tree.command(name="embed", description="Envía un embed con título y descripción")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str):
    em = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    await interaction.response.send_message(embed=em)

@bot.tree.command(name="msg", description="Envía mensaje privado a un usuario")
async def msg(interaction: discord.Interaction, usuario: discord.User, mensaje: str):
    try:
        await usuario.send(f"📩 Mensaje de {interaction.user}: {mensaje}")
        await interaction.response.send_message(f"✅ Mensaje enviado a {usuario.mention}", ephemeral=True)
    except:
        await interaction.response.send_message(f"❌ No se pudo enviar el mensaje a {usuario.mention}", ephemeral=True)

# ==================== DROPS ====================
class DropButton(View):
    def __init__(self, premio=None):
        super().__init__(timeout=None)
        self.claimed = False
        self.premio = premio

    @discord.ui.button(label="🎁 Reclamar Drop", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: Button):
        if self.claimed:
            await interaction.response.send_message("❌ Ya fue reclamado.", ephemeral=True)
            return
        self.claimed = True
        await interaction.response.send_message(f"🎉 {interaction.user.mention} ganó el drop! Premio: **{self.premio}**")

@bot.tree.command(name="drop", description="Crear un drop")
async def drop(interaction: discord.Interaction, premio: str):
    view = DropButton(premio)
    embed = discord.Embed(title="🎁 Nuevo Drop", description=f"Premio: **{premio}**\n¡Reclámalo ahora!", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=view)

# ==================== TICKETS ====================
class TicketControlView(View):
    def __init__(self, channel, user):
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user

    @discord.ui.button(label="✅ Reclamar", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: Button):
        allowed_roles = ["Helper", "Moderador", "Admin", "MM Bajo", "MM Medio", "MM Alto", "MM Jefe"]
        if any(role.name in allowed_roles for role in interaction.user.roles):
            await self.channel.send(f"📋 Ticket reclamado por {interaction.user.mention}")
            await interaction.response.send_message("✅ Ticket reclamado", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No tienes permisos", ephemeral=True)

    @discord.ui.button(label="🔒 Cerrar", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 Cerrando ticket...", ephemeral=True)
        await asyncio.sleep(2)
        if str(self.user.id) in tickets_data:
            del tickets_data[str(self.user.id)]
            save_json(TICKET_FILE, tickets_data)
        await self.channel.delete()

@bot.tree.command(name="menu", description="Muestra el panel principal de tickets")
async def menu(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Panel Principal", description="Selecciona una opción en los menús", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=TicketControlView(None, interaction.user))

# ==================== RUN ====================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: Configura tu token en la variable de entorno DISCORD_TOKEN")
    exit(1)

bot.run(TOKEN)
