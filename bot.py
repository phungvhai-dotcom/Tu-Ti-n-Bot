import discord

from discord.ext import commands

import random

import asyncio

import time

import json



TOKEN = ""

ADMIN_NAME = "vuong_83902"



intents = discord.Intents.default()

intents.message_content = True





class MyBot(commands.Bot):

    async def setup_hook(self):

        self.loop.create_task(bequan_loop())

        self.loop.create_task(auto_save_loop())





bot = MyBot(command_prefix="!", intents=intents, help_command=None)



# ================= DATA =================

data = {}

bequan_data = {}

user_dandien = {}

# Cache để lưu channel object tạm thời (không save vào JSON)

bequan_channels = {}



# ================= SAVE =================

def load_data():

    global data, bequan_data, user_dandien

    try:

        with open("data.json", "r", encoding="utf-8") as f:

            d = json.load(f)

            data = d.get("data", {})

            bequan_data = d.get("bequan_data", {})

            user_dandien = d.get("user_dandien", {})

    except:

        pass





def save_data():

    # Tạo copy của bequan_data để save (không lưu object)

    bequan_data_to_save = {}

    for uid, bq in bequan_data.items():

        bequan_data_to_save[uid] = {

            "end": bq["end"],

            "total_gain": bq["total_gain"],

            "minutes": bq["minutes"],

            "channel_id": bq["channel_id"],

            "member_id": bq["member_id"],

            "no_gain_until": bq["no_gain_until"],

            "initial_exp": bq["initial_exp"],

            "tauho_count": bq["tauho_count"],

            "exp_gained": bq["exp_gained"],

            "last_update": bq["last_update"],

            "progress_msg_id": bq["progress_msg_id"]

        }

    

    with open("data.json", "w", encoding="utf-8") as f:

        json.dump({

            "data": data,

            "bequan_data": bequan_data_to_save,

            "user_dandien": user_dandien

        }, f, ensure_ascii=False, indent=2)





async def auto_save_loop():

    await bot.wait_until_ready()

    while not bot.is_closed():

        save_data()

        await asyncio.sleep(60)





# ================= REALM =================

realm_order = [

    "Phàm Nhân",

    "Luyện Khí Kỳ",

    "Trúc Cơ Kỳ",

    "Kim Đan Kỳ",

    "Nguyên Anh Kỳ",

    "Hóa Thần Kỳ",

    "Luyện Hư Kỳ",

    "Hợp Thể Kỳ",

    "Đại Thừa Kỳ",

    "Độ Kiếp Kỳ"

]



thresholds = {

    "Luyện Khí Kỳ": 250,

    "Trúc Cơ Kỳ": 1000,

    "Kim Đan Kỳ": 5000,

    "Nguyên Anh Kỳ": 10000,

    "Hóa Thần Kỳ": 25000,

    "Luyện Hư Kỳ": 36000,

    "Hợp Thể Kỳ": 50000,

    "Đại Thừa Kỳ": 67000,

    "Độ Kiếp Kỳ": 100000

}





def next_realm(r):

    i = realm_order.index(r)

    return realm_order[i + 1] if i + 1 < len(realm_order) else r





def gain(r):

    return {

        "Phàm Nhân": 5,

        "Luyện Khí Kỳ": 3,

        "Trúc Cơ Kỳ": 2,

        "Kim Đan Kỳ": 1,

        "Nguyên Anh Kỳ": 0.5

    }.get(r, 0)





# ================= ĐAN ĐIỀN =================

def roll_dandien():

    x = random.random()

    if x < 0.15:

        return ("Phế Vật", 0.1)

    elif x < 0.35:

        return ("Tạm", 0.5)

    elif x < 0.75:

        return ("Bình Thường", 1.0)

    elif x < 0.9:

        return ("Thiên Tài", 1.5)

    return ("Nghịch Thiên", 2.0)





