import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QTableWidget, QTableWidgetItem, QAbstractItemView,
                            QMessageBox, QFrame, QGridLayout, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class DemirbasTakipSistemi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demirbas Takip Sistemi (PyQt6)")
        self.setGeometry(100, 100, 1000, 600)

        self.baglanti_olustur()
        self.merkezi_widget = QWidget()
        self.setCentralWidget(self.merkezi_widget)
        self.ana_layout = QVBoxLayout(self.merkezi_widget)

        self.arayuz_olustur()
        self.tablo_yukle()

    def baglanti_olustur(self):
        try:
            self.conn = sqlite3.connect('demirbas_takip.db')
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS demirbaslar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bilgisayar_adi TEXT,
                bilgisayar_marka TEXT,
                islemci TEXT,
                ram TEXT,
                depolama TEXT,
                sarf_malzeme TEXT,
                seri_no TEXT,
                demirbas_no TEXT,
                kullanici_adi TEXT,
                zimmet_tarihi TEXT,
                eklenme_tarihi TEXT
            )
            ''')
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Veritabani Hatasi",
                                f"Veritabanina baglanirken veya tablo olusturulurken bir hata olustu:\n{e}\nUygulama kapatilacak.")
            sys.exit(1)

    def arayuz_olustur(self):
        form_cerceve = QFrame()
        form_layout = QGridLayout(form_cerceve)
        form_cerceve.setFrameShape(QFrame.Shape.Panel)
        form_cerceve.setFrameShadow(QFrame.Shadow.Raised)

        labels = ["Bilgisayar Adi:", "Bilgisayar Markasi:", "Islemci:", "RAM:", "Depolama:", "Sarf Malzeme:", "Seri No:",
                  "Demirbas No:", "Kullanici Adi Soyadi:", "Zimmet Tarihi:"]
        self.entries = {}

        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            form_layout.addWidget(label, i, 0)
            if label_text == "Zimmet Tarihi:":
                entry = QDateEdit()
                entry.setDate(QDate.currentDate())
                form_layout.addWidget(entry, i, 1)
            else:
                entry = QLineEdit()
                form_layout.addWidget(entry, i, 1)
            field_name = label_text.replace(":", "").lower().replace(" ", "_")
            self.entries[field_name] = entry

        button_layout = QHBoxLayout()
        self.kaydet_btn = QPushButton("Kaydet")
        self.guncelle_btn = QPushButton("Guncelle")
        self.sil_btn = QPushButton("Sil")
        self.temizle_btn = QPushButton("Temizle")
        self.zimmet_cikar_btn = QPushButton("Zimmet Cikar")

        self.kaydet_btn.clicked.connect(self.kaydet)
        self.guncelle_btn.clicked.connect(self.guncelle)
        self.sil_btn.clicked.connect(self.sil)
        self.temizle_btn.clicked.connect(self.temizle)
        self.zimmet_cikar_btn.clicked.connect(self.zimmet_cikar)

        button_layout.addWidget(self.kaydet_btn)
        button_layout.addWidget(self.guncelle_btn)
        button_layout.addWidget(self.sil_btn)
        button_layout.addWidget(self.temizle_btn)
        button_layout.addWidget(self.zimmet_cikar_btn)
        form_layout.addLayout(button_layout, len(labels), 0, 1, 2)

        self.ana_layout.addWidget(form_cerceve)

        arama_cerceve = QFrame()
        arama_layout = QHBoxLayout(arama_cerceve)
        arama_cerceve.setFrameShape(QFrame.Shape.Panel)
        arama_cerceve.setFrameShadow(QFrame.Shadow.Raised)

        arama_label = QLabel("Ara:")
        self.arama_entry = QLineEdit()
        self.ara_btn = QPushButton("Ara")
        self.tumunu_goster_btn = QPushButton("Tumunu Goster")

        self.ara_btn.clicked.connect(self.ara)
        self.tumunu_goster_btn.clicked.connect(self.tablo_yukle)

        arama_layout.addWidget(arama_label)
        arama_layout.addWidget(self.arama_entry)
        arama_layout.addWidget(self.ara_btn)
        arama_layout.addWidget(self.tumunu_goster_btn)

        self.ana_layout.addWidget(arama_cerceve)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(12)
        self.tablo.setHorizontalHeaderLabels(
            ["ID", "Bilgisayar Adi", "Marka", "Islemci", "RAM", "Depolama", "Sarf Malzeme", "Seri No", "Demirbas No", "Kullanici", "Zimmet Tarihi",
             "Eklenme Tarihi"])
        self.tablo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablo.doubleClicked.connect(self.tablo_satir_sec)
        self.ana_layout.addWidget(self.tablo)

    def tablo_yukle(self, filtre=None):
        self.tablo.setRowCount(0)
        try:
            query = "SELECT * FROM demirbaslar ORDER BY id DESC"
            params = []
            if filtre:
                query = "SELECT * FROM demirbaslar WHERE bilgisayar_adi LIKE ? OR bilgisayar_marka LIKE ? OR islemci LIKE ? OR ram LIKE ? OR depolama LIKE ? OR sarf_malzeme LIKE ? OR seri_no LIKE ? OR demirbas_no LIKE ? OR kullanici_adi LIKE ? OR zimmet_tarihi LIKE ? ORDER BY id DESC"
                params = [f"%{filtre}%"] * 10
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            for row_num, row_data in enumerate(rows):
                self.tablo.insertRow(row_num)
                for col_num, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    self.tablo.setItem(row_num, col_num, item)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tablo yuklenirken bir hata olustu:\n{e}")

    def tablo_satir_sec(self, index):
        try:
            row = index.row()
            item_id = self.tablo.item(row, 0).text()
            self.cursor.execute("SELECT * FROM demirbaslar WHERE id=?", (item_id,))
            kayit = self.cursor.fetchone()
            if kayit:
                self.temizle()
                self.entries['bilgisayar_adi'].setText(kayit[1])
                self.entries['bilgisayar_markasi'].setText(kayit[2])
                self.entries['islemci'].setText(kayit[3])
                self.entries['ram'].setText(kayit[4])
                self.entries['depolama'].setText(kayit[5])
                self.entries['sarf_malzeme'].setText(kayit[6])
                self.entries['seri_no'].setText(kayit[7])
                self.entries['demirbas_no'].setText(kayit[8])
                self.entries['kullanici_adi_soyadi'].setText(kayit[9])
                zimmet_tarihi_str = kayit[10]
                try:
                    zimmet_tarihi = datetime.strptime(zimmet_tarihi_str, "%Y-%m-%d")
                except ValueError:
                    zimmet_tarihi = datetime.now()
                self.entries['zimmet_tarihi'].setDate(QDate(zimmet_tarihi.year, zimmet_tarihi.month, zimmet_tarihi.day))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Satir secilirken bir hata olustu:\n{e}")

    def kaydet(self):
        data = {}
        for field, entry in self.entries.items():
            if isinstance(entry, QDateEdit):
                data[field] = entry.date().toString("yyyy-MM-dd")
            else:
                data[field] = entry.text().strip()

        print("Kaydedilecek Veri:", data)
        print("Girisler:", self.entries)

        if not data.get('bilgisayar_adi') or not data.get('demirbas_no'):
            QMessageBox.critical(self, "Hata", "Bilgisayar Adi ve Demirbas No zorunlu alanlardir!")
            return
        
        if not data.get('bilgisayar_markasi'):
            QMessageBox.critical(self, "Hata", "Bilgisayar Markasi zorunlu alandir!")
            return

        if not data.get('islemci'):
            QMessageBox.critical(self, "Hata", "Islemci zorunlu alandir!")
            return
        
        if not data.get('ram'):
            QMessageBox.critical(self, "Hata", "RAM zorunlu alandir!")
            return
        
        if not data.get('depolama'):
            QMessageBox.critical(self, "Hata", "Depolama zorunlu alandir!")
            return

        try:
            self.cursor.execute('''
            INSERT INTO demirbaslar (
                bilgisayar_adi, bilgisayar_marka, islemci, ram, depolama, sarf_malzeme, seri_no,
                demirbas_no, kullanici_adi, zimmet_tarihi, eklenme_tarihi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['bilgisayar_adi'],
                data['bilgisayar_markasi'],
                data['islemci'],
                data['ram'],
                data['depolama'],
                data['sarf_malzeme'],
                data['seri_no'],
                data['demirbas_no'],
                data['kullanici_adi_soyadi'],
                data['zimmet_tarihi'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.conn.commit()
            QMessageBox.information(self, "Basarili", "Demirbas basariyla kaydedildi!")
            self.tablo_yukle()
            self.temizle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit sirasinda hata olustu: {str(e)}")

    def guncelle(self):
        selected_row = self.tablo.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Uyari", "Lutfen guncellemek icin bir satir secin!")
            return

        item_id = self.tablo.item(selected_row, 0).text()
        data = {}
        for field, entry in self.entries.items():
            if isinstance(entry, QDateEdit):
                data[field] = entry.date().toString("yyyy-MM-dd")
            else:
                data[field] = entry.text().strip()

        if not data['bilgisayar_adi'] or not data['demirbas_no']:
            QMessageBox.critical(self, "Hata", "Bilgisayar Adi ve Demirbas No zorunlu alanlardir!")
            return

        try:
            self.cursor.execute('''
            UPDATE demirbaslar SET
                bilgisayar_adi = ?,
                bilgisayar_marka = ?,
                islemci = ?,
                ram = ?,
                depolama = ?,
                sarf_malzeme = ?,
                seri_no = ?,
                demirbas_no = ?,
                kullanici_adi = ?,
                zimmet_tarihi = ?
            WHERE id = ?
            ''', (
                data['bilgisayar_adi'],
                data['bilgisayar_markasi'],
                data['islemci'],
                data['ram'],
                data['depolama'],
                data['sarf_malzeme'],
                data['seri_no'],
                data['demirbas_no'],
                data['kullanici_adi_soyadi'],
                data['zimmet_tarihi'],
                item_id
            ))
            self.conn.commit()
            QMessageBox.information(self, "Basarili", "Demirbas basariyla guncellendi!")
            self.tablo_yukle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Guncelleme sirasinda hata olustu: {str(e)}")

    def sil(self):
        selected_row = self.tablo.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Uyari", "Lutfen silmek icin bir satir secin!")
            return

        item_id = self.tablo.item(selected_row, 0).text()
        emin_mi = QMessageBox.question(self, "Onay", "Secili demirbasi silmek istediginize emin misiniz?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if emin_mi == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute("DELETE FROM demirbaslar WHERE id = ?", (item_id,))
                self.conn.commit()
                QMessageBox.information(self, "Basarili", "Demirbas basariyla silindi!")
                self.tablo_yukle()
                self.temizle()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme sirasinda hata olustu: {str(e)}")

    def temizle(self):
        for entry in self.entries.values():
            if isinstance(entry, QLineEdit):
                entry.clear()
            elif isinstance(entry, QDateEdit):
                entry.setDate(QDate.currentDate())

    def ara(self):
        filtre = self.arama_entry.text().strip()
        self.tablo_yukle(filtre)

    def zimmet_cikar(self):
        selected_row = self.tablo.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Uyari", "Lutfen zimmet cikarmak icin bir satir secin!")
            return

        item_data = [self.tablo.item(selected_row, i).text() for i in range(self.tablo.columnCount())]
        print(f"Item data: {item_data}")

        dosya_adi = f"Zimmet_{item_data[8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
        c = canvas.Canvas(dosya_adi, pagesize=letter)
        pdfmetrics.registerFont(TTFont('ArialUnicode', 'ArialUnicodeMS.ttf'))
        c.setFont("ArialUnicode", 12)

        c.setFont("ArialUnicode", 16)
        c.drawString(100, 750, "DEMİBAS ZİMMET FORMU")
        c.setFont("ArialUnicode", 12)
        c.drawString(100, 730, f"Zimmet Tarihi: {item_data[10]}")
        c.drawString(100, 710, "Demirbas Bilgileri:")

        y = 690
        bilgiler = [
            ("Demirbas No:", item_data[8]),
            ("Bilgisayar Adi:", item_data[1]),
            ("Marka:", item_data[2]),
            ("Islemci:", item_data[3]),
            ("RAM:", item_data[4]),
            ("Depolama:", item_data[5]),
            ("Sarf Malzeme:", item_data[6]),
            ("Seri No:", item_data[7])
        ]
        for label, value in bilgiler:
            c.drawString(120, y, label)
            c.drawString(250, y, value)
            y -= 20

        c.drawString(100, y - 20, "Kullanici Bilgileri:")
        c.drawString(120, y - 40, "Adi Soyadi:")
        c.drawString(250, y - 40, item_data[9])

        c.drawString(100, y - 80, "Teslim Alan:")
        c.drawString(400, y - 80, "Teslim Eden:")
        c.drawString(100, y - 120, "...............................")
        c.drawString(400, y - 120, "...............................")
        c.drawString(100, y - 140, "Imza")
        c.drawString(400, y - 140, "Imza")

        c.save()
        QMessageBox.information(self, "Başarılı", f"Zimmet formu başarıyla oluşturuldu:\n{os.path.abspath(dosya_adi)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pencere = DemirbasTakipSistemi()
    pencere.show()
    sys.exit(app.exec())
