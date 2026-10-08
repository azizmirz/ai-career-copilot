# streamlit_app.py

import streamlit as st
import hashlib
import requests
import tempfile
import os
import uuid
from app.tools.cv_parser import extract_text_from_pdf

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Career Co-Pilot", page_icon="🤖", layout="wide")


# ─── Köməkçi funksiyalar ──────────────────────────────────
def get_error_detail(resp):
    try:
        return resp.json().get("detail", resp.text)
    except Exception:
        return resp.text


def auth_headers():
    """JWT token-i Authorization header-ə əlavə edir."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def validate_jd_text(text: str):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    if st.session_state.get("jd_text_hash") == text_hash:
        return st.session_state.get("jd_valid")
    try:
        resp = requests.post(
            f"{API_URL}/v1/jd/validate",
            json={"text": text},
            headers=auth_headers(),
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return None
    st.session_state.jd_text_hash = text_hash
    if resp.status_code == 200:
        st.session_state.jd_valid = resp.json()["is_valid_jd"]
        return st.session_state.jd_valid
    return None


# ─── Session state inisializasiyası ──────────────────────
defaults = {
    "token": None,
    "user_email": None,
    "user_full_name": None,
    "session_id": None,
    "cv_ready": False,
    "cv_owner": None,
    "cv_filename": None,
    "cv_hash": None,
    "jd_text_hash": None,
    "jd_valid": None,
    "show_history": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "session_id" not in st.session_state or st.session_state.session_id is None:
    st.session_state.session_id = str(uuid.uuid4())


# ─── Auth UI ──────────────────────────────────────────────
def show_auth_page():
    st.title("🤖 AI Career Co-Pilot")
    st.caption(
        "CV-nizi və iş elanını yükləyin — AI vasitəsilə namizədliyinizin uyğunluğu analiz edilsin."
    )
    st.divider()

    tab_login, tab_register = st.tabs(["🔑 Giriş", "📝 Qeydiyyat"])

    with tab_login:
        st.subheader("Hesaba daxil ol")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Şifrə", type="password", key="login_password")

        if st.button("Giriş et", use_container_width=True, type="primary"):
            if not email or not password:
                st.error("Email və şifrənizi daxil edin.")
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/auth/login",
                        json={"email": email, "password": password},
                        timeout=10,
                    )
                except requests.exceptions.ConnectionError:
                    st.error("❌ Sistem xətası: Backend-ə qoşula bilmədi.")
                    st.stop()

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.session_state.user_full_name = data["full_name"]
                    st.rerun()
                else:
                    st.error(f"❌ {get_error_detail(resp)}")

    with tab_register:
        st.subheader("Yeni hesab yarat")
        full_name = st.text_input("Ad Soyad", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Şifrə", type="password", key="reg_password")

        if st.button("Qeydiyyat", use_container_width=True, type="primary"):
            if not full_name or not reg_email or not reg_password:
                st.error("Bütün sahələri doldurun.")
            elif len(reg_password) < 6:
                st.error("Şifrə ən azı 6 simvol olmalıdır.")
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/auth/register",
                        json={
                            "email": reg_email,
                            "password": reg_password,
                            "full_name": full_name,
                        },
                        timeout=10,
                    )
                except requests.exceptions.ConnectionError:
                    st.error("❌ Sistem xətası: Backend-ə qoşula bilmədi.")
                    st.stop()

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.session_state.user_full_name = data["full_name"]
                    st.success("✅ Qeydiyyat uğurludur!")
                    st.rerun()
                else:
                    st.error(f"❌ {get_error_detail(resp)}")


# ─── Tarixçə UI ───────────────────────────────────────────
def show_history():
    st.subheader("📋 Keçmiş Analizlər")

    resp = None
    try:
        resp = requests.get(
            f"{API_URL}/v1/history",
            headers=auth_headers(),
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        st.error("❌ Sistem xətası: Backend-ə qoşula bilmədi.")
        return

    if resp.status_code != 200:
        st.error(f"❌ {get_error_detail(resp)}")
        return

    records = resp.json()

    if not records:
        st.info("Hələ heç bir analiz yoxdur.")
        return

    for r in records:
        company = r.get("company") or "Naməlum Şirkət"
        with st.expander(
            f"🗂 {r['cv_owner']} → {r['job_title']} @ {company} | "
            f"{r['match_score']}% | {r['created_at'][:10]}"
        ):
            score = r["match_score"]
            level = r["match_level"]
            color_map = {
                "Poor": "🔴",
                "Fair": "🟠",
                "Good": "🟡",
                "Strong": "🟢",
                "Excellent": "⭐",
            }
            st.metric("Uyğunluq Skoru", f"{score}%")
            st.progress(score / 100)
            st.write(f"{color_map.get(level, '🔵')} **{level}**")
            st.info(f"📝 {r['summary']}")

            col1, col2 = st.columns(2)
            with col1:
                st.write("✅ **Uyğun Bacarıqlar:**")
                for s in r["matched_skills"]:
                    st.success(f"**{s['skill']}** — {s['evidence']}")
            with col2:
                st.write("❌ **Çatışmayanlar:**")
                for s in r["missing_skills"]:
                    if s["importance"] == "required":
                        st.error(f"**{s['skill']}** ⚠️ Vacib")
                    else:
                        st.warning(f"**{s['skill']}** 💡 Üstünlük")

            st.write("💡 **Tövsiyələr:**")
            for i, rec in enumerate(r["recommendations"], 1):
                st.write(f"**{i}.** {rec}")


# ─── Əsas UI ──────────────────────────────────────────────
def show_main_app():
    # ── Header ──
    col_title, col_user = st.columns([4, 1])
    with col_title:
        st.title("🤖 AI Career Co-Pilot")
        st.caption(
            "CV-nizi və iş elanını yükləyin — AI vasitəsilə namizədliyinizin uyğunluğu analiz edilsin."
        )
    with col_user:
        st.write(f"👤 {st.session_state.user_full_name or st.session_state.user_email}")
        col_hist, col_logout = st.columns(2)
        with col_hist:
            hist_label = "🏠 Ana səhifə" if st.session_state.show_history else "📋 Tarixçə"
            if st.button(hist_label):
                st.session_state.show_history = not st.session_state.show_history
                st.rerun()
        with col_logout:
            if st.button("🚪 Çıxış"):
                for key in defaults:
                    st.session_state[key] = None
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

    st.divider()

    # ── Tarixçə paneli ──
    if st.session_state.show_history:
        show_history()
        st.divider()
        return

    # ── Sol / Sağ Panel ──
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📄 CV")
        cv_file = st.file_uploader("CV-ni PDF formatında yükləyin", type=["pdf"], key="cv_upload")

        if cv_file:
            cv_bytes = cv_file.read()
            current_hash = hashlib.md5(cv_bytes).hexdigest()

            if current_hash != st.session_state.cv_hash:
                resp = None
                with st.spinner("⚙️ CV analiz edilir..."):
                    files = {"file": (cv_file.name, cv_bytes, "application/pdf")}
                    data = {"session_id": st.session_state.session_id}
                    try:
                        resp = requests.post(
                            f"{API_URL}/v1/cv/upload",
                            files=files,
                            data=data,
                            headers=auth_headers(),
                            timeout=60,
                        )
                    except requests.exceptions.ConnectionError:
                        resp = None

                if resp is None:
                    st.error("❌ Sistem xətası: Backend-ə qoşula bilmədi.")
                    st.stop()
                if resp.status_code != 200:
                    st.error(f"❌ {get_error_detail(resp)}")
                    st.stop()

                data_resp = resp.json()
                st.session_state.cv_owner = data_resp["cv_owner"]
                st.session_state.cv_filename = cv_file.name
                st.session_state.cv_hash = current_hash
                st.session_state.cv_ready = True

                st.success(f"✅ {cv_file.name} — {st.session_state.cv_owner}")
            else:
                st.success(
                    f"✅ {st.session_state.cv_filename} — "
                    f"{st.session_state.cv_owner} (hazırdır)"
                )

        elif st.session_state.cv_ready:
            st.info(
                f"📄 {st.session_state.cv_filename} — " f"{st.session_state.cv_owner} (hazırdır)"
            )

    with right_col:
        st.subheader("💼 Job Description")
        jd_input_type = st.radio(
            "Hansı formatda yükləmək istəyirsiz?",
            ["📋 Mətn yapışdır", "📄 PDF yüklə"],
            horizontal=True,
        )

        jd_text = None

        if jd_input_type == "📋 Mətn yapışdır":
            jd_text = st.text_area(
                "İş elanının mətnini bura yapışdırın",
                height=200,
                placeholder="Job Title: AI Engineer\n\nRequirements:\n- Python\n...",
            )
        else:
            jd_file = st.file_uploader(
                "JD-ni PDF formatında yükləyin", type=["pdf"], key="jd_upload"
            )
            if jd_file:
                jd_bytes = jd_file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(jd_bytes)
                    tmp_path = tmp.name
                jd_text = extract_text_from_pdf(tmp_path)
                os.unlink(tmp_path)
                st.success(f"✅ {jd_file.name} yükləndi")

        if jd_text and jd_text.strip():
            with st.spinner("🔍 Sənəd növü yoxlanılır..."):
                is_valid = validate_jd_text(jd_text)
            if is_valid is False:
                st.error("⚠️ Zəhmət olmasa düzgün iş elanı verin.")
            elif is_valid is True:
                st.success("✅ Job Description aşkarlandı")

    st.divider()

    jd_ready = bool(jd_text and jd_text.strip()) and st.session_state.jd_valid is not False

    analyze_btn = st.button(
        "🔍 Analiz Et",
        disabled=not (st.session_state.cv_ready and jd_ready),
        use_container_width=True,
        type="primary",
    )

    if not st.session_state.cv_ready:
        st.warning("⬆️ Zəhmət olmasa CV-nizi yükləyin")
    elif not jd_text or not jd_text.strip():
        st.warning("⬆️ Zəhmət olmasa Job Description verin")
    elif st.session_state.jd_valid is False:
        st.warning("⚠️ Düzgün Job Description verilməyənə qədər analiz edilə bilməz")

    if analyze_btn:
        resp = None
        with st.spinner("🤖 Uyğunluq analiz edilir..."):
            try:
                resp = requests.post(
                    f"{API_URL}/v1/match",
                    json={
                        "session_id": st.session_state.session_id,
                        "jd_text": jd_text,
                    },
                    headers=auth_headers(),
                    timeout=120,
                )
            except requests.exceptions.ConnectionError:
                resp = None

        if resp is None:
            st.error("❌ Sistem xətası: Backend-ə qoşula bilmədi.")
            st.stop()
        if resp.status_code != 200:
            st.error(f"❌ {get_error_detail(resp)}")
            st.stop()

        result = resp.json()
        analysis = result["analysis"]
        parsed_jd = result["parsed_jd"]

        st.divider()
        st.subheader("📊 Analiz Nəticəsi")
        company = parsed_jd.get("company") or "Naməlum Şirkət"
        st.caption(f"📋 {result['cv_owner']} → " f"💼 {parsed_jd.get('job_title')} @ {company}")

        score = analysis["match_score"]
        level = analysis["match_level"]

        score_col, level_col = st.columns([3, 1])
        with score_col:
            st.metric("Uyğunluq Skoru", f"{score}%")
            st.progress(score / 100)
        with level_col:
            color_map = {
                "Poor": "🔴",
                "Fair": "🟠",
                "Good": "🟡",
                "Strong": "🟢",
                "Excellent": "⭐",
            }
            st.metric("Səviyyə", f"{color_map.get(level, '🔵')} {level}")

        st.divider()
        st.info(f"📝 **Xülasə:** {analysis['summary']}")
        st.divider()

        match_col, miss_col = st.columns(2)
        with match_col:
            st.subheader("✅ Uyğun Bacarıqlar")
            for item in analysis["matched_skills"]:
                st.success(f"**{item['skill']}** — {item['evidence']}")
        with miss_col:
            st.subheader("❌ Çatışmayanlar")
            for item in analysis["missing_skills"]:
                if item["importance"] == "required":
                    st.error(f"**{item['skill']}** ⚠️ Vacib")
                else:
                    st.warning(f"**{item['skill']}** 💡 Üstünlük")

        st.divider()
        st.subheader("💡 Tövsiyələr")
        for i, rec in enumerate(analysis["recommendations"], 1):
            st.write(f"**{i}.** {rec}")

        # ── Evaluation Metrics ────────────────────────────
        if "evaluation" in result:
            ev = result["evaluation"]
            st.divider()
            st.subheader("🔬 Analiz Keyfiyyəti")
            st.caption("Bu bölmə analiz nəticəsinin etibarlılığını ölçür")

            e1, e2, e3, e4 = st.columns(4)
            with e1:
                st.metric(
                    "Bacarıq Əhatəsi",
                    f"{ev['skill_coverage_rate']}%",
                    help="CV JD tələblərinin neçə faizini qarşılayır",
                )
            with e2:
                st.metric(
                    "Kritik Boşluq",
                    f"{ev['critical_gap_rate']}%",
                    help="Vacib tələblərdən nə qədəri çatışmır (aşağı = yaxşı)",
                )
            with e3:
                st.metric(
                    "Analiz Etibarlılığı",
                    f"{ev['match_confidence']}%",
                    help="LLM skoru ilə hesablanmış skor arasındakı uyğunluq",
                )
            with e4:
                st.metric(
                    "Tövsiyə Keyfiyyəti",
                    f"{ev['recommendation_quality']}%",
                    help="Tövsiyələrin nə qədəri konkret bacarıqlara aiddir",
                )

            st.info(
                f"📊 **Ümumi Keyfiyyət: {ev['overall_quality_score']}%** "
                f"— {ev['interpretation']}"
            )


# ─── Routing ──────────────────────────────────────────────
if st.session_state.token is None:
    show_auth_page()
else:
    show_main_app()
