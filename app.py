import streamlit as st
import pandas as pd
import numpy as np

# Page Config
st.set_page_config(page_title="Agro-Suitability Pro 2026", layout="wide")

st.title("🌱 Agro-Ecological Suitability Engine")
st.markdown("Developed by **Emdadul Haque Emon** | Master's in Horticulture")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    districts = pd.read_csv('District_64_Verified_Final.csv', encoding='latin1')
    crops = pd.read_csv('Crop_Master_KS_Structured.csv', encoding='latin1')
    return districts, crops

df_dist, df_crop = load_data()

# --- 2. THE ENGINE ---
def calculate_suitability(d_row, c_row, season_type):
    # Prep inputs
    is_rabi = (season_type == "Rabi")
    if is_rabi:
        impact_rain = d_row['Rain Avg (mm)'] * 0.05
        temp_h = d_row['Temp H (°C avg)'] - 8
        temp_l = d_row['Temp L (°C avg)'] - 5
        max_t, max_r = c_row['KS1_MaxTemp'], c_row['KS5_MaxRain']
    else:
        impact_rain = d_row['Rain Avg (mm)']
        temp_h, temp_l = d_row['Temp H (°C avg)'], d_row['Temp L (°C avg)']
        # Summer Variant Logic
        if c_row.get('Summer_Tolerant', 0) == 1:
            max_t, max_r = c_row['KS1_MaxTemp'] + 4, c_row['KS5_MaxRain'] * 1.5
        else:
            max_t, max_r = c_row['KS1_MaxTemp'], c_row['KS5_MaxRain']

    # AEZ Match
    dist_aezs = str(d_row['AEZ']).replace(',', ' ').split()
    crop_aezs = str(c_row['Target AEZ']).replace(',', ' ').split()
    aez_match = any(a in crop_aezs for a in dist_aezs)

    # Switches
    is_high = "highland" in str(d_row['Land Type']).lower() or "hilly" in str(d_row['Land Type']).lower()
    eff_max_rain = max_r * (2.5 if is_high else 1.0)
    
    ks_heat = temp_h <= max_t
    ks_chill = temp_l >= c_row['KS2_MinTemp']
    ks_ph = c_row['KS3_MinPH'] <= d_row['pH avg'] <= c_row['KS4_MaxPH']
    ks_flood = impact_rain <= eff_max_rain
    
    # Count fails (Heat+Chill counts as 1 Temperature category)
    temp_fail = not (ks_heat and ks_chill)
    failed_count = [temp_fail, not ks_ph, not ks_flood].count(True)
    status_dict = {"Heat": ks_heat, "Chill": ks_chill, "pH": ks_ph, "Rain": ks_flood}

    # Scoring
    if failed_count == 0:
        def get_gaussian_perf(val, opt, sensitivity=0.2):
            return np.exp(-((val - opt)**2) / (2 * (opt * sensitivity)**2))
        f_temp = get_gaussian_perf((temp_h+temp_l)/2, (c_row['Opt_TempH']+c_row['Opt_TempL'])/2)
        f_ph = get_gaussian_perf(d_row['pH avg'], (c_row['KS3_MinPH']+c_row['KS4_MaxPH'])/2, 0.15)
        f_rn = get_gaussian_perf(impact_rain, c_row['Opt_Rain'], 0.4)
        env_perf = (f_temp + f_ph + f_rn) / 3
        bonus = 40 if aez_match else 12
        return round(60 + (env_perf * bonus), 2), status_dict, aez_match, impact_rain, temp_h, temp_l, eff_max_rain
    
    elif aez_match and failed_count == 1:
        return 30.0, status_dict, aez_match, impact_rain, temp_h, temp_l, eff_max_rain
    else:
        return 0.0, status_dict, aez_match, impact_rain, temp_h, temp_l, eff_max_rain

# --- 3. UI LAYOUT ---
with st.sidebar:
    st.header("Selector")
    selected_district = st.selectbox("District", df_dist['District'].unique())
    selected_crop = st.selectbox("Crop", df_crop['Crop Name'].unique())

