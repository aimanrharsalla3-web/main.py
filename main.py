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

# Roles para tickets
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
    role = member.guild.get_role(1469620510961963092)
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

@bot.tree.command(name="setlevel", description="Cambiar nivel de un usuario")
async def setlevel(interaction: discord.Interaction, usuario: discord.Member, nivel: int):
    levels_data[str(usuario.id)] = {"xp": nivel*100, "level": nivel}
    save_json(LEVEL_FILE, levels_data)
    await interaction.response.send_message(f"Nivel de {usuario.mention} cambiado a {nivel}")

# ==================== COMANDOS DE WARNS ====================
@bot.tree.command(name="resetwarns", description="Reinicia los warns de un usuario")
async def resetwarns(interaction: discord.Interaction, usuario: discord.Member):
    warns_data[str(usuario.id)] = 0
    save_json(WARN_FILE, warns_data)
    await interaction.response.send_message("Warns reiniciados.")

# ==================== COMANDOS DE MODERACIÓN ====================
@bot.tree.command(name="unmute", description="Desmutea a un usuario")
async def unmute(interaction: discord.Interaction, usuario: discord.Member):
    role = interaction.guild.get_role(MUTE_ROLE_ID)
    await usuario.remove_roles(role)
    await interaction.response.send_message(f"{usuario.mention} desmuteado.")

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

@bot.tree.command(name="ban", description="Banea a un usuario")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, usuario: discord.Member, razón: str="Sin razón"):
    await usuario.ban(reason=razón)
    await interaction.response.send_message(f"✅ {usuario.mention} ha sido baneado. Razón: {razón}")

@bot.tree.command(name="mute", description="Mutea a un usuario")
@commands.has_permissions(manage_roles=True)
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

# ==================== COMANDO DM ====================
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
@commands.has_permissions(manage_messages=True)
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

# Menú principal de tickets
class MainMenuView(View):
    def __init__(self):
        super().__init__(timeout=None)

        # Soporte
        options_soporte = [
            discord.SelectOption(label="Reporte", description="Reportar un problema"),
            discord.SelectOption(label="Trade ElGringo", description="Solicitar un trade"),
            discord.SelectOption(label="Reclamar Premio", description="Reclama un premio"),
            discord.SelectOption(label="Postulaciones", description="Postula para un cargo"),
            discord.SelectOption(label="Alianzas", description="Solicitar alianzas"),
            discord.SelectOption(label="Otros", description="Otros tickets")
        ]
        self.select_soporte = Select(placeholder="Soporte", options=options_soporte)
        self.select_soporte.callback = self.soporte_callback
        self.add_item(self.select_soporte)

        # Middleman
        options_mm = [
            discord.SelectOption(label="MM Bajo", description="Transacciones pequeñas"),
            discord.SelectOption(label="MM Medio", description="Transacciones medianas"),
            discord.SelectOption(label="MM Alto", description="Transacciones grandes"),
            discord.SelectOption(label="MM Jefe", description="Controla todos los tickets")
        ]
        self.select_mm = Select(placeholder="Middleman", options=options_mm)
        self.select_mm.callback = self.mm_callback
        self.add_item(self.select_mm)

    async def soporte_callback(self, interaction: discord.Interaction):
        tipo = self.select_soporte.values[0]
        await create_ticket(interaction, tipo)

    async def mm_callback(self, interaction: discord.Interaction):
        nivel = self.select_mm.values[0]
        await create_mm_ticket(interaction, nivel)

# Comando para mostrar menú
@bot.tree.command(name="menu", description="Muestra el panel principal de tickets")
@commands.has_permissions(manage_messages=True)
async def menu(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Panel Principal", description="Selecciona una opción en los menús", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=MainMenuView())

# Crear tickets
async def create_ticket(interaction, tipo):
    user = interaction.user
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="🎫 TICKETS")
    if not category:
        category = await guild.create_category("🎫 TICKETS")

    channel_name = f"ticket-{tipo}-{user.name}"
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
                  user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    for rname in ["helper","mod","admin"]:
        role = discord.utils.get(guild.roles, name=ROLES[rname])
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
    tickets_data[str(user.id)] = channel.id
    save_json(TICKET_FILE, tickets_data)

    view = TicketControlView(channel, user)
    embed = discord.Embed(title=f"🎫 Ticket: {tipo}", description=f"{user.mention}, espera a que un staff lo atienda.", color=discord.Color.green())
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Ticket creado: {channel.mention}", ephemeral=True)

async def create_mm_ticket(interaction, nivel):
    user = interaction.user
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="🤝 MIDDLEMAN")
    if not category:
        category = await guild.create_category("🤝 MIDDLEMAN")

    channel_name = f"mm-{nivel}-{user.name}"
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
                  user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    nivel_roles = {
        "MM Bajo": ROLES["mm_bajo"],
        "MM Medio": ROLES["mm_medio"],
        "MM Alto": ROLES["mm_alto"],
        "MM Jefe": ROLES["mm_jefe"]
    }
    for rname in nivel_roles:
        role = discord.utils.get(guild.roles, name=nivel_roles[rname])
        if role:
            if nivel in rname or rname=="MM Jefe":
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
    tickets_data[str(user.id)] = channel.id
    save_json(TICKET_FILE, tickets_data)

    view = TicketControlView(channel, user)
    embed = discord.Embed(title=f"🤝 Ticket MM: {nivel}", description=f"{user.mention}, espera a que un MM lo atienda.", color=discord.Color.blue())
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Ticket MM creado: {channel.mention}", ephemeral=True)

# ==================== RUN ====================
TOKEN = os.getenv("DISCORD_TOKEN")  # Pon tu token en variables de entorno
if not TOKEN:
    print("ERROR: Configura tu token en la variable de entorno DISCORD_TOKEN")
    exit(1)

bot.run(TOKEN)
