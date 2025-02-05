import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters
from datetime import datetime, time, timedelta
import re
from typing import Dict, List

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Path ke file JSON credentials
json_path = r"C:\Users\Holocene\Documents\AbsenBAM-bot\absenbam-19bee8c2fbb2.json"

# Setup koneksi ke Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
client = gspread.authorize(creds)

# Buka Google Sheets
spreadsheet_id = "1SrZWGbJ7JX9IHQnGXwwm1gyW0o0D81t5T4xtoqzEX4s"
spreadsheet = client.open_by_key(spreadsheet_id)

# Fungsi untuk membersihkan nama grup agar sesuai dengan nama sheet
def clean_sheet_name(group_name):
    # Hapus karakter yang tidak valid untuk nama sheet
    cleaned_name = re.sub(r'[^\w\-_]', '_', group_name)
    # Batasi panjang nama sheet (maksimal 100 karakter)
    return cleaned_name[:100]

# Fungsi untuk mendapatkan sheet berdasarkan nama grup
def get_sheet_for_group(group_name):
    sheet_name = clean_sheet_name(group_name)
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Buat sheet baru jika belum ada
        return spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)

# Command: /MulaiAbsenBAM
async def mulai_absen_bam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = update.message.chat.title
    await update.message.reply_text(
        f"Damai Sejahtera\n"
        f"Grup ini sedang menggunakan AbsenBAM-bot di grup {group_name}!\n\n"
        "📌 **Panduan Penggunaan:**\n"
        "1. Gunakan /absen untuk melakukan absensi setiap hari antara jam 01:00 - 04:00.\n"
        "2. Gunakan /leaderboard untuk melihat peringkat kehadiran.\n"
        "3. Gunakan /stats untuk melihat statistik kehadiran bulanan.\n"
        "4. Admin dapat menggunakan /admin untuk manajemen absensi.\n\n"
        "Dibuat oleh Bung Mrh.IK\n"
        "Puji Tuan"
    )

# Command: /absen
async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    group_name = update.message.chat.title
    now = datetime.now()
    date = now.strftime("%d-%m-%Y")
    time_str = now.strftime("%H:%M:%S")

    # Cek waktu absensi (01:00 - 04:00)
    if not (1 <= now.hour < 4):
        await update.message.reply_text("⛔ Absensi hanya bisa dilakukan antara jam 01:00 - 04:00.")
        return

    # Buka sheet untuk grup ini
    sheet = get_sheet_for_group(group_name)

    # Cek apakah sudah absen hari ini
    records = sheet.get_all_records()
    for record in records:
        if record['Nama'] == user.first_name and record['Tanggal'] == date:
            await update.message.reply_text("⛔ Anda sudah absen hari ini.")
            return

    # Tambahkan absensi ke Google Sheets
    sheet.append_row([user.first_name, time_str, date])

    # Ambil daftar yang sudah absen hari ini
    absen_hari_ini = [record['Nama'] for record in records if record['Tanggal'] == date]
    absen_hari_ini.append(user.first_name)  # Tambahkan user yang baru absen

    # Kirim daftar yang sudah absen
    daftar_absen = "\n".join(absen_hari_ini)
    await update.message.reply_text(f"✅ Absensi berhasil dicatat!\n\nDaftar yang sudah absen hari ini:\n{daftar_absen}")

# Command: /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = update.message.chat.title
    sheet = get_sheet_for_group(group_name)
    records = sheet.get_all_records()
    leaderboard_dict = {}

    for record in records:
        name = record['Nama']
        if name in leaderboard_dict:
            leaderboard_dict[name] += 1
        else:
            leaderboard_dict[name] = 1

    leaderboard_str = "🏆 Leaderboard Bulanan:\n"
    for name, count in sorted(leaderboard_dict.items(), key=lambda item: item[1], reverse=True):
        leaderboard_str += f"{name}: {count} hari\n"

    await update.message.reply_text(leaderboard_str)

# Command: /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = update.message.chat.title
    sheet = get_sheet_for_group(group_name)
    records = sheet.get_all_records()
    today = datetime.now()
    bulan_ini = today.strftime("%m-%Y")
    hari_dalam_bulan = today.day

    stats_dict = {}
    for record in records:
        tanggal = datetime.strptime(record['Tanggal'], "%d-%m-%Y")
        if tanggal.strftime("%m-%Y") == bulan_ini:
            name = record['Nama']
            if name in stats_dict:
                stats_dict[name] += 1
            else:
                stats_dict[name] = 1

    stats_str = f"📊 Statistik Kehadiran Bulan {bulan_ini}:\n"
    for name, count in stats_dict.items():
        persentase = (count / hari_dalam_bulan) * 100
        stats_str += f"{name}: {count}/{hari_dalam_bulan} hari ({persentase:.2f}%)\n"

    await update.message.reply_text(stats_str)

# Notifikasi awal absensi jam 01:00
async def notifikasi_awal(context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = context.job.data
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=(
            f"Damai Sejahtera,\n"
            f"Mari kita awali 7 program TSA dengan BAM di grup {group_name}\n"
            "يٰٓاَيُّهَا الْمُزَّمِّلُۙ\n"
            "قُمِ الَّلَيْلَ اِلَّا قَلِيْلًاۙ\n"
            "Klik tombol di bawah untuk absen\n"
            "/absen\n"
            "PTSA"
        )
    )

# Notifikasi akhir absensi jam 04:00
async def notifikasi_akhir(context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = context.job.data
    sheet = get_sheet_for_group(group_name)
    records = sheet.get_all_records()
    today = datetime.now().strftime("%d-%m-%Y")
    absen_hari_ini = [record['Nama'] for record in records if record['Tanggal'] == today]

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=(
            f"🛑 Absensi ditutup di grup {group_name}!\n"
            f"Yang sudah absen hari ini:\n{', '.join(absen_hari_ini)}\n"
            "Segala Puji Bagi Tuan Semesta Alam"
        )
    )

# Peringatan sebelum penutupan absensi (jam 03:30)
async def peringatan_penutupan(context: ContextTypes.DEFAULT_TYPE) -> None:
    group_name = context.job.data
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=(
            f"⏰ Peringatan! Absensi akan ditutup dalam 30 menit.\n"
            f"Jangan lupa absen jika belum melakukannya.\n"
            "/absen"
        )
    )

# Main function
def main() -> None:
    # Token bot Telegram
    application = Application.builder().token("7820376860:AAE3FaUigNUdqNTUK69BSNyEzUnNsnZLsys").build()

    # Tambahkan handler untuk command
    application.add_handler(CommandHandler("MulaiAbsenBAM", mulai_absen_bam))
    application.add_handler(CommandHandler("absen", absen))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("stats", stats))

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()