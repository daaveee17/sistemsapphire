from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
import joblib
import numpy as np
import os
import json
import subprocess
from io import BytesIO
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Gunakan environment variable untuk secret key di production
app.secret_key = os.environ.get('SECRET_KEY', 'sapphire-residence-tegal-2026-super-secret')

# -------------------------------------------------------------------
# KONFIGURASI DATABASE MYSQL (DENGAN XAMPP)
# -------------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost:3307/sapphire_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi Server
# app.config['SERVER_NAME'] = 'localhost:5000' # Tidak digunakan agar 127.0.0.1 tetap jalan

db = SQLAlchemy(app)

# -------------------------------------------------------------------
# MODEL DATABASE
# -------------------------------------------------------------------
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    no_hp = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    no_hp = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Blok(db.Model):
    __tablename__ = 'bloks'
    id = db.Column(db.Integer, primary_key=True)
    nama_blok = db.Column(db.String(50), nullable=False)
    tahap = db.Column(db.String(20), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Properti(db.Model):
    __tablename__ = 'properti'
    id = db.Column(db.Integer, primary_key=True)
    blok_id = db.Column(db.Integer, db.ForeignKey('bloks.id', ondelete='CASCADE'), nullable=False)
    nomor_rumah = db.Column(db.String(10), nullable=False)
    tipe_rumah = db.Column(db.String(20), nullable=False)
    luas_bangunan = db.Column(db.Float, nullable=False)
    luas_tanah = db.Column(db.Float, nullable=False)
    kamar_tidur = db.Column(db.Integer, nullable=False)
    kamar_mandi = db.Column(db.Integer, nullable=False)
    posisi = db.Column(db.String(50), default='Standard')
    smart_lock = db.Column(db.Boolean, default=False)
    harga_kpr_resmi = db.Column(db.Float, nullable=False)
    status_unit = db.Column(db.String(20), default='tersedia') # 'tersedia', 'dipesan', 'terjual'
    gambar_unit = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blok = db.relationship('Blok', backref=db.backref('properti_units', lazy=True, cascade="all, delete-orphan"))

class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    properti_id = db.Column(db.Integer, db.ForeignKey('properti.id', ondelete='SET NULL'), nullable=True)
    nama_blok = db.Column(db.String(50))
    luas_bangunan = db.Column(db.Float)
    luas_tanah = db.Column(db.Float)
    kamar_tidur = db.Column(db.Integer)
    kamar_mandi = db.Column(db.Integer)
    posisi = db.Column(db.String(50))
    smart_lock = db.Column(db.Boolean)
    harga_prediksi = db.Column(db.Float)
    gaji = db.Column(db.Float)
    dsr_status = db.Column(db.String(50))
    usia = db.Column(db.Integer, nullable=True)
    jenis_pekerjaan = db.Column(db.String(100), nullable=True)
    tanggal_prediksi = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tambahan ERD
    cicilan_eksisting = db.Column(db.Float, default=0.0)
    dp_persen = db.Column(db.Float, default=10.0)
    tenor_pilihan = db.Column(db.Integer, default=20)
    dsr_rasio = db.Column(db.Float, nullable=True)
    status_follow_up = db.Column(db.String(20), default='baru') # 'baru', 'dihubungi', 'negosiasi', 'deal', 'cancel'
    catatan_marketing = db.Column(db.Text, nullable=True)

    customer = db.relationship('Customer', backref=db.backref('leads', lazy=True))
    properti = db.relationship('Properti', backref=db.backref('leads', lazy=True))

class SimulasiKPR(db.Model):
    __tablename__ = 'simulasi_kpr'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id', ondelete='CASCADE'), nullable=False)
    plafon_kredit = db.Column(db.Float, nullable=False)
    bunga_tahunan = db.Column(db.Float, default=0.08)
    cicilan_10_tahun = db.Column(db.Float, nullable=False)
    cicilan_15_tahun = db.Column(db.Float, nullable=False)
    cicilan_20_tahun = db.Column(db.Float, nullable=False)
    cicilan_tenor_pilihan = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lead = db.relationship('Lead', backref=db.backref('simulasi_kpr', uselist=False, cascade="all, delete-orphan"))

class TrainingHistory(db.Model):
    __tablename__ = 'training_history'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    dataset_name = db.Column(db.String(255), nullable=False)
    dataset_size = db.Column(db.Integer, nullable=False)
    optimizer_terbaik = db.Column(db.String(20), nullable=False)
    mae_adam = db.Column(db.Float, nullable=False)
    r2_adam = db.Column(db.Float, nullable=False)
    mae_sgd = db.Column(db.Float, nullable=False)
    r2_sgd = db.Column(db.Float, nullable=False)
    mae_lbfgs = db.Column(db.Float, nullable=False)
    r2_lbfgs = db.Column(db.Float, nullable=False)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Admin', backref=db.backref('training_histories', lazy=True))

class DatasetUpload(db.Model):
    __tablename__ = 'dataset_uploads'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('Admin', backref=db.backref('dataset_uploads', lazy=True))

class KontakPesan(db.Model):
    __tablename__ = 'kontak_pesan'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20), nullable=True)
    subjek = db.Column(db.String(255), nullable=False)
    pesan = db.Column(db.Text, nullable=False)
    status_baca = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Slider(db.Model):
    __tablename__ = 'sliders'
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    gambar = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    urutan = db.Column(db.Integer, default=1)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(50), nullable=False)
    judul = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    gambar = db.Column(db.String(255), nullable=True)
    urutan = db.Column(db.Integer, default=1)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

