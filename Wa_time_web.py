from datetime import datetime, timedelta ,timezone
import pytz
import ephem
import streamlit as st
from streamlit_autorefresh import st_autorefresh


def get_dawn_dusk_times(date, lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = date
    
    dawn = observer.next_rising(ephem.Sun(), use_center=True)
    dusk = observer.next_setting(ephem.Sun(), use_center=True)
    
    return dawn, dusk

def convert_to_wa_time(current_time, dawn, dusk, lat, lon):
    # ephem.Date → datetime.datetime に変換
    dawn = dawn.datetime().replace(tzinfo=timezone.utc)
    dusk = dusk.datetime().replace(tzinfo=timezone.utc)
    current_time = current_time.replace(tzinfo=timezone.utc)  # 念のため

    day_zodiac = ["卯", "辰", "巳", "午", "未", "申"]
    night_zodiac = ["酉", "戌", "亥", "子", "丑", "寅"]
    
    if current_time < dawn:
        previous_dusk = dusk - timedelta(days=1)
        _, time1 = get_dawn_dusk_times(datetime.utcnow().date() - timedelta(days=1), lat, lon)
        time1 = time1.datetime().replace(tzinfo=timezone.utc)
        time2 = dawn
        zodiac_list = night_zodiac
    elif current_time < dusk:
        time1 = dawn
        time2 = dusk
        zodiac_list = day_zodiac
    else:
        time1 = dusk
        time2,_ = get_dawn_dusk_times(datetime.utcnow().date() + timedelta(days=1), lat, lon)
        time2 = time2.datetime().replace(tzinfo=timezone.utc)
        zodiac_list = night_zodiac
    
    total_minutes = (time2 - time1).seconds
    minutes_since_time1 = (current_time - time1).seconds
    zodiac_index = (minutes_since_time1 * 6) // total_minutes
    zodiac_time = zodiac_list[zodiac_index]



    # 漢数字変換辞書
    kanji_numbers = {0: "零", 1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}

    # 時間計算（元のロジック）
    fractional_part = (minutes_since_time1 * 6 / total_minutes) % 1
    wa_time_ikutu = int((fractional_part * 3 + 1)//1)
    wa_time_bu = int((fractional_part * 3 + 1) % 1 * 10 // 1)
    wa_time_rin = int((fractional_part * 3 + 1) % 1 * 100 // 1 - wa_time_bu * 10)

    # 漢数字変換
    ikutu_kanji = kanji_numbers[wa_time_ikutu]
    bu_kanji = kanji_numbers[wa_time_bu]
    rin_kanji = kanji_numbers[wa_time_rin]

    # 表示
    return f"{zodiac_time}の刻{ikutu_kanji}つ{bu_kanji}分{rin_kanji}厘"


# 実行ブロック
def main():
    # 🔁 ページを5秒ごとに自動更新
    st_autorefresh(interval=5000, key="wa_refresh")

    latitude = 34.0
    longitude = 131.0
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    jst_midnight = jst.localize(datetime(now_jst.year, now_jst.month, now_jst.day, 0, 0, 0))
    current_date = jst_midnight.astimezone(pytz.utc)
    current_time = datetime.now(timezone.utc)

    dawn, dusk = get_dawn_dusk_times(current_date, latitude, longitude)
    wa_time = convert_to_wa_time(current_time, dawn, dusk, latitude, longitude)

    st.title("和時計 ⛩")
    st.write(f"現在の和刻: **{wa_time}**")

if __name__ == "__main__":
    main()