def get_dandien(uid):

    """Lấy đan điền của user (reset hàng ngày lúc 0h)"""

    day = int(time.time() // 86400)

    

    if uid not in user_dandien or user_dandien[uid]["day"] != day:

        name, mult = roll_dandien()

        user_dandien[uid] = {

            "day": day,

            "name": name,

            "mult": mult,

            "reroll_count": 0

        }

    

    return user_dandien[uid]





def reroll_dandien(uid):

    """Reroll đan điền (chỉ 1 lần/ngày)"""

    dd = get_dandien(uid)

    

    if dd["reroll_count"] >= 1:

        return False, "Hôm nay đã reroll rồi!"

    

    name, mult = roll_dandien()

    dd["name"] = name

    dd["mult"] = mult

    dd["reroll_count"] += 1

    

    return True, f"Đan điền thay đổi: **{name}** (x{mult})"





# ================= EMBED UTILS =================

def create_embed(title, description="", color=discord.Color.blue(), fields=None):

    """Tạo embed đẹp"""

    embed = discord.Embed(title=title, description=description, color=color)

    if fields:

        for name, value, inline in fields:

            embed.add_field(name=name, value=value, inline=inline)

    return embed





def get_progress_bar(current, needed, length=15):

    """Tạo progress bar"""

    if needed == 0:

        return "█" * length

    progress = int((current / needed) * length)

    return "█" * progress + "░" * (length - progress)





def format_time(seconds):

    """Format giây thành phút:giây"""

    mins = int(seconds // 60)

    secs = int(seconds % 60)

    return f"{mins}:{secs:02d}"





# ================= START =================

@bot.event

async def on_ready():

    load_data()

    print(f"{bot.user} online!")

    await bot.change_presence(activity=discord.Activity(

        type=discord.ActivityType.watching,

        name="tu luyện | !help"

    ))

    

    # Load lại channel objects cho bequan đang chạy

    for uid in list(bequan_data.keys()):

        bq = bequan_data[uid]

        try:

            channel = bot.get_channel(bq["channel_id"])

            if channel:

                bequan_channels[uid] = channel

        except:

            pass





# ================= MESSAGE =================

@bot.event

async def on_message(message):

    if message.author.bot:

        return



    uid = str(message.author.id)



    if uid not in data:

        data[uid] = {

            "exp": 0,

            "realm": "Phàm Nhân",

            "notify": True

        }



    user = data[uid]



    # ================= CHECK BẾ QUAN =================

    if uid in bequan_data:

        # Nếu là command thì block

        if message.content.startswith("!"):

            embed = create_embed(

                "⛔ Bế Quan",

                f"{message.author.mention} đang bế quan! Không thể dùng lệnh!",

                discord.Color.red()

            )

            await message.channel.send(embed=embed)

            return

        

        # Nếu là chat bình thường thì trừ tuvi

        user["exp"] = max(0, user["exp"] - 5)

        embed = create_embed(

            "⚠️ Bế Quan",

            f"{message.author.mention} đang bế quan! **-5** tu vi! 🌪️",

            discord.Color.orange()

        )

        await message.channel.send(embed=embed)

        save_data()

        return



    if message.content.startswith("!"):

        await bot.process_commands(message)

        return



    # ================= CHECK BẮT BUỘC DOTPHA =================

    cur = user["realm"]

    can_gain_exp = True



    if cur != "Độ Kiếp Kỳ":

        nxt = next_realm(cur)

        need = thresholds[nxt]

        max_exp = need * 1.1  # 110%

        

        # Nếu vượt quá 110% thì bắt buộc dotpha, không được cộng exp

        if user["exp"] >= max_exp:

            embed = create_embed(

                "⛔ Bắt Buộc Đột Phá!",

                f"{message.author.mention} tu vi quá cao!\nPhải dùng `!dotpha` để tiếp tục tu luyện!",

                discord.Color.red()

            )

            await message.channel.send(embed=embed)

            can_gain_exp = False

        # Check cơ hội dotpha thường

        elif user["exp"] >= need:

            if user["notify"]:

                embed = create_embed(

                    "⚡ Cơ Hội Đột Phá!",

                    f"{message.author.mention} đã đủ điều kiện đột phá **{nxt}**!\nDùng `!dotpha`",

                    discord.Color.green()

                )

                await message.channel.send(embed=embed)

                user["notify"] = False

        else:

            user["notify"] = True



    # ================= GAIN EXP =================

    if can_gain_exp:

        base_gain = gain(user["realm"])

        

        # Nếu từ Hóa Thần Kỳ trở lên thì không được exp từ chat

        if base_gain > 0:

            dd = get_dandien(uid)

            user["exp"] += base_gain * dd["mult"]



    save_data()

    await bot.process_commands(message)





# ================= DOTPHA =================

@bot.command()

async def dotpha(ctx):

    uid = str(ctx.author.id)

    u = data.get(uid)



    if not u:

        embed = create_embed("❌ Lỗi", "Chưa tu luyện!", discord.Color.red())

        return await ctx.send(embed=embed)



    if u["realm"] == "Độ Kiếp Kỳ":

        embed = create_embed("🏔️ Đỉnh Phong", f"{ctx.author.mention} đã đạt cảnh giới tối cao!", discord.Color.gold())

        return await ctx.send(embed=embed)



    nxt = next_realm(u["realm"])

    need = thresholds[nxt]



    if u["exp"] < need:

        embed = create_embed(

            "❌ Chưa Đủ Tu Vi",

            f"{ctx.author.mention} chưa đủ điều kiện!",

            discord.Color.red(),

            [

                ("Tu vi hiện tại", f"{int(u['exp'])}", True),

                ("Tu vi cần", f"{need}", True),

                ("Còn thiếu", f"⬆️ {int(need - u['exp'])}", True)

            ]

        )

        return await ctx.send(embed=embed)



    if random.random() < 0.5:

        u["realm"] = nxt

        u["notify"] = True

        embed = create_embed(

            "⚡ Đột Phá Thành Công!",

            f"{ctx.author.mention} đã nâng lên **{nxt}**! 🎉",

            discord.Color.green()

        )

        await ctx.send(embed=embed)

    else:

        loss = int(u["exp"] * 0.36)

        u["exp"] -= loss

        embed = create_embed(

            "🌩️ Thiên Kiếp Thất Bại!",

            f"{ctx.author.mention} bị thiên kiếp đánh!\n**-{loss}** tu vi ❌",

            discord.Color.red(),

            [("Tu vi còn", f"{int(u['exp'])}", False)]

        )

        await ctx.send(embed=embed)



    save_data()





# ================= TUVI =================

@bot.command()

async def tuvi(ctx):

    uid = str(ctx.author.id)

    u = data.get(uid)

    

    if not u:

        embed = create_embed("❌ Lỗi", "Bạn chưa có dữ liệu tu luyện!", discord.Color.red())

        return await ctx.send(embed=embed)



    dd = get_dandien(uid)

    realm = u["realm"]

    exp = u["exp"]



    fields = [

        ("🧗 Cảnh Giới", f"**{realm}**", False),

        ("🧬 Đan Điền Hôm Nay", f"{dd['name']} (x{dd['mult']})", False)

    ]



    if realm != "Độ Kiếp Kỳ":

        nxt = next_realm(realm)

        need = thresholds[nxt]

        bar = get_progress_bar(exp, need)

        max_exp = need * 1.1

        fields.append(

            ("📊 Tiến độ đột phá",

             f"{bar}\n`{int(exp)}/{need}`\n⬆️ {int(need - exp)} tu vi\n⛔ Max: {int(max_exp)}",

             False)

        )

    else:

        fields.append(("📊 Tu Vi", f"**{int(exp)}** ✨", False))



    embed = create_embed(

        f"📜 Hồ Sơ - {ctx.author.name}",

        "",

        discord.Color.blue(),

        fields

    )

    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)

    

    await ctx.send(embed=embed)





# ================= DANDIEN =================

@bot.command()

async def dandien(ctx):

    """Xem đan điền hôm nay"""

    uid = str(ctx.author.id)

    dd = get_dandien(uid)

    

    reroll_status = "✅ Có thể reroll" if dd["reroll_count"] < 1 else "❌ Đã reroll rồi"

    

    embed = create_embed(

        "🧬 Đan Điền Hôm Nay",

        f"**{dd['name']}**",

        discord.Color.blue(),

        [

            ("Multiplier", f"x{dd['mult']}", False),

            ("Ảnh Hưởng", f"Tất cả tu vi nhân thêm {dd['mult']}x", False),

            ("Reroll", reroll_status, False)

        ]

    )

    await ctx.send(embed=embed)





@bot.command()

async def rerolldandien(ctx):

    """Reroll đan điền (1 lần/ngày)"""

    uid = str(ctx.author.id)

    get_dandien(uid)

    

    success, message = reroll_dandien(uid)

    

    if success:

        dd = user_dandien[uid]

        embed = create_embed(

            "✨ Reroll Thành Công!",

            message,

            discord.Color.green(),

            [("Multiplier mới", f"x{dd['mult']}", False)]

        )

        save_data()

    else:

        embed = create_embed(

            "❌ Reroll Thất Bại",

            message,

            discord.Color.red()

        )

    

    await ctx.send(embed=embed)





# ================= BEQUAN =================

@bot.command()

async def bequan(ctx, minutes: int = None):

    uid = str(ctx.author.id)



    if uid not in data:

        data[uid] = {"exp": 0, "realm": "Phàm Nhân", "notify": True}



    user = data[uid]



    # SỬA LỖI 1: Bắt buộc phải nhập thời gian

    if minutes is None:

        embed = create_embed(

            "❌ Thiếu Tham Số",

            "Cách dùng: `!bequan <phút>`\nVí dụ: `!bequan 10`",

            discord.Color.red(),

            [("Thời gian cho phép", "1 - 1440 phút (24 giờ)", False)]

        )

        return await ctx.send(embed=embed)



    if minutes < 1 or minutes > 1440:

        embed = create_embed(

            "❌ Thời gian không hợp lệ",

            "Bế quan từ 1 đến 1440 phút (24 giờ)",

            discord.Color.red()

        )

        return await ctx.send(embed=embed)



    if uid in bequan_data:

        embed = create_embed(

            "❌ Đang Bế Quan",

            f"{ctx.author.mention} đã bế quan rồi!",

            discord.Color.red()

        )

        return await ctx.send(embed=embed)



    dd = get_dandien(uid)

    total_gain = 1 * dd["mult"] * minutes

    initial_exp = user["exp"]



    msg = await ctx.send(f"🧘 **{ctx.author.name}** bắt đầu bế quan {minutes} phút...")



    # SỬA LỖI 2: Lưu ID thay vì object

    bequan_data[uid] = {

        "end": time.time() + minutes * 60,

        "total_gain": total_gain,

        "minutes": minutes,

        "channel_id": ctx.channel.id,

        "member_id": ctx.author.id,

        "no_gain_until": 0,

        "initial_exp": initial_exp,

        "tauho_count": 0,

        "exp_gained": 0,

        "last_update": time.time(),

        "progress_msg_id": None

    }

    

    # Lưu channel object trong cache

    bequan_channels[uid] = ctx.channel



    save_data()





# ================= GIVE ADMIN =================

@bot.command()

async def give(ctx, member: discord.Member, amount: float):

    if ctx.author.name != ADMIN_NAME:

        embed = create_embed("❌ Không Có Quyền", "Chỉ admin mới có thể dùng!", discord.Color.red())

        return await ctx.send(embed=embed)



    if amount < 0:

        embed = create_embed("❌ Lỗi", "Số lượng phải dương!", discord.Color.red())

        return await ctx.send(embed=embed)



    uid = str(member.id)

    if uid not in data:

        data[uid] = {"exp": 0, "realm": "Phàm Nhân", "notify": True}



    data[uid]["exp"] += amount

    save_data()



    embed = create_embed(

        "✅ Cấp Tu Vi",

        f"Đã cấp **+{amount}** tu vi cho {member.mention}",

        discord.Color.green(),

        [("Tu vi hiện tại", f"{int(data[uid]['exp'])}", False)]

    )

    await ctx.send(embed=embed)





# ================= HELP =================

@bot.command()

async def help(ctx):

    embed = create_embed(

        "📚 Danh Sách Lệnh",

        "Hệ thống tu luyện xuyên tế",

        discord.Color.blue(),

        [

            ("🧗 Tu Luyện", "`!tuvi` - Xem thông tin tu vi\n`!dandien` - Xem đan điền hôm nay\n`!rerolldandien` - Reroll đan điền (1 lần/ngày)\n`!dotpha` - Đột phá\n`!bequan <phút>` - Bế quan (bắt buộc phải nhập số phút)", False),

            ("💡 Cách Chơi", "Chat bình thường để tăng tu vi\nKhi đủ exp dùng `!dotpha` để nâng cảnh giới\nMỗi ngày có đan điền khác nhau\nCó thể reroll 1 lần/ngày để tìm đan điền tốt hơn\nBế quan có nguy hiểm tẩu hỏa (10% mỗi phút)\nTừ Hóa Thần Kỳ trở lên không được exp từ chat", False)

        ]

    )

    await ctx.send(embed=embed)





# ================= LOOP BẾ QUAN =================

async def bequan_loop():

    await bot.wait_until_ready()



    while not bot.is_closed():

        now = time.time()



        for uid in list(bequan_data.keys()):

            bq = bequan_data[uid]

            user = data.get(uid)



            if not user:

                continue



            time_remaining = bq["end"] - now

            

            # ================= KẾT THÚC BẾ QUAN =================

            if time_remaining <= 0:

                final_exp = bq["initial_exp"] + bq["exp_gained"]

                user["exp"] = final_exp



                # Lấy channel từ cache hoặc từ ID

                channel = bequan_channels.get(uid)

                if not channel:

                    channel = bot.get_channel(bq["channel_id"])

                

                if channel:

                    embed = create_embed(

                        "🧘 Bế Quan Hoàn Tất",

                        f"Kết thúc bế quan!",

                        discord.Color.green(),

                        [

                            ("Thời gian", f"{bq['minutes']} phút", True),

                            ("Tu vi ban đầu", f"{int(bq['initial_exp'])}", True),

                            ("Tu vi tăng", f"**+{int(bq['exp_gained'])}** ✨", True),

                            ("Số lần tẩu hỏa", f"🔥 {bq['tauho_count']} lần", True),

                            ("Tu vi cuối cùng", f"**{int(final_exp)}**", True),

                            ("Đan điền", f"{get_dandien(uid)['name']} (x{get_dandien(uid)['mult']})", True)

                        ]

                    )



                    try:

                        await channel.send(embed=embed)

                    except:

                        pass

                

                # Xóa khỏi bequan_data

                del bequan_data[uid]

                if uid in bequan_channels:

                    del bequan_channels[uid]

                

                save_data()

                continue



            # ================= TẨU HỎA =================

            if not bq.get("no_gain_until", 0) or now >= bq["no_gain_until"]:

                if random.random() < 0.1:

                    bq["no_gain_until"] = now + 300

                    bq["tauho_count"] += 1

                    

                    # Lấy channel từ cache hoặc từ ID

                    channel = bequan_channels.get(uid)

                    if not channel:

                        channel = bot.get_channel(bq["channel_id"])

                    

                    if channel:

                        embed = create_embed(

                            "🔥 Tẩu Hỏa!",

                            f"Bị tẩu hỏa trong bế quan!\n⛔ 5 phút tiếp theo sẽ không nhận tu vi!",

                            discord.Color.red()

                        )

                        

                        try:

                            await channel.send(embed=embed)

                        except:

                            pass



            # ================= CỘNG EXP =================

            if not bq.get("no_gain_until", 0) or now >= bq["no_gain_until"]:

                exp_per_interval = bq["total_gain"] / (bq["minutes"] * 2)

                bq["exp_gained"] += exp_per_interval



            # ================= CẬP NHẬT TIẾN TRÌNH =================

            if now - bq["last_update"] >= 30:

                bq["last_update"] = now

                remaining_text = format_time(time_remaining)

                

                progress_embed = create_embed(

                    "🧘 Tiến Trình Bế Quan",

                    "",

                    discord.Color.blue(),

                    [

                        ("⏱️ Thời gian còn lại", remaining_text, True),

                        ("⏳ Tổng thời gian", f"{bq['minutes']} phút", True),

                        ("🔥 Lần tẩu hỏa", f"{bq['tauho_count']}", True),

                        ("✨ Tu vi đã nhận", f"+{int(bq['exp_gained'])}", True),

                        ("📊 Tiến độ", f"{int((bq['minutes']*60 - time_remaining) / (bq['minutes']*60) * 100)}%", True),

                        ("🧬 Đan Điền", f"{get_dandien(uid)['name']} (x{get_dandien(uid)['mult']})", True)

                    ]

                )



                # Lấy channel từ cache hoặc từ ID

                channel = bequan_channels.get(uid)

                if not channel:

                    channel = bot.get_channel(bq["channel_id"])

                

                if channel:

                    try:

                        # Nếu có progress_msg_id, edit nó

                        if bq["progress_msg_id"]:

                            try:

                                msg = await channel.fetch_message(bq["progress_msg_id"])

                                await msg.edit(embed=progress_embed)

                            except:

                                # Nếu message bị xóa, tạo message mới

                                msg = await channel.send(embed=progress_embed)

                                bq["progress_msg_id"] = msg.id

                        else:

                            # Tạo message mới

                            msg = await channel.send(embed=progress_embed)

                            bq["progress_msg_id"] = msg.id

                    except:

                        pass



            save_data()



        await asyncio.sleep(30)





# ================= RUN =================

bot.run(TOKEN)
