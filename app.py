import streamlit as st
from ultralytics import YOLO
from PIL import Image
import tempfile
import time

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vehicle Damage Detection",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# Model loading
# ----------------------------------------------------------------------------
@st.cache_resource
def load_model():
    return YOLO("models/best.pt")

model = load_model()

# ----------------------------------------------------------------------------
# Styling — inspection HUD aesthetic
# ----------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
    --bg:        #0B0D10;
    --panel:     #14181D;
    --border:    #1F2733;
    --text:      #E8EAED;
    --muted:     #7A8699;
    --signal:    #FF5630;
    --signal-dim:#7A2E1F;
    --clear:     #3DDC84;
}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

.stApp {
    background: var(--bg);
}

/* Kill default streamlit chrome */
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }

/* ---- Top scanner bar ---- */
.scan-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 18px;
    margin-bottom: 6px;
}
.scan-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.65rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 10px;
}
.scan-title .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: var(--signal);
    box-shadow: 0 0 8px var(--signal);
    display: inline-block;
}
.scan-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.02em;
}

/* ---- Section labels ---- */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ---- Upload zone ---- */
[data-testid="stFileUploaderDropzone"] {
    background: var(--panel) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--signal) !important;
}
[data-testid="stFileUploader"] section { background: transparent; }
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: var(--muted) !important;
}

/* ---- Browse button ---- */
[data-testid="stFileUploader"] button {
    background: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}
[data-testid="stFileUploader"] button:hover {
    background: var(--signal) !important;
    color: #0B0D10 !important;
    border-color: var(--signal) !important;
}
[data-testid="stFileUploader"] button:focus {
    box-shadow: 0 0 0 1px var(--signal) !important;
}

/* ---- Image frames ---- */
.frame-wrap {
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    background: var(--panel);
    position: relative;
}
.frame-wrap img { display: block; }
.frame-tag {
    position: absolute;
    top: 10px; left: 10px;
    background: rgba(11,13,16,0.85);
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 3px;
    text-transform: uppercase;
    z-index: 2;
}

/* ---- Scan sweep animation ---- */
@keyframes sweep {
    0%   { top: -2%; }
    100% { top: 100%; }
}
.sweep-line {
    position: absolute;
    left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--signal) 50%, transparent);
    box-shadow: 0 0 12px var(--signal);
    animation: sweep 1.4s ease-in-out infinite;
    z-index: 3;
}

/* ---- Result manifest rows ---- */
.result-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 4px;
    border-bottom: 1px solid var(--border);
}
.result-row:last-child { border-bottom: none; }
.result-index {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    width: 28px;
    flex-shrink: 0;
}
.result-name {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.92rem;
    width: 200px;
    flex-shrink: 0;
    text-transform: capitalize;
}
.result-bar-track {
    flex: 1;
    height: 5px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
}
.result-bar-fill {
    height: 100%;
    background: var(--signal);
    border-radius: 3px;
}
.result-conf {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--text);
    width: 64px;
    text-align: right;
    flex-shrink: 0;
}

/* ---- Clear status panel ---- */
.clear-panel {
    border: 1px solid var(--border);
    border-left: 3px solid var(--clear);
    background: var(--panel);
    padding: 16px 18px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.clear-panel .icon { color: var(--clear); font-size: 1.3rem; }
.clear-panel .msg {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
}
.clear-panel .sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--muted);
}

/* ---- Stat strip ---- */
.stat-strip {
    display: flex;
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 28px;
}
.stat-cell {
    flex: 1;
    background: var(--panel);
    padding: 14px 18px;
}
.stat-cell .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.stat-cell .value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--signal);
}
.stat-cell .value.signal { color: var(--signal); }
.stat-cell .value.clear { color: var(--clear); }

/* ---- Footer ---- */
.footer-note {
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.03em;
}