d = df_dist[df_dist['District'] == selected_district].iloc[0]
c = df_crop[df_crop['Crop Name'] == selected_crop].iloc[0]

# Execution
r_score, r_stat, r_aez, r_rn, r_h, r_l, r_lim = calculate_suitability(d, c, "Rabi")
s_score, s_stat, s_aez, s_rn, s_h, s_l, s_lim = calculate_suitability(d, c, "Summer")

# --- Top Display ---
st.header(f"Results for {selected_crop} in {selected_district}")
c1, c2, c3 = st.columns(3)

c1.metric("❄️ Rabi Suitability", f"{r_score}%")
c2.metric("☀️ Summer Suitability", f"{s_score}%")

# Custom AEZ Metric - Only changing status color and symbol
with c3:
    aez_label = "🗺️ AEZ Status"
    aez_value = f"AEZ {d['AEZ']}"
    
    if r_aez:
        symbol, color, text = "✅", "#28a745", "Match" # Green
    else:
        symbol, color, text = "❌", "#dc3545", "No Match" # Red

    st.markdown(f"""
        <div style="display: flex; flex-direction: column;">
            <p style="font-size: 14px; color: rgb(40, 80, 20); margin-bottom: 0px;">{aez_label}</p>
            <p style="font-size: 28px; font-weight: 600; margin-bottom: 0px; color: rgb(49, 90, 63);">{aez_value}</p>
            <p style="font-size: 16px; color: {color}; margin-top: -5px; font-weight: 400;">{symbol} {text}</p>
        </div>
        """, unsafe_allow_html=True)

# --- 4. DETAILED DATA TABLE ---
st.subheader("Environmental Comparison")
# Showing why factors failed (as requested)
analysis_df = pd.DataFrame({
    "Parameter": ["Max Temp", "Min Temp", "Rainfall", "Soil pH"],
    "Rabi Status": ["✅" if r_stat["Heat"] else "❌", "✅" if r_stat["Chill"] else "❌", "✅" if r_stat["Rain"] else "❌", "✅" if r_stat["pH"] else "❌"],
    "Summer Status": ["✅" if s_stat["Heat"] else "❌", "✅" if s_stat["Chill"] else "❌", "✅" if s_stat["Rain"] else "❌", "✅" if s_stat["pH"] else "❌"],
    "District Value (Rabi/Sum)": [f"{r_h}/{s_h}°C", f"{r_l}/{s_l}°C", f"{round(r_rn,1)}/{round(s_rn,1)}mm", d['pH avg']],
    "Crop Tolerance": [f"Max: {c['KS1_MaxTemp']}°C", f"Min: {c['KS2_MinTemp']}°C", f"Max: {r_lim}/{s_lim}mm", f"{c['KS3_MinPH']}-{c['KS4_MaxPH']}"]
})
st.table(analysis_df)

# --- 5. RECOMMENDATIONS ---
st.divider()
st.subheader(f"Top 5 Recommended Crops for {selected_district}")
r_recs, s_recs = [], []

for _, row in df_crop.iterrows():
    rs, _, _, _, _, _, _ = calculate_suitability(d, row, "Rabi")
    ss, _, _, _, _, _, _ = calculate_suitability(d, row, "Summer")
    if rs > 0: r_recs.append((row['Crop Name'], rs))
    if ss > 0: s_recs.append((row['Crop Name'], ss))

rec_col1, rec_col2 = st.columns(2)
with rec_col1:
    st.write("🟢 **Best for Rabi (Winter)**")
    for name, sc in sorted(r_recs, key=lambda x: x[1], reverse=True)[:5]:
        st.write(f"- {name}: {sc}%")

with rec_col2:
    st.write("🟠 **Best for Summer (Kharif)**")
    for name, sc in sorted(s_recs, key=lambda x: x[1], reverse=True)[:5]:
        st.write(f"- {name}: {sc}%")
