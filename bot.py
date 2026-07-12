import discord
from discord.ext import commands
import asyncio
import os
import json
from dotenv import load_dotenv

# ============ الإعدادات ============
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNERS_FILE = "owners.json"
UPDATES_ROLE_ID = 1510783082926571580  # الرول اللي يختاره اللاعب بنفسه

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

# ============ إدارة الـ Owners ============
def load_owners():
    if not os.path.exists(OWNERS_FILE):
        initial = [int(x.strip()) for x in os.getenv("OWNER_IDS").split(",")]
        save_owners(initial)
        return initial
    with open(OWNERS_FILE, "r") as f:
        return json.load(f)

def save_owners(owners_list):
    with open(OWNERS_FILE, "w") as f:
        json.dump(owners_list, f)

OWNER_IDS = load_owners()

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# ============ منع التكرار ============
processing_messages = set()

# ============ حدث الإقلاع ============
@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح كـ {bot.user} (ID: {bot.user.id})")
    print(f"📡 متصل على {len(bot.guilds)} سيرفر")
    try:
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"🔄 تم مزامنة {len(synced)} أمر بسيرفر {guild.name} فوراً")
    except Exception as e:
        print(f"⚠️ خطأ بمزامنة الأوامر: {e}")

# ============ حدث الرسائل (منع التكرار) ============
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.id in processing_messages:
        return
    processing_messages.add(message.id)
    try:
        await bot.process_commands(message)
    finally:
        processing_messages.discard(message.id)

# ============ +dm و /dm ============
@bot.command(name="dm")
async def dm_user(ctx, member: discord.Member, *, message: str):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية تستخدم هذا الأمر.")
        return
    try:
        await member.send(message)
        await ctx.send(f"✅ تم إرسال الرسالة إلى {member.name}")
    except discord.Forbidden:
        await ctx.send(f"❌ ما قدرت أرسل لـ {member.name} — مقفل DMs.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ صار خطأ: {e}")