/* Hide default spinner text styling oddities */
.stSpinner > div { color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown("""
<div class="scan-header">
    <div class="scan-title"><span class="dot"></span>VEHICLE DAMAGE DETECTION</div>
    <div class="scan-sub">YOLOv8 · OBJECT DETECTION</div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ----------------------------------------------------------------------------
# Upload
# ----------------------------------------------------------------------------
st.markdown('<div class="section-label">01 / INPUT</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop a vehicle image to scan",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed",
)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.write("")
    st.markdown('<div class="section-label">02 / SCAN RESULT</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        placeholder1 = st.empty()
        with placeholder1.container():
            st.markdown(
                f'<div class="frame-wrap"><div class="frame-tag">Source</div>'
                f'<div class="sweep-line"></div></div>',
                unsafe_allow_html=True,
            )
            st.image(image, use_container_width=True)

    with col2:
        placeholder2 = st.empty()
        with placeholder2.container():
            st.markdown('<div class="frame-wrap"><div class="frame-tag">Detection</div></div>', unsafe_allow_html=True)

    with st.spinner(""):
        scan_start = time.time()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image.save(tmp.name)
            results = model(tmp.name)

        result = results[0]
        plotted_img = result.plot()

        # Hold the sweep animation just long enough to register as a real scan
        elapsed = time.time() - scan_start
        min_duration = 1.1
        if elapsed < min_duration:
            time.sleep(min_duration - elapsed)

    # Clear the sweep overlay, show final frames
    with col1:
        st.markdown(
            '<div class="frame-wrap"><div class="frame-tag">Source</div></div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.image(plotted_img, use_container_width=True)

    st.write("")

    # ----------------------------------------------------------------------
    # Stats strip
    # ----------------------------------------------------------------------
    n_detections = len(result.boxes)
    if n_detections > 0:
        confs = [float(b.conf[0]) for b in result.boxes]
        avg_conf = sum(confs) / len(confs)
        max_conf = max(confs)
        status_val = '<span class="value signal">FLAGGED</span>'
    else:
        avg_conf = 0
        max_conf = 0
        status_val = '<span class="value clear">CLEAR</span>'

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-cell">
            <div class="label">Status</div>
            {status_val}
        </div>
        <div class="stat-cell">
            <div class="label">Regions Detected</div>
            <div class="value">{n_detections}</div>
        </div>
        <div class="stat-cell">
            <div class="label">Avg Confidence</div>
            <div class="value">{avg_conf*100:.1f}%</div>
        </div>
        <div class="stat-cell">
            <div class="label">Peak Confidence</div>
            <div class="value">{max_conf*100:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ----------------------------------------------------------------------
    # Detection manifest
    # ----------------------------------------------------------------------
    st.markdown('<div class="section-label">03 / DETECTION LOG</div>', unsafe_allow_html=True)

    if n_detections == 0:
        st.markdown("""
        <div class="clear-panel">
            <span class="icon">✓</span>
            <div>
                <div class="msg">No damage detected</div>
                <div class="sub">Scan completed · vehicle surface within normal parameters</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        rows = ""

        for i, box in enumerate(result.boxes, start=1):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            damage_type = model.names[cls_id]
            pct = conf * 100

            rows += (
                f'<div class="result-row">'
                f'<div class="result-index">{i:02d}</div>'
                f'<div class="result-name">{damage_type}</div>'
                f'<div class="result-bar-track">'
                f'<div class="result-bar-fill" style="width:{pct}%;"></div>'
                f'</div>'
                f'<div class="result-conf">{pct:.1f}%</div>'
                f'</div>'
            )

        st.markdown(f'<div>{rows}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="footer-note">MODEL: best.pt &nbsp;·&nbsp; INFERENCE: YOLOv8 &nbsp;·&nbsp; '
            'BUILT WITH STREAMLIT</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown("""
    <div style="margin-top: 24px; padding: 32px; border: 1px dashed var(--border);
                border-radius: 6px; text-align: center; color: var(--muted);
                font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
        AWAITING INPUT — upload a vehicle image above to begin scan
    </div>
    """, unsafe_allow_html=True)
