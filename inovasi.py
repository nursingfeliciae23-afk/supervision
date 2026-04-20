import streamlit as st
import pandas as pd
import smtplib
import urllib.parse
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==========================================
# 1. INISIALISASI DATA (SESSION STATE)
# ==========================================
# Ini wajib ada agar Tab 3 tidak error saat mencari data
if 'df_sdm' not in st.session_state:
    st.session_state.df_sdm = pd.DataFrame({"Nama Perawat": ["Perawat A", "Perawat B", "Perawat C"]})
if 'df_jadwal_supervisi' not in st.session_state:
    st.session_state.df_jadwal_supervisi = pd.DataFrame(columns=["Tanggal", "Perawat", "Prosedur", "Supervisor", "Status"])
if 'log_supervisi' not in st.session_state:
    st.session_state.log_supervisi = []
if 'df_kpi' not in st.session_state:
    st.session_state.df_kpi = pd.DataFrame({
        "Nama Perawat": ["Perawat A", "Perawat B", "Perawat C"], 
        "Rata-rata Skor": [85.5, 92.0, 78.5]
    })
if 'log_catatan_karu' not in st.session_state:
    st.session_state.log_catatan_karu = []

# ==========================================
# 2. KONFIGURASI & DATA STANDAR BAKU
# ==========================================
SENDER_EMAIL = "email_anda@gmail.com"
SENDER_PASSWORD = "password_aplikasi_anda"

SOP_PERASAT = {
    "Pemasangan Infus": [
        "Memasang torniket dan mencari vena yang tepat",
        "Melakukan desinfeksi area insersi dengan benar (sirkuler dari dalam ke luar)",
        "Menginsersikan jarum/abocath dengan sudut 15-30 derajat",
        "Melihat adanya blood return dan menarik mandrin perlahan",
        "Melakukan fiksasi transparan/plester dengan aman",
        "Menyambungkan selang infus dan mengatur tetesan sesuai advis"
    ],
    "Perawatan Luka (Wound Care)": [
        "Membuka balutan lama dengan hati-hati menggunakan pinset",
        "Mengkaji kondisi luka (warna, eksudat, bau, ukuran)",
        "Membersihkan luka dengan cairan fisiologis (NaCl 0.9%)",
        "Melakukan debridement/mengangkat jaringan nekrotik (jika perlu)",
        "Mengaplikasikan salep/dressing primer sesuai jenis luka",
        "Menutup dan memfiksasi balutan baru dengan rapi"
    ],
    "Pemasangan Kateter Urine": [
        "Memposisikan pasien (Dorsal recumbent) & memasang perlak",
        "Melakukan vulva/penis hygiene dari arah atas ke bawah",
        "Mengoleskan jelly pada kateter dan memasukkannya perlahan",
        "Memastikan urine keluar dan menampungnya di bengkok",
        "Mengembangkan balon fiksasi dengan aquabides sesuai takaran",
        "Menyambungkan kateter ke urine bag dan fiksasi di paha"
    ]
}

def send_email(to_email, nama_perawat, supervisor, perasat, skor, feedback):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Hasil Supervisi Klinis ({perasat}) - {nama_perawat}"

        body = f"""Halo {nama_perawat},
        
Berikut adalah hasil supervisi tindakan keperawatan Anda pada {datetime.now().strftime('%d-%m-%Y')}.
        
Tindakan / Perasat: {perasat}
Supervisor: {supervisor}
Skor Kepatuhan SOP: {skor}/100
        
Evaluasi & Langkah yang Terlewat:
{feedback}
        
Terima kasih. Salam, Manajemen Keperawatan"""

        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        return False

# ==========================================
# 3. UI UTAMA STREAMLIT
# ==========================================
st.set_page_config(page_title="Modul Supervisi Klinis", layout="wide")

st.title("🏥 Modul Supervisi Klinis Keperawatan")
st.markdown("Penilaian komprehensif berbasis Standar Operasional Prosedur (SOP) melalui 3 Fase.")

# Membuat 3 Tab (Gabungan dari kode Anda)
tab1, tab2, tab3 = st.tabs([
    "📋 Form Supervisi Tindakan", 
    "📊 Riwayat & Database", 
    "📈 Matriks Kinerja & Penjadwalan"
])