@bot.tree.command(name="dm", description="إرسال رسالة خاصة لشخص معين")
async def slash_dm_user(interaction: discord.Interaction, member: discord.Member, message: str):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    try:
        await member.send(message)
        await interaction.response.send_message(f"✅ تم الإرسال إلى {member.name}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ مقفل DMs عند {member.name}.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

# ============ +addowner / +removeowner + Slash ============
@bot.command(name="addowner")
async def add_owner(ctx, member: discord.Member):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية.")
        return
    if member.id in OWNER_IDS:
        await ctx.send(f"⚠️ {member.name} موجود أصلاً.")
        return
    OWNER_IDS.append(member.id)
    save_owners(OWNER_IDS)
    await ctx.send(f"✅ تم إضافة {member.name}.")

@bot.command(name="removeowner")
async def remove_owner(ctx, member: discord.Member):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية.")
        return
    if member.id not in OWNER_IDS:
        await ctx.send(f"⚠️ {member.name} مو موجود.")
        return
    OWNER_IDS.remove(member.id)
    save_owners(OWNER_IDS)
    await ctx.send(f"✅ تم إزالة {member.name}.")

@bot.tree.command(name="addowner", description="إضافة شخص مصرّح له")
async def slash_add_owner(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    if member.id in OWNER_IDS:
        await interaction.response.send_message(f"⚠️ {member.name} موجود أصلاً.", ephemeral=True)
        return
    OWNER_IDS.append(member.id)
    save_owners(OWNER_IDS)
    await interaction.response.send_message(f"✅ تم إضافة {member.name}.", ephemeral=True)

@bot.tree.command(name="removeowner", description="إزالة شخص من المصرّح لهم")
async def slash_remove_owner(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    if member.id not in OWNER_IDS:
        await interaction.response.send_message(f"⚠️ {member.name} مو موجود.", ephemeral=True)
        return
    OWNER_IDS.remove(member.id)
    save_owners(OWNER_IDS)
    await interaction.response.send_message(f"✅ تم إزالة {member.name}.", ephemeral=True)

# ============ +come و /come ============
@bot.command(name="come")
async def tanbih(ctx, member: discord.Member):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية تستخدم هذا الأمر.")
        return
    channel_name = ctx.channel.name
    channel_link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}"
    message = (
        f"📩 لديك رسالة جديدة في التذكرة\n"
        f"مرحباً {member.mention}\n"
        f"صاحب التذكرة في انتظار ردك في **{channel_name}**\n"
        f"يرجى الرد في أقرب وقت ممكن.\n"
        f"📌 القناة: {channel_link}\n"
        f"👤 بواسطة: {ctx.author.name}"
    )
    try:
        await member.send(message)
        await ctx.send(f"✅ تم إرسال التنبيه إلى {member.name}")
    except discord.Forbidden:
        await ctx.send(f"❌ ما قدرت أرسل لـ {member.name} — مقفل DMs.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ صار خطأ: {e}")

@bot.tree.command(name="come", description="تنبيه شخص بالرد على تذكرته")
async def slash_tanbih(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    channel_name = interaction.channel.name
    channel_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}"
    message = (
        f"📩 لديك رسالة جديدة في التذكرة\n"
        f"مرحباً {member.mention}\n"
        f"صاحب التذكرة في انتظار ردك في **{channel_name}**\n"
        f"يرجى الرد في أقرب وقت ممكن.\n"
        f"📌 القناة: {channel_link}\n"
        f"👤 بواسطة: {interaction.user.name}"
    )
    try:
        await member.send(message)
        await interaction.response.send_message(f"✅ تم إرسال التنبيه إلى {member.name}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ مقفل DMs عند {member.name}.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

# ============ +dmall و /dmall (بس لأعضاء الرول المحدد) ============
@bot.command(name="dmall")
async def dm_all(ctx, *, message: str):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية تستخدم هذا الأمر.")
        return
    role = ctx.guild.get_role(UPDATES_ROLE_ID)
    if role is None:
        await ctx.send("⚠️ الرول غير موجود، تأكد من الـ Role ID.")
        return
    members = [m for m in role.members if not m.bot]
    if not members:
        await ctx.send("⚠️ ما فيه أعضاء مشتركين بهذا الرول حالياً.")
        return
    await ctx.send(f"⏳ جاري الإرسال لـ {len(members)} عضو مشترك بالتحديثات...")
    success = 0
    failed = 0
    for member in members:
        try:
            await member.send(message)
            success += 1
        except discord.Forbidden:
            failed += 1
        except discord.HTTPException:
            failed += 1
        await asyncio.sleep(1.2)
    await ctx.send(f"✅ تم الإرسال: نجح {success}، فشل {failed}.")

@bot.tree.command(name="dmall", description="إرسال رسالة لأعضاء رول التحديثات فقط")
async def slash_dm_all(interaction: discord.Interaction, message: str):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    role = interaction.guild.get_role(UPDATES_ROLE_ID)
    if role is None:
        await interaction.response.send_message("⚠️ الرول غير موجود.", ephemeral=True)
        return
    members = [m for m in role.members if not m.bot]
    if not members:
        await interaction.response.send_message("⚠️ ما فيه أعضاء مشتركين بهذا الرول.", ephemeral=True)
        return
    await interaction.response.send_message(f"⏳ جاري الإرسال لـ {len(members)} عضو...", ephemeral=True)
    success = 0
    failed = 0
    for member in members:
        try:
            await member.send(message)
            success += 1
        except discord.Forbidden:
            failed += 1
        except discord.HTTPException:
            failed += 1
        await asyncio.sleep(1.2)
    await interaction.followup.send(f"✅ تم الإرسال: نجح {success}، فشل {failed}.", ephemeral=True)

# ============ +maybespay و /maybespay ============
def build_pay_embed():
    embed = discord.Embed(
        title="💳 طرق الدفع المتوفرة ❤️",
        color=discord.Color.gold(),
        description="جميع حسابات MAYBE STORE الخاصة بالدفع"
    )
    embed.add_field(name="📱 Almadar | المدار", value="`0930668745`", inline=False)
    embed.add_field(name="📱 Libyana | ليبيانا", value="`0928242459`", inline=False)
    embed.add_field(name="₿ Litecoin Address | عنوان لايتكوين", value="`ltc1qnm2naalmffe4avaml4hayxkxmq85h0hgzsrlhf`", inline=False)
    embed.add_field(name="💵 USDT Address | عنوان USDT", value="`0x023BFE36Bd72F38004de6b124A436234F4a7Ef33`", inline=False)
    embed.set_footer(text="#MAYBE STORE")
    return embed

@bot.command(name="maybespay")
async def pay(ctx):
    await ctx.send(embed=build_pay_embed())

@bot.tree.command(name="maybespay", description="💳 عرض طرق الدفع المتوفرة")
async def slash_pay(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_pay_embed())

# ============ +stats و /stats ============
def build_stats_embed(guild):
    embed = discord.Embed(title=f"📊 إحصائيات {guild.name}", color=discord.Color.blue())
    embed.add_field(name="👥 الأعضاء", value=guild.member_count, inline=True)
    embed.add_field(name="💬 الرومات", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 الرولات", value=len(guild.roles), inline=True)
    embed.add_field(name="🤖 البوتات", value=len([m for m in guild.members if m.bot]), inline=True)
    embed.add_field(name="👤 الأعضاء الحقيقيين", value=len([m for m in guild.members if not m.bot]), inline=True)
    embed.set_footer(text=f"🆔 {guild.id}")
    return embed

@bot.command(name="stats")
async def server_stats(ctx):
    await ctx.send(embed=build_stats_embed(ctx.guild))

@bot.tree.command(name="stats", description="📊 عرض إحصائيات السيرفر")
async def slash_stats(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_stats_embed(interaction.guild))

# ============ +مسح و /مسح ============
@bot.command(name="مسح")
async def clear_messages(ctx, amount: int):
    if not is_owner(ctx.author.id):
        await ctx.send("❌ ما عندك صلاحية.")
        return
    if amount > 100:
        await ctx.send("⚠️ تقدر تحذف بس 100 رسالة كحد أقصى.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🗑️ تم حذف {len(deleted) - 1} رسالة.", delete_after=3)

@bot.tree.command(name="مسح", description="🧹 حذف عدد معين من الرسائل")
async def slash_clear(interaction: discord.Interaction, amount: int):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    if amount > 100:
        await interaction.response.send_message("⚠️ تقدر تحذف بس 100 رسالة كحد أقصى.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🗑️ تم حذف {len(deleted)} رسالة.", ephemeral=True)

# ============ /message-send ============
@bot.tree.command(name="message-send", description="إرسال رسالة نصية بالروم")
async def message_send(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    target_channel = channel or interaction.channel
    try:
        await target_channel.send(message)
        await interaction.response.send_message(f"✅ تم الإرسال بـ {target_channel.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ ما قدرت أرسل بهذا الروم — تأكد من صلاحيات البوت.", ephemeral=True)

# ============ /embed-create ============
@bot.tree.command(name="embed-create", description="إنشاء وإرسال Embed مخصص")
async def embed_create(
    interaction: discord.Interaction,
    title: str,
    color: str = "blue",
    channel: discord.TextChannel = None
):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("❌ ما عندك صلاحية.", ephemeral=True)
        return
    colors = {
        "blue": discord.Color.blue(),
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "gold": discord.Color.gold(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
    }
    embed_color = colors.get(color.lower(), discord.Color.blue())
    embed = discord.Embed(title=title, color=embed_color)
    target_channel = channel or interaction.channel
    try:
        await target_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ تم إرسال الـ Embed بـ {target_channel.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ ما قدرت أرسل بهذا الروم — تأكد من صلاحيات البوت.", ephemeral=True)

# ============ تشغيل البوت (لازم يضل آخر شي بالملف) ============
bot.run(TOKEN)