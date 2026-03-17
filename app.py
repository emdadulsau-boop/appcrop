import streamlit as st
import pandas as pd

#################################
from fpdf import FPDF
import io
import time

def generate_report(d_name, crop_results):
    # Initialize PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- Header (Removed Emojis) ---
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"Agricultural Suitability Analysis: {d_name}", ln=True, align='C')
    pdf.ln(5)

    for res in crop_results:
        # --- 1. Title & Score (Removed 🌱 Emoji) ---
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_fill_color(230, 230, 230)
        # We use str() and replace any high-unicode characters
        crop_name = str(res['crop']).encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, f"Crop: {crop_name} | Score: {res['score']}%", ln=True, fill=True)
        
        # --- 2. Insight ---
        pdf.set_font("Helvetica", '', 11)
        pdf.ln(2)
        # Remove ** which Streamlit uses for bold but PDF sees as raw text
        clean_insight = str(res['insight']).replace("**", "").encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 7, txt=clean_insight)
        pdf.ln(5)

        # --- 3. Technical Table ---
        pdf.set_font("Helvetica", 'B', 9)
        pdf.set_fill_color(245, 245, 245)
        
        w_param, w_dist, w_req, w_score = 45, 45, 65, 35
        
        pdf.cell(w_param, 8, "Parameter", border=1, fill=True)
        pdf.cell(w_dist, 8, "District Value", border=1, fill=True)
        pdf.cell(w_req, 8, "Requirement", border=1, fill=True)
        pdf.cell(w_score, 8, "Score", border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", '', 8)
        for row in res['table_data']:
            # Safe extraction - using 'ignore' to drop any character that isn't Latin-1
            p_text = str(row.get('Parameter', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
            d_text = str(row.get('District Value', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
            r_text = str(row.get('Requirement', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
            s_text = str(row.get('Score', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')

            pdf.cell(w_param, 7, p_text, border=1)
            pdf.cell(w_dist, 7, d_text, border=1)
            pdf.cell(w_req, 7, r_text, border=1)
            pdf.cell(w_score, 7, s_text, border=1)
            pdf.ln()
        
        pdf.ln(10) 

    # For fpdf (older version in your logs), dest='S' returns the string/bytes
    # If using fpdf2, just return pdf.output()
    try:
        return pdf.output(dest='S').encode('latin-1')
    except:
        return pdf.output()
     
    ########################################



# 1. THE DEFINITION (Place this at the TOP of your script)
def run_ai_insights(d_row, crop_name, total, aez_match, temp_score, texture_score, sal_score, season):
    st.markdown(f'<p style="color: #00d2ff; font-size: 1.05rem; font-weight: bold; margin-bottom: 5px; opacity: 0.9;">✨ AI Agronomist Analysis: {crop_name}</p>', unsafe_allow_html=True)
    st.info(f"Analyze specific bottlenecks for {crop_name} in this environment.")

    ans_key = f"ai_answer_{crop_name}"
    
    # --- FIX 1: INITIALIZE THE KEY ---
    if ans_key not in st.session_state:
        st.session_state[ans_key] = "Select an analysis button above to see expert advice."

    col1, col2, col3 = st.columns(3)

    # --- BUTTON 1: THE BOTTLENECK FINDER ---
    if col1.button(f"🔍 Why {int(total)}%?", key=f"why_{crop_name}"):
        reasons = []
        if not aez_match: reasons.append("outside primary AEZ target zones")
        if temp_score < 15: reasons.append("temperatures outside metabolic optimum")
        if texture_score < 0: 
            texture = d_row.get('Soil Texture', 'unknown')
            reasons.append(f"mechanical barrier from {texture} texture")
        if sal_score <= 0: reasons.append("salinity exceeds variety safety threshold")
        
        if not reasons:
            st.session_state[ans_key] = f"**Analysis:** {crop_name} is in its ideal environment! All parameters are optimized."
        else:
            summary = " and ".join(reasons)
            st.session_state[ans_key] = f"**Analysis:** The score is {int(total)}% because it is {summary}."
        # No need for st.write here anymore, the Success box at bottom handles it

    # --- BUTTON 2: SOIL AMENDMENTS ---
    if col2.button("🧪 Soil Remedy", key=f"remedy_{crop_name}"):
        d_ph = d_row.get('pH avg', 7.0)
        if d_ph > 7.5:
            st.session_state[ans_key] = f"**Alkaline Alert (pH {d_ph}):** High alkalinity can lock nutrients. Use **Ammonium Sulfate** and organic mulch."
        elif d_ph < 5.5:
            st.session_state[ans_key] = f"**Acidity Alert (pH {d_ph}):** High acidity risks Al-toxicity. Apply **Dolomite or Lime**."
        else:
            st.session_state[ans_key] = f"**pH Optimal ({d_ph}):** Soil is balanced. Maintain organic matter."

    # --- BUTTON 3: VARIETY STRATEGY ---
    if col3.button("🌡️ Varieties", key=f"var_{crop_name}"):
        if sal_score <= 0:
            st.session_state[ans_key] = f"**Salt Strategy:** Current salinity requires **salt-tolerant varieties** (e.g., BINA/BRRI lines)."
        elif season == "Summer":
            st.session_state[ans_key] = f"**Heat Strategy:** Use thermotolerant varieties to prevent flower drop."
        else:
            st.session_state[ans_key] = f"**Standard Strategy:** High-yielding varieties (HYV) will perform well here."

    # --- FIX 2: ONLY SHOW IF NOT THE DEFAULT ---
    if st.session_state[ans_key] != "Select an analysis button above to see expert advice.":
        st.success(st.session_state[ans_key])    
# --- CONFIGURATION ---
st.set_page_config(page_title="AgriGenius Pro", layout="wide", initial_sidebar_state="expanded")

# --- REFINED NEON UI ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at center, #001f3f 0%, #000814 100%); color: #ffffff !important; }
    [data-testid="stSidebar"] { min-width: 200px !important; max-width: 240px !important; background-color: #000814 !important; border-right: 2px solid #00d2ff; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .district-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; border: 1px solid #00d2ff; margin-bottom: 25px; }
    .sky-blue-val { color: #00d2ff !important; font-weight: bold; }
    .crop-header-btn { background: linear-gradient(90deg, #2e7d32 0%, #1b5e20 100%); color: #ffffff !important; padding: 12px 20px; border-radius: 12px; font-weight: 800; display: flex; justify-content: space-between; margin-top: 20px; }
    .percentage-badge { background: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 8px; border: 1px solid white; }
    .details-box { background: rgba(255, 255, 255, 0.03); border-radius: 0 0 12px 12px; padding: 15px; border: 1px solid rgba(0, 210, 255, 0.2); margin-bottom: 25px; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #43a047, #92fe9d); }
    h1 { color: #43a047 !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # Update paths as needed for your local machine
        districts = pd.read_csv(r'C:\Users\Tc\Desktop\District_64_Verified_Final.csv', encoding='latin1')
        crops = pd.read_csv(r'C:\Users\Tc\Desktop\Crop_Master_KS_Updated.csv', encoding='latin1')
        districts.columns = districts.columns.str.strip()
        crops.columns = crops.columns.str.strip()
        return districts, crops
    except:
        return None, None

def get_salinity_val(sal_str):
    sal_map = {'Non-saline': 0.5, 'Slightly saline': 2.5, 'Slight to moderate': 4.0, 'Moderately saline': 8.0, 'Strong saline': 12.0, 'Very strong': 16.0}
    for key, val in sal_map.items():
        if key.lower() in str(sal_str).lower(): return val
    return 1.0

def calculate_suitability_v3(d_row, c_row, season):
    raw_comparison = []
    
    # 1. AEZ MATCH (30%)
    dist_aezs = set(str(d_row.get('AEZ', '')).replace(',', ' ').split())
    crop_aezs = set(str(c_row.get('Target AEZ', '')).replace(',', ' ').split())
    aez_match = any(a in crop_aezs for a in dist_aezs)
    aez_score = 30 if aez_match else 0
    raw_comparison.append({"Parameter": "AEZ Map", "District Value": str(d_row.get('AEZ')), "Requirement": str(c_row.get('Target AEZ')), "Score": f"{aez_score}/30"})

    # 2. ENVIRONMENTAL
    if season == "Rabi":
        temp_h, temp_l = d_row.get('Temp H (C avg)', 30)-7, d_row.get('Temp L (C avg)', 15)-4
        rain = d_row.get('Rain Avg (mm)', 100) * 0.1
    else:
        temp_h, temp_l = d_row.get('Temp H (C avg)', 30)+4, d_row.get('Temp L (C avg)', 15)+1
        rain = d_row.get('Rain Avg (mm)', 100)

    avg_t = (temp_h + temp_l) / 2
    temp_score = 15 if (c_row.get('Opt_TempL', 15) <= avg_t <= c_row.get('Opt_TempH', 30)) else 7.5
    raw_comparison.append({"Parameter": "Avg Temp", "District Value": f"{round(avg_t,1)}°C", "Requirement": f"{c_row.get('Opt_TempL')}-{c_row.get('Opt_TempH')}°C", "Score": f"{temp_score}/15"})

    d_ph = d_row.get('pH avg', 7.0)
    ph_score = 15 if (c_row.get('KS3_MinPH', 5) <= d_ph <= c_row.get('KS4_MaxPH', 8)) else 5
    raw_comparison.append({"Parameter": "Soil pH", "District Value": f"{d_ph}", "Requirement": f"{c_row.get('KS3_MinPH', 5.5)}-{c_row.get('KS4_MaxPH', 7.5)}", "Score": f"{ph_score}/15"})

    rain_score = 10 if (0.5 * c_row.get('Opt_Rain', 1000) <= rain <= 1.5 * c_row.get('Opt_Rain', 1000)) else 5
    raw_comparison.append({"Parameter": "Rainfall", "District Value": f"{round(rain, 1)}mm", "Requirement": f"~{c_row.get('Opt_Rain', 1000)}mm", "Score": f"{rain_score}/10"})

    d_sal = get_salinity_val(d_row.get('Soil Salinity', 'Non-saline'))
    c_sal_limit = c_row.get('Salt_Tolerance_dS_m', 2.0)
    
    if d_sal <= c_sal_limit:
        sal_score = 10
    else:
        # Calculate how many "units" of the limit we are over; # At 5x the limit, 'ratio' will be 5.0
        ratio = d_sal / c_sal_limit
        
        # Linear deduction: 10 - ((ratio - 1) * (30 / 4)); # This ensures that at ratio=1 (limit), score is 10; # At ratio=5 (5x limit), score is 10 - (4 * 7.5) = -20
        deduction = (ratio - 1) * 7.5
        sal_score = round(10 - deduction, 2)
        
        # Optional: Hard floor at -20 so it doesn't drop to infinity
        sal_score = max(sal_score, -20.0)

    raw_comparison.append({
        "Parameter": "Salinity", 
        "District Value": f"{d_sal} dS/m", 
        "Requirement": f"Max {c_sal_limit}", 
        "Score": f"{sal_score}/10"
    })
    # 3. KILL SWITCHES
    raw_comparisons=[]
    term_reasons = []
    final_reason = None
    if season == "Summer" and c_row.get('Summer_Tolerant', 1) == 0:
        if temp_h > (c_row.get('KS1_MaxTemp', 35) + 1): 
                term_reasons.append(f"Extreme Heat ({temp_h}°C)")
    if d_sal > (c_sal_limit * 5):
        term_reasons.append(f"Toxic Salinity ({d_sal} dS/m)")
    if term_reasons:
        # Join all reasons found into one string
        final_reason = " & ".join(term_reasons)
        
       # 4. PHYSICAL SOIL LOGIC (Selective Alignment)
    texture_val = str(d_row.get('Soil Texture', '')).lower()
    crop_name = str(c_row.get('Crop Name', '')).lower()
    deep_rooted = ['carrot', 'radish', 'potato', 'onion', 'garlic', 'chili']
    is_target = any(crop in crop_name for crop in deep_rooted)

    if is_target:
        texture_score = float(d_row.get('texture_score', 0))
        if texture_score == 10: texture_status = "Ideal Texture"
        elif texture_score == 0: texture_status = "Moderate Texture"
        elif texture_score == -10: texture_status = "Heavy Soil (Yield Penalty)"
        elif texture_score == -20: texture_status = "Severe Compaction Risk"
        else: texture_status = "Sub-optimal Texture"
    else:
        texture_score = 10 
        texture_status = "Texture Neutral"

    raw_comparison.append({
        "Parameter": "Root Zone Suitability", 
        "District Value": d_row.get('Soil Texture'), 
        "Requirement": "Deep Root Expansion", 
        "Score": f"{texture_score}/10"
    })

    # 5. FINAL SCORE
    total = aez_score + temp_score + ph_score + rain_score + sal_score + texture_score
    final_score = max(0, min(total, 100))

    if final_reason:
        final_score = 0.0
        texture_status = "Biological Failure"
    else:
        # Normal math here
        final_score = aez_score + temp_score + ph_score # etc...
        texture_status = "Normal"

    return round(final_score, 2), final_reason, texture_status, aez_match, d_sal, c_sal_limit, raw_comparison
        


def main():
    st.markdown("<h1> Syl-64 Crop Suit Analyzer </h1>", unsafe_allow_html=True)
    dist_df, crop_df = load_data()
    if dist_df is None: return

    # --- TOP SELECTION BAR ---
    # Creating three columns at the top for a horizontal selection experience
    top_col1, top_col2, top_col3 = st.columns([1.5, 2, 1])

    with top_col1:
        # Create a placeholder for the district selector
         dist_placeholder = st.empty()

# Only show the selectbox if a district hasn't been "confirmed" yet
    if "confirmed_dist" not in st.session_state:
            with dist_placeholder:
                 sel_dist = st.selectbox("🌍 Select District", district_options, key="dist_selector")
                 if sel_dist != "Select a District":
                    st.session_state.confirmed_dist = sel_dist
                    st.rerun() # This forces the page to refresh and closes the keyboard/list

    with top_col2:
        sel_crops = st.multiselect(
            "🌱 SELECT CROPS", 
            options=sorted(crop_df['Crop Name'].unique()), 
            default=None
         )
        if sel_crops:
           with st.spinner(f"Running district-crop suit analysis for {sel_crops}..."):
                time.sleep(4)
        

    with top_col3:
        sel_season = st.radio("🗓️ SEASON", ["Rabi", "Summer"], horizontal=True)

    if sel_dist == "Select a District":
        st.warning("Please select a district above to begin the analysis.")
        st.stop()

    # --- DISTRICT SUMMARY CARD ---
    d_data = dist_df[dist_df['District'] == sel_dist].iloc[0]

    st.markdown(f"""
    <div class="district-card">
        <h2 style="margin:0; font-size:1.1rem;">Active Analysis: {sel_dist} District</h2>
        <p style="margin:10px 0 0 0; color:white; font-size:0.9rem;">
            <b>AEZ:</b> <span class="sky-blue-val">{d_data.get('AEZ')}</span> | 
            <b>Texture:</b> <span class="sky-blue-val">{d_data.get('Soil Texture')}</span> | 
            <b>pH:</b> <span class="sky-blue-val">{d_data.get('pH avg')}</span> | 
            <b>Salinity:</b> <span class="sky-blue-val">{d_data.get('Soil Salinity')}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    report_data = []
    
    if not sel_crops:
        st.info("Please select one or more crops to view suitability scores.")
    else:
        # --- YOUR EXISTING CROP LOOP ---
        for crop in sel_crops:
            c_data = crop_df[crop_df['Crop Name'] == crop].iloc[0]
            
            # (Calculation logic remains exactly the same...)
            score, final_reason, status, aez_match, d_sal, c_sal_limit, raw_list = calculate_suitability_v3(d_data, c_data, sel_season)
            
            # Extraction of scores
            t_score = next((float(item['Score'].split('/')[0]) for item in raw_list if item['Parameter'] == "Avg Temp"), 15)
            tex_score = next((float(item['Score'].split('/')[0]) for item in raw_list if item['Parameter'] == "Root Zone Suitability"), 10)
            s_score = next((float(item['Score'].split('/')[0]) for item in raw_list if item['Parameter'] == "Salinity"), 10)
            
            # Silent Insight Generation
            reasons1 = []
            if not aez_match: reasons1.append("outside primary AEZ target zones")
            if t_score < 15: reasons1.append("temperatures outside metabolic optimum")
            if tex_score < 0: 
                texture = d_data.get('Soil Texture', 'unknown')
                reasons1.append(f"mechanical barrier from {texture} texture")
            if s_score <= 0: reasons1.append("salinity exceeds variety safety threshold")
            
            silent_insight = f"Analysis: {crop} is optimized." if not reasons1 else f"Analysis: {int(score)}% due to {', '.join(reasons1)}."

            report_data.append({
                "crop": crop,
                "score": score,
                "insight": silent_insight,
                "table_data": raw_list
            })
            
            if final_reason:
               st.error(f"🛑 **TERMINATED:** {final_reason}")
    
    # Dynamic Caption: Checks what is inside final_reason to show the right message
               if "Heat" in final_reason and "Salinity" in final_reason:
                st.caption("Crop is biologically unsuitable due to heat and salt stress.")
               elif "Salinity" in final_reason:
                st.caption("Lethal osmotic pressure. The crop cannot intake water due to salt concentration.")
               elif "Heat" in final_reason:        
                st.caption("Critical thermal limit reached. Pollen sterility or metabolic failure likely.")
            else:
    # Only show the expander/details if the crop isn't terminated
               st.success("✅ Environment is within survival thresholds.")            # --- UI Display ---
            st.markdown(f'<div class="crop-header-btn"><span>🌱 {crop}</span><span class="percentage-badge">{score}%</span></div>', unsafe_allow_html=True)
            st.progress(score/100)
            with st.expander("🔍 VIEW TECHNICAL DATA & AI ANALYSIS"):
                st.table(pd.DataFrame(raw_list))
                run_ai_insights(d_data, crop, score, aez_match, t_score, tex_score, s_score, sel_season)

        # --- EXPORT SECTION AT BOTTOM ---
        st.markdown("---")
        if report_data:
            pdf_bytes = generate_report(sel_dist, report_data)
            st.download_button(
                label="📥 Download Full PDF Report",
                data=pdf_bytes,
                file_name=f"Report_{sel_dist}.pdf",
                mime="application/pdf",
                key=f"download_btn_{sel_dist}_v1"
            )            
        "Developed by Emdadul Haque Emon"
if __name__ == "__main__":

  main()