# ------------------------------------------
# TAB 1: FORM PENILAIAN SOP
# ------------------------------------------
with tab1:
    jenis_perasat = st.selectbox("💉 Pilih Tindakan (Perasat) yang Disupervisi:", list(SOP_PERASAT.keys()))
    st.markdown("---")
    
    with st.form("form_supervisi_baku"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Data Perawat")
            nama_disupervisi = st.text_input("Nama Perawat Pelaksana")
            email_disupervisi = st.text_input("Email Perawat (Untuk Laporan)")
            no_wa_perawat = st.text_input("Nomor WA (Contoh: 62812...)")
            
        with col2:
            st.subheader("Data Supervisor")
            nama_supervisor = st.text_input("Nama Supervisor")
            peran_supervisor = st.selectbox("Peran Supervisor", ["Ketua Tim (Katim)", "Kepala Ruangan (Karu)"])
            tanggal_supervisi = st.date_input("Tanggal Supervisi")
        
        st.markdown("---")
        st.subheader(f"Instrumen Penilaian: {jenis_perasat}")
        
        langkah_terlewat = []
        
        st.markdown("**A. Fase Pra-Interaksi & Orientasi**")
        pra1 = st.checkbox("1. Mencuci tangan dan menyiapkan alat sesuai kebutuhan")
        pra2 = st.checkbox("2. Mengidentifikasi pasien dengan benar (Nama & RM)")
        pra3 = st.checkbox("3. Menjelaskan tujuan, prosedur, dan inform consent")
        
        st.markdown(f"**B. Fase Kerja ({jenis_perasat})**")
        langkah_kerja_cek = []
        for i, langkah in enumerate(SOP_PERASAT[jenis_perasat]):
            cek = st.checkbox(f"{i+4}. {langkah}")
            langkah_kerja_cek.append((langkah, cek))
            
        st.markdown("**C. Fase Terminasi & Dokumentasi**")
        term1 = st.checkbox("Mengevaluasi respon pasien & merapikan alat")
        term2 = st.checkbox("Mencuci tangan setelah tindakan")
        term3 = st.checkbox("Mendokumentasikan tindakan dan respon di rekam medis")
        
        st.markdown("---")
        catatan_tambahan = st.text_area("Catatan Tambahan Supervisor (Opsional)")
        validasi = st.checkbox("Saya memvalidasi bahwa penilaian ini dilakukan secara objektif.")
        submit_button = st.form_submit_button(label="Simpan Penilaian", type="primary")

    if submit_button:
        if not nama_disupervisi or not nama_supervisor:
            st.warning("Mohon lengkapi Nama Perawat dan Nama Supervisor!")
        elif not validasi:
            st.warning("Centang kotak validasi di bagian paling bawah!")
        else:
            if not pra1: langkah_terlewat.append("Cuci tangan & persiapan alat")
            if not pra2: langkah_terlewat.append("Identifikasi pasien")
            if not pra3: langkah_terlewat.append("Edukasi & inform consent")
            
            for langkah, dilakukan in langkah_kerja_cek:
                if not dilakukan: langkah_terlewat.append(langkah)
                
            if not term1: langkah_terlewat.append("Evaluasi respon")
            if not term2: langkah_terlewat.append("Cuci tangan pasca tindakan")
            if not term3: langkah_terlewat.append("Dokumentasi")
            
            total_langkah = 3 + len(SOP_PERASAT[jenis_perasat]) + 3
            langkah_dilakukan = total_langkah - len(langkah_terlewat)
            skor_persen = round((langkah_dilakukan / total_langkah) * 100, 2)
            
            if len(langkah_terlewat) == 0:
                teks_feedback = "Semua tahapan dilakukan sesuai SOP.\n"
            else:
                teks_feedback = "Langkah terlewat:\n" + "\n".join([f"- {lt}" for lt in langkah_terlewat])
            
            data_baru = {
                "Tanggal": tanggal_supervisi.strftime('%Y-%m-%d'),
                "Nama Perawat": nama_disupervisi,
                "Supervisor": nama_supervisor,
                "Tindakan": jenis_perasat,
                "Skor SOP (%)": skor_persen,
                "Langkah Terlewat": ", ".join(langkah_terlewat) if langkah_terlewat else "Sesuai SOP"
            }
            
            df_baru = pd.DataFrame([data_baru])
            if os.path.exists('db_supervisi_klinis.csv'):
                df_lama = pd.read_csv('db_supervisi_klinis.csv')
                df_final = pd.concat([df_lama, df_baru], ignore_index=True)
            else:
                df_final = df_baru
            df_final.to_csv('db_supervisi_klinis.csv', index=False)
            st.success(f"✅ Tersimpan! Skor: {skor_persen}%")

# ------------------------------------------
# TAB 2: DATABASE & RIWAYAT CSV
# ------------------------------------------
with tab2:
    st.header("🗄️ Database & Riwayat Supervisi")
    if os.path.exists('db_supervisi_klinis.csv'):
        df_show = pd.read_csv('db_supervisi_klinis.csv')
        st.subheader("📋 Tabel Data Observasi")
        st.dataframe(df_show, use_container_width=True)
        csv = df_show.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Unduh CSV", data=csv, file_name='data_supervisi.csv', mime='text/csv')
    else:
        st.info("Belum ada data di CSV.")

# ------------------------------------------
# TAB 3: MATRIKS KINERJA & PENJADWALAN (Bagian yang Error Sebelumnya)
# ------------------------------------------
with tab3:
    st.header("📋 Matriks Kinerja & Perencanaan Supervisi")
    st.caption("Pantau rencana supervisi, KPI bulanan, dan buku saku Karu.")

    t3_jadwal, t3_kpi, t3_catatan = st.tabs([
        "🗓️ Jadwal Supervisi",
        "📊 Matriks KPI Staf", 
        "📒 Catatan Pembinaan Karu"
    ])

    with t3_jadwal:
        st.subheader("Matrix Rencana Supervisi Klinis")
        st.dataframe(st.session_state.df_jadwal_supervisi, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("➕ Tambah Rencana Baru")
        with st.form("form_tambah_jadwal"):
            c1, c2, c3 = st.columns(3)
            with c1:
                tgl_rencana = st.date_input("Tanggal Rencana")
                staf_target = st.selectbox("Perawat Target", st.session_state.df_sdm["Nama Perawat"])
            with c2:
                pros_target = st.selectbox("Prosedur/SPO", list(SOP_PERASAT.keys()) + ["Lainnya"])
                spv_name = st.selectbox("Supervisor", ["Karu", "Katim A", "Katim B"])
            with c3:
                catatan_rencana = st.text_area("Catatan Khusus", placeholder="Misal: Fokus teknik aseptik")
            
            if st.form_submit_button("Daftarkan ke Jadwal"):
                new_row = pd.DataFrame({
                    "Tanggal": [tgl_rencana.strftime('%d-%m-%Y')],
                    "Perawat": [staf_target],
                    "Prosedur": [pros_target],
                    "Supervisor": [spv_name],
                    "Status": ["Terjadwal"]
                })
                st.session_state.df_jadwal_supervisi = pd.concat([st.session_state.df_jadwal_supervisi, new_row], ignore_index=True)
                st.success(f"✅ Jadwal untuk {staf_target} berhasil dibuat!")
                st.rerun()

    with t3_kpi:
        st.subheader("Rapor Kinerja (KPI) Bulanan")
        st.dataframe(st.session_state.df_kpi, use_container_width=True, hide_index=True)
        
        if not st.session_state.df_kpi.empty:
            best_nurse = st.session_state.df_kpi.loc[st.session_state.df_kpi["Rata-rata Skor"].idxmax()]
            st.success(f"🏆 **Perawat Berkinerja Terbaik Bulan Ini:** {best_nurse['Nama Perawat']} (Skor: {best_nurse['Rata-rata Skor']})")

    with t3_catatan:
        st.subheader("Buku Saku Pembinaan Karu")
        with st.form("form_catatan"):
            kat = st.selectbox("Kategori", ["Apresiasi", "Teguran Lisan", "Coaching"])
            staf = st.selectbox("Staf", st.session_state.df_sdm["Nama Perawat"])
            isi = st.text_area("Detail")
            if st.form_submit_button("Simpan Catatan"):
                st.session_state.log_catatan_karu.append({"Waktu": datetime.now().strftime('%d/%m/%Y'), "Staf": staf, "Kategori": kat, "Isi": isi})
                st.success("Tercatat!")
                st.rerun()

        if st.session_state.log_catatan_karu:
            st.table(pd.DataFrame(st.session_state.log_catatan_karu))