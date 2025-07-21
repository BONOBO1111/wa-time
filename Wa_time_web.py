from datetime import datetime, timedelta ,timezone
import pytz
import ephem
import streamlit as st
from streamlit_autorefresh import st_autorefresh

#ＣＭＤで下記のコマンドを入力すると走る
# D:\wa_time>streamlit run wa_time_web.py

def get_dawn_dusk_around(time_utc, lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)

    # 過去24時間を基点に夜明け・日没を取得
    observer.date = time_utc - timedelta(days=1)
    dawn_past = observer.next_rising(ephem.Sun(), use_center=True)
    dusk_past = observer.next_setting(ephem.Sun(), use_center=True)

    # 現在を基点に夜明け・日没を取得
    observer.date = time_utc
    dawn_next = observer.next_rising(ephem.Sun(), use_center=True)
    dusk_next = observer.next_setting(ephem.Sun(), use_center=True)

    # UTC化
    dawn_past = dawn_past.datetime().replace(tzinfo=timezone.utc)
    dusk_past = dusk_past.datetime().replace(tzinfo=timezone.utc)
    dawn_next = dawn_next.datetime().replace(tzinfo=timezone.utc)
    dusk_next = dusk_next.datetime().replace(tzinfo=timezone.utc)

    # 過去の遅いほうが time1、現在以降の早いほうが time2
    time1 = max(dawn_past, dusk_past)
    time2 = min(dawn_next, dusk_next)

    # 昼夜判定
    is_day = dawn_past > dusk_past
    zodiac_list = ["卯", "辰", "巳", "午", "未", "申"] if is_day else ["酉", "戌", "亥", "子", "丑", "寅"]

    full_day = timedelta(days=1)
    daytime = time2-time1 if is_day else full_day-(time2-time1) #日中の時間
    nightime = full_day-daytime #夜間の時間
    day_night_rate = daytime / nightime  # 昼／夜 比率
    return time1, time2, zodiac_list, day_night_rate, is_day  # is_day が昼か夜か

def convert_to_wa_time(current_time, time1, time2, zodiac_list):
    total_minutes = (time2 - time1).total_seconds() / 60
    minutes_since_time1 = (current_time - time1).total_seconds() / 60
    zodiac_index = int((minutes_since_time1 * 6) // total_minutes)
    zodiac_time = zodiac_list[zodiac_index]

    fractional_part = (minutes_since_time1 * 6 / total_minutes) % 1
    dev_index = int((fractional_part * 16)//1)

    dev_list = {0: "正刻", 1: "十六分の一", 2: "八分の一", 3: "十六分の三", 4: "四分の一", 5: "十六分の五", 6: "八分の三", 7: "十六分の七", 8: "二分の一", 9: "十六分の九",10:"八分の五",11:"十六分の十一",12:"四分の三",13:"十六分の十三",14:"八分の七",15:"十六分の十五"}
    dev = dev_list[dev_index]
    wa_time = f"{zodiac_time}の刻{dev}"
    return wa_time, zodiac_time, dev_index


# 実行ブロック
def main():
    st_autorefresh(interval=5000, key="wa_refresh")

# 📍 プリセットとカスタム入力切り替え
st.sidebar.header("📍 観測地点の設定")

locations = {
    "宇部市（デフォルト）": (33.946, 131.246),
    "東京都": (35.6895, 139.6917),
    "鎌倉市": (35.3167, 139.5500),
    "京都市": (35.0116, 135.7681),
    "舞鶴市": (35.4753, 135.3331),
    "大阪市": (34.6937, 135.5023),
    "静岡市": (34.9756, 138.3828),
    "ロンドン":(51.5072,-0.1275),
    "カスタム入力": None
}

selected = st.sidebar.selectbox("観測地点を選択", list(locations.keys()))
message_area = st.sidebar.empty()

if selected == "カスタム入力":
    latitude = st.sidebar.number_input("緯度（北緯=＋）", value=346, step=1)
    longitude = st.sidebar.number_input("経度（東経=＋）", value=131, step=1)
    message_area.markdown(f"カスタム地点（緯度: {latitude}, 経度: {longitude}）の和刻を示します。")
elif selected in locations:
    latitude, longitude = locations[selected]
    message_area.markdown(f"**{selected}** の和刻を示します。")
else:
    message_area.error("無効な観測地点が選択されました。")

# ✅ 上記どちらのケースでも latitude と longitude が決まる

# 太陽高度取得関数
def get_solar_altitude(dt, lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = dt
    sun = ephem.Sun()
    sun.compute(observer)
    return sun.alt * 180 / ephem.pi

# 線形補間関数（2点間）
def interpolate_rgb(altitude, table):
    for i in range(len(table) - 1):
        a1, r1, g1, b1 = table[i]
        a2, r2, g2, b2 = table[i + 1]
        if a1 <= altitude <= a2:
            ratio = (altitude - a1) / (a2 - a1)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            return (r, g, b)
    # 範囲外の場合は最も近い端の値
    if altitude < table[0][0]:
        return tuple(table[0][1:])
    elif altitude > table[-1][0]:
        return tuple(table[-1][1:])

# 高度テーブル（例）
# 高度は低い順に並べること
alt_rgb_table = [
    [-90,0,5,10],
    [-18,0,5,10],
    [-7.36,148,57,189],
    [0,255,51,231],
    [5,253,53,139],
    [20,0,176,240],
    [45,125,224,255],
    [70,125,224,255],
    [90,65,55,255]
]

def get_background_color(dt, lat, lon):
    alt = get_solar_altitude(dt, lat, lon)
    rgb = interpolate_rgb(alt, alt_rgb_table)
    return rgb

# 使用例


# 🌐 共通処理はここから
now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
time1, time2, zodiac_list, day_night_rate, is_daytime = get_dawn_dusk_around(now_utc, latitude , longitude)
wa_time, zodiac_time, dev_index = convert_to_wa_time(now_utc, time1, time2, zodiac_list)

bg_color = get_background_color(now_utc,latitude , longitude)
print(f"現在の背景色（RGB）: {bg_color}")


# 文字色の決定
text_color = "rgb(0,0,0)" if is_daytime else "rgb(255,255,255)"

# 背景色の変換　
#def rgb_tuple_to_css(rgb_tuple):
#    return f"rgb({rgb_tuple[0]},{rgb_tuple[1]},{rgb_tuple[2]})"

# CSS文字列に変換 (r,g,b)→rgb(r,g,b)
bg_css_color = f"rgb{bg_color}"

# 背景と文字色の両方をCSSに適用
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_css_color};
        color: {text_color};
    }}
    h1, p, .stMarkdown {{
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# 表示
st.title("和時計 ⛩")
st.write(f"現在の和刻: **{wa_time}** ")
st.caption(f"今日の昼夜比率:{day_night_rate:.2f}")
st.caption(f"観測地点：緯度 {latitude:.4f}、経度 {longitude:.4f}")

if __name__ == "__main__":
    main()