with app.app_context():
    try:
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(default_admin)
            db.session.commit()
    except Exception:
        pass # Warning koneksi disembunyikan

# -------------------------------------------------------------------
# AUTHENTICATION DECORATOR (MIDDLEWARE)
# -------------------------------------------------------------------
def admin_required(f):
    """Middleware untuk membatasi akses khusus admin di subdomain admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login admin terlebih dahulu.', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------
# KONFIGURASI
# -------------------------------------------------------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_PATH, 'models')
DATASET_PATH = os.path.join(BASE_PATH, 'Dataset_Sapphire_Final.csv')

# -------------------------------------------------------------------
# INISIALISASI GLOBAL
# -------------------------------------------------------------------
scaler = None
le_blok = None
le_posisi = None # Dihapus
models = {}
training_results = {}
resources_loaded = False


def load_resources():
    """Muat semua model, encoder, dan hasil training dari disk."""
    global scaler, le_blok, le_posisi, models, training_results, resources_loaded

    try:
        print(f"Memuat resources dari: {MODEL_PATH}")

        scaler = joblib.load(os.path.join(MODEL_PATH, 'scaler.pkl'))
        le_blok = joblib.load(os.path.join(MODEL_PATH, 'le_blok.pkl'))
        # le_posisi = joblib.load(os.path.join(MODEL_PATH, 'le_posisi.pkl'))

        models = {
            'adam': joblib.load(os.path.join(MODEL_PATH, 'model_adam.pkl')),
            'sgd': joblib.load(os.path.join(MODEL_PATH, 'model_sgd.pkl')),
            'lbfgs': joblib.load(os.path.join(MODEL_PATH, 'model_lbfgs.pkl'))
        }

        # Muat hasil training (metrik, statistik, deskriptif)
        json_path = os.path.join(MODEL_PATH, 'training_results.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                training_results = json.load(f)
            print("Hasil training berhasil dimuat dari JSON.")
        else:
            print("WARNING: training_results.json tidak ditemukan.")

        resources_loaded = True
        print("Semua resources berhasil dimuat.")
        return True

    except Exception as e:
        print(f"ERROR saat memuat resources: {e}")
        resources_loaded = False
        return False


load_resources()


# -------------------------------------------------------------------
# FUNGSI UTILITAS
# -------------------------------------------------------------------
def hitung_cicilan(plafon, bunga_tahunan, tenor_tahun):
    """Hitung cicilan bulanan menggunakan formula anuitas."""
    r = bunga_tahunan / 12
    n = tenor_tahun * 12
    if r == 0:
        return plafon / n
    return plafon * (r * (1 + r)**n) / ((1 + r)**n - 1)


def format_rupiah(angka):
    """Format angka ke format Rupiah Indonesia."""
    return f"{angka:,.0f}".replace(",", ".")


def analisis_dsr(gaji, cicilan_baru, cicilan_eksisting=0):
    """Analisis Debt Service Ratio (DSR) 30%."""
    if gaji <= 0:
        return {
            'rasio': 0,
            'status': 'DATA TIDAK LENGKAP',
            'kelas': 'warning',
            'saran': 'Masukkan data penghasilan untuk analisis kelayakan kredit.'
        }

    total_cicilan = cicilan_baru + cicilan_eksisting
    rasio = (total_cicilan / gaji) * 100

    if rasio <= 30:
        return {
            'rasio': round(rasio, 2),
            'status': 'LAYAK',
            'kelas': 'success',
            'saran': f'Rasio cicilan terhadap penghasilan Anda sebesar {rasio:.1f}%, masih di bawah ambang batas DSR 30%. Kredit dinilai layak secara finansial.'
        }
    elif rasio <= 40:
        return {
            'rasio': round(rasio, 2),
            'status': 'PERTIMBANGKAN KEMBALI',
            'kelas': 'warning',
            'saran': f'Rasio cicilan terhadap penghasilan Anda sebesar {rasio:.1f}%, melebihi ambang batas ideal DSR 30%. Pertimbangkan untuk memperkecil hutang lain, memilih tenor lebih panjang, atau menambah uang muka.'
        }
    else:
        return {
            'rasio': round(rasio, 2),
            'status': 'TIDAK LAYAK',
            'kelas': 'danger',
            'saran': f'Rasio cicilan terhadap penghasilan Anda sebesar {rasio:.1f}%, jauh melebihi batas aman DSR 30%. Disarankan untuk melunasi hutang eksisting, menambah uang muka, atau memilih unit yang lebih terjangkau.'
        }


# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------

@app.route('/')
def index():
    """Halaman utama - Form prediksi harga."""
    daftar_blok = sorted(le_blok.classes_.tolist()) if le_blok else []
    return render_template('index.html',
                           page='prediksi',
                           daftar_blok=daftar_blok)


@app.route('/predict', methods=['POST'])
def predict():
    """Proses prediksi harga dan analisis kelayakan kredit."""
    if not resources_loaded:
        return render_template('index.html',
                               page='prediksi',
                               error="Model belum dimuat. Jalankan train_model.py terlebih dahulu.")

    try:
        # 1. Ambil input dari form
        nama_blok = request.form['nama_blok']
        lb = float(request.form['luas_bangunan'])
        lt = float(request.form['luas_tanah'])
        kt = int(request.form['kamar_tidur'])
        km = int(request.form['kamar_mandi'])
        posisi = request.form.get('posisi', '-') # Dihapus dari input layer
        sdl = int(request.form['smart_lock'])
        
        gaji_raw = request.form.get('gaji', '')
        gaji = float(gaji_raw) if gaji_raw.strip() else 0.0

        # 2. Transform input
        blok_encoded = le_blok.transform([nama_blok])[0]
        # posisi_encoded = le_posisi.transform([posisi])[0]
        input_raw = np.array([[blok_encoded, lb, lt, kt, km, sdl]])
        input_scaled = scaler.transform(input_raw)

        # 3. Ambil input tambahan untuk simulasi
        dp_persen_raw = request.form.get('dp_persen', '')
        dp_persen = float(dp_persen_raw) if dp_persen_raw.strip() else 10.0
        
        tenor_raw = request.form.get('tenor_pilihan', '')
        tenor_pilihan = int(tenor_raw) if tenor_raw.strip() else 20
        
        cicilan_raw = request.form.get('cicilan_lain', '')
        cicilan_lain = float(cicilan_raw) if cicilan_raw.strip() else 0.0
        usia = int(request.form.get('usia', 0)) if request.form.get('usia') else None
        jenis_pekerjaan = request.form.get('jenis_pekerjaan', '')

        # 4. Prediksi dan KPR untuk semua optimizer
        hasil_prediksi_all = {}
        bunga = 0.08  # 8% per tahun

        for opt_name, model in models.items():
            pred_raw = model.predict(input_scaled)[0]
            pred_val = max(0, pred_raw * 1000000)
            
            dp = pred_val * (dp_persen / 100)
            plafon = pred_val - dp
            
            c10 = hitung_cicilan(plafon, bunga, 10)
            c15 = hitung_cicilan(plafon, bunga, 15)
            c20 = hitung_cicilan(plafon, bunga, 20)
            
            # Hitung cicilan berdasarkan tenor pilihan user
            c_pilihan = hitung_cicilan(plafon, bunga, tenor_pilihan)
            dsr = analisis_dsr(gaji, c_pilihan, cicilan_lain)

            hasil_prediksi_all[opt_name] = {
                'harga_raw': pred_val,
                'harga_format': format_rupiah(pred_val),
                'metrik': training_results.get('metrik_model', {}).get(opt_name.upper(), {}),
                'dp': format_rupiah(dp),
                'plafon': format_rupiah(plafon),
                'c10': format_rupiah(c10),
                'c15': format_rupiah(c15),
                'c20': format_rupiah(c20),
                'c_pilihan': format_rupiah(c_pilihan),
                'dsr': dsr
            }

        # 4. Ambil prediksi dari optimizer terbaik (misal LBFGS) sebagai acuan KPR
        opt_utama = 'lbfgs' if 'lbfgs' in models else list(models.keys())[0]
        best_pred_val = hasil_prediksi_all[opt_utama]['harga_raw']
        best_dsr_status = hasil_prediksi_all[opt_utama]['dsr']['status']

        # Simpan Lead ke Database MySQL
        try:
            new_lead = Lead(
                nama_blok=nama_blok,
                luas_bangunan=lb,
                luas_tanah=lt,
                kamar_tidur=kt,
                kamar_mandi=km,
                posisi='-', # Dihapus dari model
                smart_lock=bool(sdl),
                harga_prediksi=best_pred_val,
                gaji=gaji,
                dsr_status=best_dsr_status,
                usia=usia,
                jenis_pekerjaan=jenis_pekerjaan
            )
            db.session.add(new_lead)
            db.session.commit()
        except Exception as e:
            print(f"Gagal menyimpan ke database: {e}")

        # 5. Render hasil
        daftar_blok = sorted(le_blok.classes_.tolist())

        return render_template('index.html',
                               page='prediksi',
                               daftar_blok=daftar_blok,
                               hasil_prediksi_all=hasil_prediksi_all,
                               opt_utama=opt_utama.upper(),
                               dp_persen=dp_persen,
                               tenor_pilihan=tenor_pilihan,
                               bunga=bunga * 100,
                               input_user=request.form)

    except Exception as e:
        import traceback
        traceback.print_exc()
        daftar_blok = sorted(le_blok.classes_.tolist()) if le_blok else []
        return render_template('index.html',
                               page='prediksi',
                               daftar_blok=daftar_blok,
                               error=str(e))


# (Logout route moved to admin_bp)
# -------------------------------------------------------------------
from flask import Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def index():
    """Redirect root subdomain admin ke dashboard atau login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.data_leads'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            user = Admin.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session['admin_logged_in'] = True
                session['username'] = user.username
                
                flash(f'Login Admin berhasil! Selamat datang {user.username}.', 'success')
                return redirect(url_for('admin.data_leads'))
            else:
                flash('Username atau password salah.', 'danger')
        except Exception as e:
            flash(f'Gagal koneksi ke database: {e}', 'danger')
            
    return render_template('admin_login.html', page='admin_login')

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout dari dashboard admin.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/latih_model', methods=['GET', 'POST'])
@admin_required
def latih_model():
    if request.method == 'POST':
        if 'dataset' not in request.files:
            flash('Tidak ada file yang diunggah', 'danger')
            return redirect(request.url)
            
        file = request.files['dataset']
        if file.filename == '':
            flash('File tidak dipilih', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith('.csv'):
            filename = 'Dataset_Sapphire_Final.csv'
            file_path = os.path.join(BASE_PATH, filename)
            file.save(file_path)
            
            try:
                # Menjalankan train_model.py
                result = subprocess.run(['python', 'train_model.py'], cwd=BASE_PATH, capture_output=True, text=True)
                if result.returncode == 0:
                    flash('Model berhasil dilatih ulang dengan data baru!', 'success')
                    # Muat ulang resources ke dalam memori aplikasi
                    load_resources()
                else:
                    flash(f'Gagal melatih model. Error Output: {result.stderr}', 'danger')
            except Exception as e:
                flash(f'Terjadi kesalahan saat menjalankan training: {str(e)}', 'danger')
                
            return redirect(url_for('admin.latih_model'))
        else:
            flash('Harap unggah file berformat .csv', 'danger')
            
    return render_template('admin_latih_model.html', page='admin_latih_model')

@admin_bp.route('/data_leads', methods=['GET'])
@admin_required
def data_leads():
    leads = []
    try:
        leads = Lead.query.order_by(Lead.tanggal_prediksi.desc()).limit(50).all()
    except Exception as e:
        print(f"Error fetching leads: {e}")
        flash('Tidak dapat terhubung ke database untuk memuat leads.', 'danger')
        
    return render_template('admin_data_leads.html', page='admin_data_leads', leads=leads)


@app.route('/perbandingan')
def perbandingan():
    """Halaman perbandingan performa optimizer."""
    metrik = training_results.get('metrik_model', {})
    arsitektur = training_results.get('arsitektur', {})
    best = training_results.get('optimizer_terbaik', 'LBFGS')
    split = training_results.get('split_data', {})
    return render_template('dashboard.html',
                           page='dashboard',
                           metrik=metrik,
                           arsitektur=arsitektur,
                           optimizer_terbaik=best,
                           split_data=split)


@app.route('/analisis')
def analisis():
    """Halaman analisis deskriptif dan uji statistik."""
    deskriptif = training_results.get('deskriptif', {})
    statistik = training_results.get('statistik', {})
    arsitektur = training_results.get('arsitektur', {})
    fitur = training_results.get('fitur', [])
    return render_template('analisis.html',
                           page='analisis',
                           deskriptif=deskriptif,
                           statistik=statistik,
                           arsitektur=arsitektur,
                           fitur=fitur)



@app.route('/api/metrics')
def api_metrics():
    """API endpoint untuk data metrik (JSON)."""
    return jsonify(training_results)


@app.route('/tentang')
def tentang():
    """Halaman Tentang Sapphire."""
    return render_template('tentang.html', page='tentang')


@app.route('/estimasi')
def estimasi():
    """Halaman Landing Estimasi Nilai Properti."""
    return render_template('estimasi.html', page='estimasi')


@app.route('/properti-baru')
def properti_baru():
    """Halaman Informasi Properti Baru."""
    return render_template('properti_baru.html', page='properti_baru')




# -------------------------------------------------------------------
# UTILITAS EXCEL
# -------------------------------------------------------------------
def style_excel(ws, title, headers, data_rows, start_row=1):
    """Styling Excel worksheet secara konsisten."""
    hdr_font = Font(name='Calibri', bold=True, size=11, color='FFFFFF')
    hdr_fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    hdr_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell_font = Font(name='Calibri', size=10)
    cell_align = Alignment(vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Title
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=len(headers))
    title_cell = ws.cell(row=start_row, column=1, value=title)
    title_cell.font = Font(name='Calibri', bold=True, size=13, color='1E3A5F')
    title_cell.alignment = Alignment(horizontal='left')

    # Headers
    hr = start_row + 1
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=hr, column=ci, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = hdr_align
        c.border = thin_border

    # Data
    for ri, row_data in enumerate(data_rows, hr + 1):
        for ci, val in enumerate(row_data, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            c.font = cell_font
            c.alignment = cell_align
            c.border = thin_border
            if ri % 2 == 0:
                c.fill = PatternFill(start_color='F5F6F8', end_color='F5F6F8', fill_type='solid')

    # Auto-width
    for ci in range(1, len(headers) + 1):
        max_len = len(str(headers[ci - 1]))
        for ri in range(hr + 1, hr + 1 + len(data_rows)):
            val = ws.cell(row=ri, column=ci).value
            if val:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(ci)].width = min(max_len + 4, 35)

    return hr + 1 + len(data_rows)


# -------------------------------------------------------------------
# EXPORT ROUTES
# -------------------------------------------------------------------
@app.route('/export/prediksi', methods=['POST'])
def export_prediksi():
    """Export hasil prediksi ke Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = 'Hasil Prediksi'

        # Data dari form
        blok = request.form.get('blok', '-')
        lb = request.form.get('lb', '-')
        lt = request.form.get('lt', '-')
        kt = request.form.get('kt', '-')
        km = request.form.get('km', '-')
        posisi = request.form.get('posisi', '-')
        sdl = request.form.get('sdl', '-')
        optimizer = request.form.get('optimizer', '-')
        harga = request.form.get('harga', '-')
        dp = request.form.get('dp', '-')
        plafon = request.form.get('plafon', '-')
        cicilan_10 = request.form.get('cicilan_10', '-')
        cicilan_15 = request.form.get('cicilan_15', '-')
        cicilan_20 = request.form.get('cicilan_20', '-')
        gaji = request.form.get('gaji', '-')
        cicilan_lain = request.form.get('cicilan_lain', '0')
        tenor_pilihan = request.form.get('tenor_pilihan', '20')
        dp_persen = request.form.get('dp_persen', '10')
        dsr_status = request.form.get('dsr_status', '-')
        dsr_rasio = request.form.get('dsr_rasio', '-')
        usia = request.form.get('usia', '-')
        jenis_pekerjaan = request.form.get('jenis_pekerjaan', '-')

        # Spesifikasi unit
        next_row = style_excel(ws, 'SPESIFIKASI UNIT',
            ['Parameter', 'Nilai'],
            [
                ['Blok Kavling', blok],
                ['Luas Bangunan (m2)', lb],
                ['Luas Tanah (m2)', lt],
                ['Kamar Tidur', kt],
                ['Kamar Mandi', km],
                ['Posisi Kavling', posisi],
                ['Smart Door Lock', 'Ya' if sdl == '1' else 'Tidak'],
                ['Optimizer', optimizer],
            ])

        # Hasil prediksi
        next_row = style_excel(ws, 'HASIL PREDIKSI HARGA',
            ['Keterangan', 'Nilai'],
            [
                ['Estimasi Harga KPR', f'Rp {harga}'],
                [f'Uang Muka (DP {dp_persen}%)', f'Rp {dp}'],
                ['Plafon Kredit', f'Rp {plafon}'],
                ['Bunga', '8.0% / tahun'],
            ], start_row=next_row + 1)

        # Simulasi KPR
        next_row = style_excel(ws, 'SIMULASI KREDIT',
            ['Tenor', 'Cicilan per Bulan'],
            [
                ['10 Tahun', f'Rp {cicilan_10}'],
                ['15 Tahun', f'Rp {cicilan_15}'],
                ['20 Tahun', f'Rp {cicilan_20}'],
            ], start_row=next_row + 1)

        # Kelayakan
        next_row = style_excel(ws, 'ANALISIS KELAYAKAN KREDIT (DSR)',
            ['Parameter', 'Nilai'],
            [
                ['Usia Pemohon', f'{usia} Tahun'],
                ['Jenis Pekerjaan', jenis_pekerjaan],
                ['Penghasilan Bulanan', f'Rp {gaji}'],
                ['Cicilan Eksisting (Lainnya)', f'Rp {cicilan_lain}'],
                [f'DSR (Tenor {tenor_pilihan} Tahun)', f'{dsr_rasio}%'],
                ['Status Kelayakan', dsr_status],
                ['Ambang Batas DSR', '30%'],
            ], start_row=next_row + 1)

        # Timestamp
        r = next_row + 2
        ws.cell(row=r, column=1, value=f'Dicetak pada: {datetime.now().strftime("%d %B %Y, %H:%M WIB")}')
        ws.cell(row=r, column=1).font = Font(name='Calibri', size=9, italic=True, color='888888')

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        fname = f'Prediksi_Sapphire_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        return send_file(output, as_attachment=True, download_name=fname,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/dashboard')
def export_dashboard():
    """Export perbandingan optimizer ke Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = 'Perbandingan Optimizer'
        metrik = training_results.get('metrik_model', {})
        arsitektur = training_results.get('arsitektur', {})

        # Arsitektur info
        next_row = style_excel(ws, 'ARSITEKTUR MODEL ANN',
            ['Parameter', 'Nilai'],
            [
                ['Hidden Layers', '-'.join(str(x) for x in arsitektur.get('hidden_layers', []))],
                ['Fitur Input', str(arsitektur.get('input_layer', 7))],
                ['Fungsi Aktivasi', arsitektur.get('aktivasi', 'ReLU')],
                ['Max Iterasi', str(arsitektur.get('max_iter', 10000))],
                ['Data Training', str(training_results.get('split_data', {}).get('training', '-'))],
                ['Data Testing', str(training_results.get('split_data', {}).get('testing', '-'))],
                ['Rasio Split', training_results.get('split_data', {}).get('ratio', '80:20')],
            ])

        # Tabel metrik
        rows = []
        for opt_name, m in metrik.items():
            rows.append([
                opt_name,
                f"Rp {m.get('mae', 0):,.0f}".replace(',', '.'),
                round(m.get('r2', 0), 6),
            ])

        next_row = style_excel(ws, 'PERBANDINGAN METRIK EVALUASI',
            ['Optimizer', 'MAE', 'R2 Score'],
            rows, start_row=next_row + 1)

        # Kesimpulan
        best = training_results.get('optimizer_terbaik', '-')
        r = next_row + 1
        ws.cell(row=r, column=1, value=f'Optimizer Terbaik: {best}')
        ws.cell(row=r, column=1).font = Font(name='Calibri', bold=True, size=11, color='0D7C66')

        r += 2
        ws.cell(row=r, column=1, value=f'Dicetak pada: {datetime.now().strftime("%d %B %Y, %H:%M WIB")}')
        ws.cell(row=r, column=1).font = Font(name='Calibri', size=9, italic=True, color='888888')

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        fname = f'Dashboard_Sapphire_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        return send_file(output, as_attachment=True, download_name=fname,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/analisis')
def export_analisis():
    """Export analisis statistik ke Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = 'Analisis Statistik'
        deskriptif = training_results.get('deskriptif', {})
        statistik = training_results.get('statistik', {})

        # Statistik deskriptif
        desc_rows = []
        for nama, stats in deskriptif.get('statistik', {}).items():
            desc_rows.append([
                nama,
                f"{stats['mean']:,.2f}".replace(',', '.'),
                f"{stats['std']:,.2f}".replace(',', '.'),
                f"{stats['min']:,.0f}".replace(',', '.'),
                f"{stats['median']:,.0f}".replace(',', '.'),
                f"{stats['max']:,.0f}".replace(',', '.'),
            ])

        next_row = style_excel(ws, 'STATISTIK DESKRIPTIF',
            ['Variabel', 'Mean', 'Std. Dev', 'Min', 'Median', 'Max'],
            desc_rows)



        # Distribusi
        dist_rows = []
        for tipe, info in deskriptif.get('distribusi_tipe', {}).items():
            dist_rows.append([tipe, info['count'], f"{info['persen']}%"])

        next_row = style_excel(ws, 'DISTRIBUSI TIPE RUMAH',
            ['Tipe', 'Jumlah Unit', 'Persentase'],
            dist_rows, start_row=next_row + 1)

        r = next_row + 1
        ws.cell(row=r, column=1, value=f'Dicetak pada: {datetime.now().strftime("%d %B %Y, %H:%M WIB")}')
        ws.cell(row=r, column=1).font = Font(name='Calibri', size=9, italic=True, color='888888')

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        fname = f'Analisis_Sapphire_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        return send_file(output, as_attachment=True, download_name=fname,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/export/leads_excel')
@admin_required
def export_leads_excel():
    """Export data leads ke Excel."""
    try:
        leads = Lead.query.order_by(Lead.tanggal_prediksi.desc()).all()
        wb = Workbook()
        ws = wb.active
        ws.title = 'Data Leads'

        headers = ['Tanggal Prediksi', 'Blok', 'L. Bangunan (m2)', 'L. Tanah (m2)', 'K. Tidur', 'K. Mandi', 'Posisi', 'Smart Lock', 'Usia', 'Jenis Pekerjaan', 'Gaji (Rp)', 'Status DSR', 'Prediksi Harga (Rp)']
        data_rows = []
        for lead in leads:
            data_rows.append([
                lead.tanggal_prediksi.strftime('%Y-%m-%d %H:%M') if lead.tanggal_prediksi else '-',
                lead.nama_blok,
                lead.luas_bangunan,
                lead.luas_tanah,
                lead.kamar_tidur,
                lead.kamar_mandi,
                lead.posisi,
                'Ya' if lead.smart_lock else 'Tidak',
                lead.usia if lead.usia else '-',
                lead.jenis_pekerjaan if lead.jenis_pekerjaan else '-',
                f"{lead.gaji:,.0f}".replace(',', '.') if lead.gaji else '-',
                lead.dsr_status,
                f"{lead.harga_prediksi:,.0f}".replace(',', '.') if lead.harga_prediksi else '-'
            ])

        next_row = style_excel(ws, 'DATA LEADS (HISTORI PREDIKSI)', headers, data_rows)

        r = next_row + 1
        ws.cell(row=r, column=1, value=f'Dicetak pada: {datetime.now().strftime("%d %B %Y, %H:%M WIB")}')
        ws.cell(row=r, column=1).font = Font(name='Calibri', size=9, italic=True, color='888888')

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        fname = f'Data_Leads_Sapphire_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        return send_file(output, as_attachment=True, download_name=fname,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register Blueprint
app.register_blueprint(admin_bp)

# -------------------------------------------------------------------
# SUBDOMAIN DISPATCHER MIDDLEWARE
# -------------------------------------------------------------------
class SubdomainDispatcher:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', '')
        path = environ.get('PATH_INFO', '')
        # Jika diakses dari subdomain admin. dan belum memiliki awalan /admin
        if host.startswith('admin.') and not path.startswith('/admin'):
            environ['PATH_INFO'] = '/admin' + path
        return self.app(environ, start_response)

app.wsgi_app = SubdomainDispatcher(app.wsgi_app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=5000)