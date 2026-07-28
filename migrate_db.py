from app import app, db

with app.app_context():
    try:
        db.session.execute(db.text('ALTER TABLE lead ADD COLUMN usia INTEGER'))
        db.session.commit()
        print("Kolom usia berhasil ditambahkan.")
    except Exception as e:
        print(f"Error (mungkin kolom usia sudah ada): {e}")
        db.session.rollback()

    try:
        db.session.execute(db.text('ALTER TABLE lead ADD COLUMN jenis_pekerjaan VARCHAR(100)'))
        db.session.commit()
        print("Kolom jenis_pekerjaan berhasil ditambahkan.")
    except Exception as e:
        print(f"Error (mungkin kolom jenis_pekerjaan sudah ada): {e}")
        db.session.rollback()
