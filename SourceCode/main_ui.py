from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtWidgets
import sqlite3
from hijri_converter import convert
from datetime import datetime, timedelta, date
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from bidi.algorithm import get_display
import arabic_reshaper
import sqlite3
from typing import List
import aspose.pdf as ap
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
import sys
from PyQt5.QtWidgets import QApplication


class HolidayHistoryDialog(QDialog):
    def __init__(self, db_path, militarycode, name):
        super().__init__()
        self.db_path = db_path
        self.militarycode = militarycode
        self.name = name  # Use self.militarycode to store it as an instance attribute
        self.setWindowTitle("Holiday History")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        # Date input layout
        date_layout = QHBoxLayout()

        self.start_date_label = QLabel("من التاريخ:")
        self.start_date_edit = QLineEdit()
        today_gregorian = datetime.today()

        # Convert to Hijri date
        today_hijri = convert.Gregorian(
            today_gregorian.year, today_gregorian.month, today_gregorian.day
        ).to_hijri()

        self.start_date_edit.setText(str(today_hijri))

        self.end_date_label = QLabel("الي التاريخ:")
        self.end_date_edit = QLineEdit()
        self.end_date_edit.setText(str(today_hijri))

        date_layout.addWidget(self.end_date_edit)
        date_layout.addWidget(self.end_date_label)
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(self.start_date_label)
        self.layout.addLayout(date_layout)

        # Print button
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.handle_print_button)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

    def handle_print_button(self):
        start_date_hijri = self.start_date_edit.text()
        end_date_hijri = self.end_date_edit.text()
        self.print(start_date_hijri, end_date_hijri, self.militarycode)

    def print(
        self, start_date_hijri: str, end_date_hijri: str, military_code: int = None
    ):
        table = self.get_holiday_data(start_date_hijri, end_date_hijri, military_code)
        self.create_pdf(
            "Printing/holidays_history.pdf",
            table,
            self.name,
            self.get_civil_registry_by_military_number(military_code),
        )
        self.print_pdf("Printing/holidays_history.pdf")

    def get_civil_registry_by_military_number(self, military_number):
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()
        query = "SELECT civil_registry FROM users WHERE military_number = ?"
        cursor.execute(query, (military_number,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return "Name not found"

    def get_holiday_data(
        self, start_date_hijri: str, end_date_hijri: str, military_code: int = None
    ) -> List[List]:
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL query to get data between start_date and end_date, and optionally filter by military_code
        query = """
        SELECT military_number, the_kind_of_holiday, duration_of_vacation, start_Date, return_date, duration_of_absence, user_code, check_in_date
        FROM holidays_history
        WHERE start_Date BETWEEN ? AND ?
        """

        # Add filter for military_code if provided
        if military_code is not None:
            query += " AND military_number = ?"
            params = (start_date_hijri, end_date_hijri, military_code)
        else:
            params = (start_date_hijri, end_date_hijri)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Format data
        formatted_data = []
        for row in rows:
            formatted_row = [
                row[0],  # military_number
                row[1],  # the_kind_of_holiday
                row[2],  # duration_of_vacation
                row[3],  # start_Date (Hijri)
                row[4],  # return_date (Hijri)
                row[5],  # duration_of_absence
                row[6],  # user_code
                row[7],  # check_in_date
            ]
            formatted_data.append(formatted_row)

        return formatted_data
    def show_printer_check_dialog(self):
        # Create a QMessageBox
        msg_box = QMessageBox()

        # Set the icon, title, and message
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("تحذير")
        msg_box.setText("الرجاء التحقق من الطابعه   ")

        # Add OK button
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Execute the dialog and wait for the user to close it
        msg_box.exec_()
    def printer_check_done(self):
        # Create a QMessageBox
        msg_box = QMessageBox()

        # Set the icon, title, and message
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("تحذير")
        msg_box.setText("تم ارسال الملف الي الطابعه")

        # Add OK button
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Execute the dialog and wait for the user to close it
        msg_box.exec_()


    def print_pdf(self, file_path):
        try:
            viewer = ap.facades.PdfViewer()
            # Open input PDF file
            viewer.bind_pdf(file_path)

            # Print a PDF document
            viewer.print_document()

            # Close PDF file
            viewer.close()
            self.printer_check_done()
        except Exception as e:
            self.show_printer_check_dialog()
            



    def create_pdf(self, output_filename, table_data, user_name, user_code):
        c = canvas.Canvas(output_filename, pagesize=A4)
        width, height = A4

        # Register the custom Arabic font
        pdfmetrics.registerFont(TTFont("Arabic", "Printing/Amiri-Regular.ttf"))

        # Load the image
        image_path = "Printing/logo.png"  # Replace with the path to your image
        image = ImageReader(image_path)
        image_width, image_height = image.getSize()
        aspect_ratio = image_height / float(image_width)
        image_display_width = width / 8  # Adjust as needed
        image_display_height = image_display_width * aspect_ratio
        image_x = (width - image_display_width) / 2
        image_y = height - image_display_height - 30

        # Draw the image
        c.drawImage(
            image_path,
            image_x,
            image_y,
            width=image_display_width,
            height=image_display_height,
        )

        # Arabic text
        arabic_text1 = "المملكة العربية السعودية"
        reshaped_text1 = arabic_reshaper.reshape(arabic_text1)
        bidi_text1 = get_display(reshaped_text1)

        arabic_text2 = "رئاسة أمن الدولة"
        reshaped_text2 = arabic_reshaper.reshape(arabic_text2)
        bidi_text2 = get_display(reshaped_text2)

        arabic_text3 = "قوات الطوارئ الخاصة"
        reshaped_text3 = arabic_reshaper.reshape(arabic_text3)
        bidi_text3 = get_display(reshaped_text3)

        # Add text to PDF
        text_y = 800
        c.setFont("Arabic", 10)
        c.drawRightString(width - 20, text_y, bidi_text1)
        c.drawRightString(width - 20, text_y - 20, bidi_text2)
        c.drawRightString(width - 20, text_y - 40, bidi_text3)

        # Additional text on the other side of the page
        arabic_text4 = f" رقم الهوية : {user_code}"
        reshaped_text4 = arabic_reshaper.reshape(arabic_text4)
        bidi_text4 = get_display(reshaped_text4)

        arabic_text5 = f"الاسم : {user_name}"
        reshaped_text5 = arabic_reshaper.reshape(arabic_text5)
        bidi_text5 = get_display(reshaped_text5)

        c.drawRightString(120, text_y, bidi_text4)
        c.drawRightString(150, text_y - 20, bidi_text5)

        # Table headers
        headers = [
            "اسم المستخدم",
            "مدة التطويف",
            "تاريخ العودة",
            "تاريخ النهاية",
            "تاريخ البدابة",
            "مدة الاجازة",
            "نوع الاجازة",
            "الرقم العسكري",
        ]

        # Reorder the data to match headers
        sorted_data = [headers]
        print(table_data)  # Start with headers
        for row in table_data:
            sorted_row = [
                row[6],  # الرقم العسكري
                row[5],  # نوع الاجازة
                row[7],  # مدة الاجازة
                row[4],  # تاريخ البدابة
                row[3],  # تاريخ النهاية
                row[2],  # تاريخ العودة#
                row[1],  # مدة التطويف"
                row[0],  # اسم المستخدم"
            ]
            sorted_data.append(sorted_row)
        # Reshape Arabic text in the table
        reshaped_data = []
        for row in sorted_data:
            reshaped_row = []
            for item in row:
                if isinstance(item, str):
                    reshaped_item = arabic_reshaper.reshape(item)
                    bidi_item = get_display(reshaped_item)
                    reshaped_row.append(bidi_item)
                else:
                    reshaped_row.append(item)
            reshaped_data.append(reshaped_row)

        table = Table(reshaped_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Arabic"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        table.wrapOn(c, width, height)
        table.drawOn(c, 50, text_y - 150)

        # Save PDF
        c.save()


class UpdateAdminDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("تغير الادمن و الكود")
        self.setGeometry(300, 300, 400, 200)

        # Create layout
        layout = QVBoxLayout()

        # Create username label and input
        self.username_label = QLabel("الاسم:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Create password label and input
        self.password_label = QLabel("الكود:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide password input
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Create submit button
        self.submit_button = QPushButton("تغيبر")
        self.submit_button.clicked.connect(self.update_admin_credentials)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def update_admin_credentials(self):
        new_username = self.username_input.text()
        new_password = self.password_input.text()

        if new_username and new_password:
            try:
                # Connect to the SQLite database
                conn = sqlite3.connect('agents.db')
                cursor = conn.cursor()

                # Update the first row's username and password in the admin table
                cursor.execute("""
                    UPDATE admin
                    SET username = ?, password = ?
                    WHERE ROWID = (SELECT ROWID FROM admin LIMIT 1)
                """, (new_username, int(new_password)))

                # Commit the changes
                conn.commit()

                # Show success message
                QMessageBox.information(self, "Success", "Admin credentials updated successfully.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

            finally:
                # Close the connection
                conn.close()

                # Close the dialog
                self.accept()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")

class EditAgent(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.populate_table()

    def initUI(self):
        self.setGeometry(100, 100, 900, 700)
        self.setWindowTitle("Edit User Table")

        self.agents_section = QtWidgets.QTableWidget(self)
        self.agents_section.setGeometry(QtCore.QRect(15, 30, 701, 591))
        self.agents_section.setObjectName("agents_section")
        self.agents_section.setColumnCount(9)
        self.agents_section.setHorizontalHeaderLabels(
            [
                "Name",
                "Military Rank",
                "Military Number",
                "General Number",
                "Civil Registry",
                "Mobile Number",
                "Group",
                "Governorate",
                "Remaining Holidays",
            ]
        )
        self.agents_section.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)

        # Connect the cellChanged signal to a custom slot
        self.agents_section.cellChanged.connect(self.cell_changed)

        self.save_button = QtWidgets.QPushButton("Save Changes", self)
        self.save_button.setGeometry(QtCore.QRect(730, 30, 120, 40))
        self.save_button.clicked.connect(self.save_changes)

    def get_users_data(self):
        connection = sqlite3.connect("agents.db")  # Change to your database file name
        cursor = connection.cursor()

        cursor.execute(
            "SELECT name, military_rank, military_number, general_number, civil_registry, mobile_number, the_group, governorate, the_remaining_holidays FROM users"
        )
        data = cursor.fetchall()

        connection.close()
        return data

    def populate_table(self):
        data = self.get_users_data()
        self.agents_section.setRowCount(len(data))

        for row_num, row_data in enumerate(data):
            for col_num, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                if col_num == 2:  # Make the "Military Number" column non-editable
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.agents_section.setItem(row_num, col_num, item)

    def cell_changed(self, row, column):
        item = self.agents_section.item(row, column)
        item.setBackground(QtGui.QColor("#FFEB3B"))  # Highlight the edited cell

    def save_changes(self):
        connection = sqlite3.connect("agents.db")
        cursor = connection.cursor()

        row_count = self.agents_section.rowCount()
        col_count = self.agents_section.columnCount()

        for row in range(row_count):
            row_data = []
            for column in range(col_count):
                item = self.agents_section.item(row, column)
                row_data.append(item.text() if item else "")

            cursor.execute(
                """
                UPDATE users
                SET name=?, military_rank=?, general_number=?, civil_registry=?, mobile_number=?, the_group=?, governorate=?, the_remaining_holidays=?
                WHERE military_number=?
            """,
                (
                    row_data[0],
                    row_data[1],
                    row_data[3],
                    row_data[4],
                    row_data[5],
                    row_data[6],
                    row_data[7],
                    row_data[8],
                    row_data[2],
                ),
            )

        connection.commit()
        connection.close()

        # Reset the background color of all cells
        for row in range(row_count):
            for column in range(col_count):
                item = self.agents_section.item(row, column)
                item.setBackground(QtGui.QColor("white"))


class EditHistory(QtWidgets.QDialog):
    def __init__(self, military_number):
        super().__init__()

        self.military_number = military_number
        self.initUI()
        self.populate_holidays_table()

    def initUI(self):
        self.setGeometry(100, 100, 1000, 800)  # Larger size for the dialog
        self.setWindowTitle("Edit Holidays Table")

        # Create and set up holidays table
        self.Holidays_History = QtWidgets.QTableWidget(self)
        self.Holidays_History.setGeometry(
            QtCore.QRect(10, 60, 820, 700)
        )  # Adjusted size
        self.Holidays_History.setRowCount(60)
        self.Holidays_History.setColumnCount(8)
        self.Holidays_History.setHorizontalHeaderLabels(
            [
                "الرقم العسكرى",
                "نوع الاجازة",
                "مدة الاجازة",
                "تاربخ البداية",
                "تاربخ النهابة",
                "مدة التطويف",
                "اسم المستخدم",
                "تاريخ العودة",
            ]
        )

        # Create and set up save button
        self.save_button = QtWidgets.QPushButton("Save Changes", self)
        self.save_button.setGeometry(
            QtCore.QRect(850, 100, 120, 40)
        )  # Adjusted position
        self.save_button.clicked.connect(self.save_changes)

    def get_holidays_data(self):
        connection = sqlite3.connect("agents.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT military_number, the_kind_of_holiday, duration_of_vacation, start_Date, return_date, duration_of_absence, user_code, check_in_date
            FROM holidays_history
            WHERE military_number = ?
        """,
            (self.military_number,),
        )
        data = cursor.fetchall()
        connection.close()
        return data

    def populate_holidays_table(self):
        data = self.get_holidays_data()
        self.Holidays_History.setRowCount(len(data))

        for row_num, row_data in enumerate(data):
            for col_num, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                if col_num == 0:  # Military Number column
                    item.setFlags(
                        item.flags() & ~QtCore.Qt.ItemIsEditable
                    )  # Make read-only
                self.Holidays_History.setItem(row_num, col_num, item)

    def save_changes(self):
        connection = sqlite3.connect("agents.db")
        cursor = connection.cursor()

        row_count = self.Holidays_History.rowCount()
        col_count = self.Holidays_History.columnCount()

        for row in range(row_count):
            row_data = []
            for column in range(col_count):
                item = self.Holidays_History.item(row, column)
                row_data.append(item.text() if item else "")

            cursor.execute(
                """
                UPDATE holidays_history
                SET the_kind_of_holiday=?, duration_of_vacation=?, start_Date=?, return_date=?, duration_of_absence=?, user_code=?, check_in_date=?
                WHERE military_number=?
            """,
                (
                    row_data[1],
                    row_data[2],
                    row_data[3],
                    row_data[4],
                    row_data[5],
                    row_data[6],
                    row_data[7],
                    row_data[0],
                ),
            )

        connection.commit()
        connection.close()

        # Reset the background color of all cells
        for row in range(row_count):
            for column in range(col_count):
                item = self.Holidays_History.item(row, column)
                item.setBackground(QtGui.QColor("white"))

class Ui_MainWindow(object):
    def save_hijri_date_if_checked(
        self, start_date, return_date, military_number, started_box
    ):
        # Check if the Started_Box checkbox is checked
        if started_box.isChecked():
            # Get today's Gregorian date and convert it to Hijri
            today_hijri = convert.Gregorian.today().to_hijri()

            # Format the Hijri date as YYYY-MM-DD
            hijri_date_str = today_hijri.isoformat()

            # Connect to the SQLite database
            conn = sqlite3.connect("agents.db")
            cursor = conn.cursor()

            # Update the check_in_date with today's Hijri date using the given conditions
            cursor.execute(
                """
                UPDATE holidays_history
                SET check_in_date = ?
                WHERE military_number = ? AND start_Date = ? AND return_date = ?
            """,
                (hijri_date_str, military_number, start_date, return_date),
            )

            # Commit the changes and close the connection
            conn.commit()
            conn.close()

    def get_holiday_data(
        self, start_date_hijri: str, end_date_hijri: str, military_code: int = None
    ) -> List[List]:
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL query to get data between start_date and end_date, and optionally filter by military_code
        query = """
        SELECT military_number, the_kind_of_holiday, duration_of_vacation, start_Date, return_date, duration_of_absence, user_code, check_in_date
        FROM holidays_history
        WHERE start_Date BETWEEN ? AND ?
        """

        # Add filter for military_code if provided
        if military_code is not None:
            query += " AND military_number = ?"
            params = (start_date_hijri, end_date_hijri, military_code)
        else:
            params = (start_date_hijri, end_date_hijri)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Format data
        formatted_data = []
        for row in rows:
            formatted_row = [
                row[0],  # military_number
                row[1],  # the_kind_of_holiday
                row[2],  # duration_of_vacation
                row[3],  # start_Date (Hijri)
                row[4],  # return_date (Hijri)
                row[5],  # duration_of_absence
                row[6],  # user_code
                row[7],  # check_in_date
            ]
            formatted_data.append(formatted_row)

        return formatted_data

    def create_pdf(self, output_filename, table_data, user_name, user_code):
        c = canvas.Canvas(output_filename, pagesize=A4)
        width, height = A4

        # Register the custom Arabic font
        pdfmetrics.registerFont(TTFont("Arabic", "Printing/Amiri-Regular.ttf"))

        # Load the image
        image_path = "Printing/logo.png"  # Replace with the path to your image
        image = ImageReader(image_path)
        image_width, image_height = image.getSize()
        aspect_ratio = image_height / float(image_width)
        image_display_width = width / 8  # Adjust as needed
        image_display_height = image_display_width * aspect_ratio
        image_x = (width - image_display_width) / 2
        image_y = height - image_display_height - 30

        # Draw the image
        c.drawImage(
            image_path,
            image_x,
            image_y,
            width=image_display_width,
            height=image_display_height,
        )

        # Arabic text
        arabic_text1 = "المملكة العربية السعودية"
        reshaped_text1 = arabic_reshaper.reshape(arabic_text1)
        bidi_text1 = get_display(reshaped_text1)

        arabic_text2 = "رئاسة أمن الدولة"
        reshaped_text2 = arabic_reshaper.reshape(arabic_text2)
        bidi_text2 = get_display(reshaped_text2)

        arabic_text3 = "قوات الطوارئ الخاصة"
        reshaped_text3 = arabic_reshaper.reshape(arabic_text3)
        bidi_text3 = get_display(reshaped_text3)

        # Add text to PDF
        text_y = 800
        c.setFont("Arabic", 10)
        c.drawRightString(width - 20, text_y, bidi_text1)
        c.drawRightString(width - 20, text_y - 20, bidi_text2)
        c.drawRightString(width - 20, text_y - 40, bidi_text3)

        # Additional text on the other side of the page
        arabic_text4 = f"الكود الخاص : {user_code}"
        reshaped_text4 = arabic_reshaper.reshape(arabic_text4)
        bidi_text4 = get_display(reshaped_text4)

        arabic_text5 = f"الاسم : {user_name}"
        reshaped_text5 = arabic_reshaper.reshape(arabic_text5)
        bidi_text5 = get_display(reshaped_text5)

        c.drawRightString(120, text_y, bidi_text4)
        c.drawRightString(150, text_y - 20, bidi_text5)

        # Table headers
        headers = [
            "الرقم العسكري",
            "اسم المستخدم",
            "مدة التطويف",
            "تاريخ النهاية",
            "تاريخ البدابة",
            "مدة الاجازة",
            "نوع الاجازة",
            "تاريخ العودة",
        ]

        # Reorder the data to match headers
        sorted_data = [headers]  # Start with headers
        for row in table_data:
            sorted_row = [
                row[0],  # الرقم العسكري
                row[6],  # اسم المستخدم
                row[5],  # مدة التطويف
                row[3],  # تاريخ النهاية
                row[4],  # تاريخ البدابة
                row[2],  # مدة الاجازة
                row[1],  # نوع الاجازة
                row[7],  # تاريخ العودة
            ]
            sorted_data.append(sorted_row)

        # Reshape Arabic text in the table
        reshaped_data = []
        for row in sorted_data:
            reshaped_row = []
            for item in row:
                if isinstance(item, str):
                    reshaped_item = arabic_reshaper.reshape(item)
                    bidi_item = get_display(reshaped_item)
                    reshaped_row.append(bidi_item)
                else:
                    reshaped_row.append(item)
            reshaped_data.append(reshaped_row)

        table = Table(reshaped_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Arabic"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        table.wrapOn(c, width, height)
        table.drawOn(c, 50, text_y - 150)

        # Save PDF
        c.save()

    def check_in_date_status(self, military_number):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL statement to retrieve relevant data using military_number
        query = """
        SELECT the_kind_of_holiday, duration_of_vacation, Start_Date, Return_date, duration_of_absence, user_code, check_in_date 
        FROM holidays_history
        WHERE military_number = ?;
        """

        # Execute the query
        cursor.execute(query, (military_number,))
        result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            (
                the_kind_of_holiday,
                duration_of_vacation,
                start_date_hijri,
                return_date_hijri,
                duration_of_absence,
                user_code,
                check_in_date,
            ) = result
            print(type(result[6]))
            if result[6] == None:
                # Convert Hijri dates to Gregorian
                if return_date_hijri:
                    return_date_hijri_obj = convert.Hijri(
                        *map(int, return_date_hijri.split("-"))
                    )
                    return_date_gregorian = return_date_hijri_obj.to_gregorian()
                    return_date_gregorian_date = date(
                        return_date_gregorian.year,
                        return_date_gregorian.month,
                        return_date_gregorian.day,
                    )
                else:
                    return_date_gregorian_date = None

                # Calculate the remaining days
                current_date_gregorian = datetime.now().date()
                if return_date_gregorian_date:
                    remaining_days = (
                        return_date_gregorian_date - current_date_gregorian
                    ).days
                    if remaining_days < 0:
                        remaining_days = 0
                else:
                    remaining_days = None

                # Set the checkbox state
                # self.Started_Box.setChecked(bool(check_in_date))

                return {
                    "current_date_hijri": convert.Gregorian(
                        current_date_gregorian.year,
                        current_date_gregorian.month,
                        current_date_gregorian.day,
                    ).to_hijri(),
                    "remaining_days": remaining_days,
                    "the_kind_of_holiday": the_kind_of_holiday,
                    "duration_of_vacation": duration_of_vacation,
                    "start_Date": start_date_hijri,
                    "return_date": return_date_hijri,
                    "duration_of_absence": duration_of_absence,
                    "user_code": user_code,
                    "check_in_date": (
                        check_in_date if check_in_date else "Not checked in"
                    ),
                }
            else:
                return False
        else:
            return None

    def get_name_by_military_number(self, military_number):
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()
        query = "SELECT name FROM users WHERE military_number = ?"
        cursor.execute(query, (military_number,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            return "Name not found"

    def alert_new_absentees(self):
        absentees = self.fetch_current_absentees()
        print(type(absentees))  # For debugging purposes

        if absentees:
            absent_message = "تحقق من قائمة التطويف\n"
            for military_number, return_date, check_in_date in absentees:
                print(military_number, return_date, check_in_date)
                absent_message += (
                    f"الاسم : {self.get_name_by_military_number(military_number)}\n"
                )

            # Display the alert
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle("Absent Alert")
            msg_box.setText(absent_message)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            # Optional: Display a message if no absentees are found
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Absent Alert")
            msg_box.setText("No new absentees detected.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def fetch_current_absentees(self):
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # Get the current Gregorian date and convert it to Hijri
        current_date_gregorian = datetime.now().date()
        current_date_hijri = convert.Gregorian(
            current_date_gregorian.year,
            current_date_gregorian.month,
            current_date_gregorian.day,
        ).to_hijri()
        current_date_hijri_str = f"{current_date_hijri.year}-{current_date_hijri.month:02d}-{current_date_hijri.day:02d}"

        query = """
            SELECT military_number, return_date, check_in_date
            FROM holidays_history
            WHERE Return_date < ?
            AND (check_in_date IS NULL OR check_in_date = '');
        """

        cursor.execute(query, (current_date_hijri_str,))
        absentees = cursor.fetchall()

        filtered_absentees = []

        for absentee in absentees:
            military_number, return_date_hijri, check_in_date_hijri = absentee

            if return_date_hijri:
                return_date_hijri_obj = convert.Hijri(
                    *map(int, return_date_hijri.split("-"))
                )
                return_date_gregorian = return_date_hijri_obj.to_gregorian()
                return_date_gregorian_date = date(
                    return_date_gregorian.year,
                    return_date_gregorian.month,
                    return_date_gregorian.day,
                )
            else:
                return_date_gregorian_date = None

            current_date_gregorian = datetime.now().date()

            if return_date_gregorian_date:
                duration_of_absence = (
                    current_date_gregorian - return_date_gregorian_date
                ).days
            else:
                duration_of_absence = None
            print(duration_of_absence)
            if duration_of_absence == 1:
                filtered_absentees.append(
                    {
                        "military_number": military_number,
                        "return_date": return_date_hijri,
                        "check_in_date": check_in_date_hijri,
                    }
                )

        conn.close()

        return filtered_absentees

    def update_check_in_date(self, state):
        if state == QtCore.Qt.Checked:
            # Get the current Hijri date
            current_date_gregorian = datetime.now().date()
            current_date_hijri = convert.Gregorian(
                current_date_gregorian.year,
                current_date_gregorian.month,
                current_date_gregorian.day,
            ).to_hijri()
            current_date_hijri_str = f"{current_date_hijri.year}-{current_date_hijri.month:02d}-{current_date_hijri.day:02d}"

            # Update the database
            conn = sqlite3.connect("agents.db")
            cursor = conn.cursor()
            query = """
                UPDATE holidays_history
                SET check_in_date = ?
                WHERE military_number = ?
                AND Start_Date <= ?
                AND Return_date >= ?;
                """
            cursor.execute(
                query,
                (
                    current_date_hijri_str,
                    self.Military_Code.text(),
                    current_date_hijri_str,
                    current_date_hijri_str,
                ),
            )
            conn.commit()
            conn.close()
        else:
            # Optionally handle the case when the checkbox is unchecked
            pass

    def add_data_to_table(self, name, duration):
        row_position = self.alert_section.rowCount()
        self.alert_section.insertRow(row_position)

        name_item = QtWidgets.QTableWidgetItem(self.get_name_by_military_number(name))
        duration_item = QtWidgets.QTableWidgetItem(duration)

        self.alert_section.setItem(row_position, 0, name_item)
        self.alert_section.setItem(row_position, 1, duration_item)

    def run_holiday_history_dialog(self, military_code, name):
        self.edit_window = HolidayHistoryDialog("agents.db", military_code, name)
        self.edit_window.exec_()

    def query_name_from_db(self, military_number):
        conn = sqlite3.connect("military_users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM users WHERE military_number = ?", (military_number,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    def get_today_hijri_date(self):
        today_gregorian = date.today()
        today_hijri = convert.Gregorian(
            today_gregorian.year, today_gregorian.month, today_gregorian.day
        ).to_hijri()
        return today_hijri

    def days_between_hijri_dates(self, start_date_str, end_date_str):
        start_date = convert.Hijri(*map(int, start_date_str.split("-"))).to_gregorian()
        end_date = convert.Hijri(*map(int, end_date_str.split("-"))).to_gregorian()
        delta = end_date - start_date
        return delta.days

    def check_absent(self):
        connection = sqlite3.connect("agents.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT military_number, return_date, check_in_date FROM holidays_history"
        )
        data = cursor.fetchall()

        today_hijri = self.get_today_hijri_date()
        today_hijri_str = (
            f"{today_hijri.year}-{today_hijri.month:02d}-{today_hijri.day:02d}"
        )

        absentees = []

        for row in data:
            military_number, return_date, check_in_date = row
            if not check_in_date:  # Only process if check_in_date is empty
                if return_date:
                    days_diff = self.days_between_hijri_dates(
                        return_date, today_hijri_str
                    )
                    if days_diff > 0:
                        absentees.append((military_number, days_diff))
                    elif days_diff == 1:
                        absentees.append((military_number, days_diff))

        connection.close()
        return absentees

    def separate_absentees(self, data):
        military_numbers = []
        days_absent = []

        for military_number, days_absent_count in data:
            military_numbers.append(military_number)
            days_absent.append(days_absent_count)

        return military_numbers, days_absent

    def check_and_display_absents(self):
        absentees = self.check_absent()
        military_numbers, days_absent = self.separate_absentees(absentees)

        # Clear the table before adding new data
        self.alert_section.setRowCount(0)

        for military_number, days in zip(military_numbers, days_absent):
            self.add_data_to_table(str(military_number), str(days))

    def open_edit_History(self, military_number):
        # Request military number from the user
        self.edit_window = EditHistory(military_number)
        self.edit_window.exec_()  # Open the dialog as modal

    def populate_table(self):
        data = self.get_users_data()
        self.agents_section.setRowCount(len(data))

        for row_num, row_data in enumerate(data):
            for col_num, col_data in enumerate(row_data):
                self.agents_section.setItem(
                    row_num, col_num, QtWidgets.QTableWidgetItem(str(col_data))
                )

    def open_edit_Agent(self):
        self.edit_window = EditAgent()
        self.edit_window.exec_()  # Open the dialog as modal

    def get_users_data(self):
        # Connect to the SQLite database
        connection = sqlite3.connect("agents.db")  # Change to your database file name
        cursor = connection.cursor()

        # Fetch all data from the users table
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()

        # Close the connection
        connection.close()
        return data

    def calculate_all_durations_of_absence(self):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()
        # SQL statement to get all military numbers, return_date, and check_in_date
        query = """
        SELECT military_number, return_date, check_in_date 
        FROM holidays_history;
        """

        # Execute the query
        cursor.execute(query)
        results = cursor.fetchall()

        for result in results:
            military_number, return_date_hijri, check_in_date_hijri = result

            # Convert Hijri dates to Gregorian
            if return_date_hijri:
                return_date_hijri_obj = convert.Hijri(
                    *map(int, return_date_hijri.split("-"))
                )
                return_date_gregorian = return_date_hijri_obj.to_gregorian()
                return_date_gregorian_date = date(
                    return_date_gregorian.year,
                    return_date_gregorian.month,
                    return_date_gregorian.day,
                )
            else:
                return_date_gregorian_date = None

            # If check_in_date is empty, set it to today's date
            if check_in_date_hijri:
                check_in_date_hijri_obj = convert.Hijri(
                    *map(int, check_in_date_hijri.split("-"))
                )
                check_in_date_gregorian = check_in_date_hijri_obj.to_gregorian()
                check_in_date_gregorian_date = date(
                    check_in_date_gregorian.year,
                    check_in_date_gregorian.month,
                    check_in_date_gregorian.day,
                )
            else:
                current_date_gregorian = datetime.now().date()
                check_in_date_hijri_obj = convert.Gregorian(
                    current_date_gregorian.year,
                    current_date_gregorian.month,
                    current_date_gregorian.day,
                ).to_hijri()
                check_in_date_hijri = f"{check_in_date_hijri_obj.year}-{check_in_date_hijri_obj.month:02d}-{check_in_date_hijri_obj.day:02d}"
                check_in_date_gregorian_date = current_date_gregorian

            # Calculate the duration of absence
            if return_date_gregorian_date and check_in_date_gregorian_date:
                duration_of_absence = (
                    check_in_date_gregorian_date - return_date_gregorian_date
                ).days
            else:
                duration_of_absence = None

            # Update the duration_of_absence and possibly check_in_date in the database
            update_query = """
            UPDATE holidays_history
            SET duration_of_absence = ?
            WHERE military_number = ? AND return_date = ?;
            """
            cursor.execute(
                update_query,
                (
                    duration_of_absence,
                    military_number,
                    return_date_hijri,
                ),
            )

        # Commit the changes and close the database connection
        conn.commit()
        conn.close()

        print("Duration of absence updated for all records.")

    def show_add_admin_dialog(self):
        check = self.check_admin()
        if check != False:
            dialog = QtWidgets.QDialog()
            dialog.setWindowTitle("Add Admin User")

            layout = QtWidgets.QVBoxLayout(dialog)

            user_name_label = QtWidgets.QLabel("User Name:")
            user_name_input = QtWidgets.QLineEdit()
            layout.addWidget(user_name_label)
            layout.addWidget(user_name_input)

            user_code_label = QtWidgets.QLabel("User Code:")
            user_code_input = QtWidgets.QLineEdit()
            layout.addWidget(user_code_label)
            layout.addWidget(user_code_input)

            submit_button = QtWidgets.QPushButton("Submit")
            layout.addWidget(submit_button)

            def submit():
                user_name = user_name_input.text()
                user_code = user_code_input.text()

                if user_name and user_code:
                    # Connect to the database
                    conn = sqlite3.connect("agents.db")
                    cursor = conn.cursor()

                    # Insert the new admin user
                    query = """
                    INSERT INTO admin_users (user_name, user_code)
                    VALUES (?, ?)
                    """
                    cursor.execute(query, (user_name, user_code))
                    conn.commit()
                    conn.close()

                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.warning(
                        dialog, "Input Error", "All fields are required."
                    )

            submit_button.clicked.connect(submit)

            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                print("Admin user added successfully.")
        else:
            pass

    def add_value_to_row(self, military_number, end_time, column_name, new_value):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()
        # Convert the end time to Hijri
        new_value_hijri = convert.Gregorian(
            new_value.year, new_value.month, new_value.day
        ).to_hijri()
        new_value_hijri_str = f"{new_value_hijri.year}-{new_value_hijri.month:02d}-{new_value_hijri.day:02d}"

        # SQL statement to update the specific column value
        query = f"""
        UPDATE holidays_history
        SET {column_name} = ?
        WHERE military_number = ?
        AND Return_date = ?;
        """

        # Execute the query
        cursor.execute(query, (new_value_hijri_str, military_number, end_time))
        conn.commit()

        # Close the database connection
        conn.close()
        print(
            f"{column_name} updated to {new_value_hijri_str} for military number {military_number} with end date {new_value}."
        )

    def get_admin_user(self, user_code):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL statement to check for the user_code
        query = """
        SELECT user_name FROM admin_users WHERE user_code = ?;
        """

        # Execute the query
        cursor.execute(query, (user_code,))
        result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            return result[0]  # Return the user_name
        else:
            return None
    def change_admin_tr(self):
        self.check_admin()
        self.change_admin = UpdateAdminDialog()
        self.change_admin.exec_()
    def get_admin(self, user_code):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL statement to check for the user_code
        query = """
            SELECT username FROM admin WHERE password = ?;
            """

        # Execute the query
        cursor.execute(query, (user_code,))
        result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            return result[0]  # Return the user_name
        else:
            return None

    def check_admin_user(self):
        input_dialog = QtWidgets.QInputDialog(self)
        input_dialog.setWindowTitle("التحقق من هوية المستخدم")
        input_dialog.setLabelText("ادخل الكود الخاص بك:")
        input_dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
        input_dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
        ok = input_dialog.exec_()
        user_code = input_dialog.textValue()

        print(user_code)
        if ok:
            user_name = self.get_admin_user(user_code)
            if user_name:
                QtWidgets.QMessageBox.information(
                    self,
                    "تم الاضافة بنجاح",
                    f"المستخدم : {user_name}",
                )
                return user_code
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "تعذر الاضافة",
                    f"لم يتم العثور علي المتسخدم",
                )
                return False
        else:
            return False

    def check_admin(self):
        input_dialog = QtWidgets.QInputDialog(self)
        input_dialog.setWindowTitle("التحقق من هوية المستخدم")
        input_dialog.setLabelText("ادخل الكود الخاص بك:")
        input_dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
        input_dialog.setTextEchoMode(QtWidgets.QLineEdit.Password)
        ok = input_dialog.exec_()
        user_code = input_dialog.textValue()

        print(user_code)
        if ok:
            user_name = self.get_admin(user_code)
            if user_name:
                QtWidgets.QMessageBox.information(
                    self,
                    "تم الاضافة بنجاح",
                    f"المستخدم : {user_name}",
                )
                return user_code
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    " خطاء في الادخال",
                    f"لم يتم العثور علي المتسخدم",
                )
                return False
        else:
            return False

    def check_current_holiday(self, military_number):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # Get the current Gregorian date and convert it to Hijri
        current_date_gregorian = datetime.now().date()
        current_date_hijri = convert.Gregorian(
            current_date_gregorian.year,
            current_date_gregorian.month,
            current_date_gregorian.day,
        ).to_hijri()
        current_date_hijri_str = f"{current_date_hijri.year}-{current_date_hijri.month:02d}-{current_date_hijri.day:02d}"

        # SQL statement to check for a running holiday or a holiday without a check_in_date
        query = """
            SELECT the_kind_of_holiday, duration_of_vacation, Start_Date, Return_date, duration_of_absence, user_code, check_in_date
            FROM holidays_history
            WHERE military_number = ?
            AND Start_Date <= ?
            AND Return_date >= ?
            AND (check_in_date IS NULL OR check_in_date = '');
            """

        # Execute the query
        cursor.execute(
            query, (military_number, current_date_hijri_str, current_date_hijri_str)
        )
        result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            (
                the_kind_of_holiday,
                duration_of_vacation,
                start_date_hijri,
                return_date_hijri,
                duration_of_absence,
                user_code,
                check_in_date,
            ) = result

            return_date_hijri_obj = convert.Hijri(
                *map(int, return_date_hijri.split("-"))
            )
            return_date_gregorian = return_date_hijri_obj.to_gregorian()
            return_date_gregorian_date = date(
                return_date_gregorian.year,
                return_date_gregorian.month,
                return_date_gregorian.day,
            )
            remaining_days = (return_date_gregorian_date - current_date_gregorian).days
            if remaining_days < 0:
                remaining_days = 0
                return remaining_days
            # Set the checkbox state based on check_in_date
            if check_in_date:
                self.Started_Box.setChecked(True)
            else:
                self.Started_Box.setChecked(False)

            return {
                "current_date_hijri": current_date_hijri_str,
                "remaining_days": remaining_days,
                "the_kind_of_holiday": the_kind_of_holiday,
                "duration_of_vacation": duration_of_vacation,
                "start_Date": start_date_hijri,
                "return_date": return_date_hijri,
                "duration_of_absence": duration_of_absence,
                "user_code": user_code,
                "check_in_date": check_in_date,
            }
        else:
            return False

    def uptodate_history(self):
        try:
            results = self.search_holidays_by_military_number(self.Military_Code.text())
            self.Holidays_History.setRowCount(
                len(results)
            )  # Set the row count to the number of results
            for row_num, row_data in enumerate(results):
                for col_num, data in enumerate(row_data):
                    self.Holidays_History.setItem(
                        row_num, col_num, QtWidgets.QTableWidgetItem(str(data))
                    )
        except Exception as e:
            pass

    def search_holidays_by_military_number(self, military_number):
        # Convert current date to Hijri
        today = QtCore.QDate.currentDate()

        hijri_year = (
            convert.Gregorian(today.year(), today.month(), today.day()).to_hijri().year
        )

        hijri_year = str(hijri_year)

        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # SQL statement to search for the military number and filter by Hijri year
        search_query = """
        SELECT * FROM holidays_history
        WHERE military_number = ?
        AND strftime('%Y', start_Date) = ?;
        """
        print(hijri_year)
        # Execute the query
        cursor.execute(search_query, (military_number, hijri_year))
        results = cursor.fetchall()

        # Close the database connection
        conn.close()

        return results

    def update_placeholder_text(self):
        self.Holiday_End_input.setText(
            str(self.hijri_date_and_future(self.Holiday_Duration_input.value()))
        )

    def hijri_date_and_future(self, days):
        # Get the current Gregorian date
        current_date = datetime.now()
        hijri_date_str = self.Holiday_Start_input.text()
        try:
            year, month, day = map(int, hijri_date_str.split("-"))
            gregorian_date = convert.Hijri(year, month, day).to_gregorian()
        except ValueError:
            gregorian_date = current_date
            return gregorian_date
        current_date = gregorian_date
        # Convert the current Gregorian date to Hijri date
        hijri_date = convert.Gregorian(
            current_date.year, current_date.month, current_date.day
        ).to_hijri()

        # Calculate the future Gregorian date
        future_date = current_date + timedelta(days=days)

        # Convert the future Gregorian date to Hijri date
        future_hijri_date = convert.Gregorian(
            future_date.year, future_date.month, future_date.day
        ).to_hijri()

        return future_hijri_date

    def hijri_date(self):
        # Get the current Gregorian date
        current_date = datetime.now()
        hijri_date = convert.Gregorian(
            current_date.year, current_date.month, current_date.day
        ).to_hijri()
        return hijri_date

    def edit_remaining_holidays(self, military_number, days):
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        try:
            # SQL statement to update the_remaining_holidays column
            update_sql = """
            UPDATE users
            SET the_remaining_holidays = the_remaining_holidays - ?
            WHERE military_number = ?
            """

            cursor.execute(update_sql, (days, military_number))

            conn.commit()

            print("Remaining holidays updated successfully!")

        except sqlite3.Error as e:
            print(f"Error: {e}")

        finally:
            cursor.close()
            conn.close()

    def search_user_by_code(self, user_code):

        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        search_query = """
        SELECT user_name FROM admin_users WHERE user_code = ?;
        """

        cursor.execute(search_query, (user_code,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        else:
            return "User not found"

    def add_holiday(
        self,
        military_number,
        the_kind_of_holiday,
        duration_of_vacation,
        start_date,
        return_date,
    ):
        try:
            user_code = self.check_admin_user()
            if not user_code:
                pass
            else:
                conn = sqlite3.connect("agents.db")
                cursor = conn.cursor()
                duration_of_absence = "0"
                try:
                    insert_sql = """
                    INSERT INTO holidays_history (military_number, the_kind_of_holiday, duration_of_vacation, start_date, duration_of_absence, return_date, user_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(
                        insert_sql,
                        (
                            military_number,
                            the_kind_of_holiday,
                            duration_of_vacation,
                            start_date,
                            duration_of_absence,
                            return_date,
                            user_code,
                        ),
                    )
                    conn.commit()
                    print("Holiday added successfully!")
                except sqlite3.Error as e:
                    print(f"Error: {e}")

                finally:
                    cursor.close()
                    conn.close()
                    self.edit_remaining_holidays(military_number, duration_of_vacation)
        except Exception as e:
            print(f"Error: {e}")
            return

    def save_agent_data(
        self,
        military_number,
        name,
        general_number,
        military_rank,
        governorate,
        mobile_number,
        civil_registry,
        the_group,
    ):
        try:
            user_code = self.check_admin_user()
            if not user_code:
                pass
            else:
                the_remaining_holidays = 60
                # Connect to the database
                conn = sqlite3.connect("agents.db")
                cursor = conn.cursor()
                if not military_number.isnumeric():
                    print("Error: Military number must be numeric.")
                    return
                # SQL statement to create the table if it doesn't exist
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    "military_number"	NUMERIC,
                    "name"	TEXT,
                    "general_number"	NUMERIC,
                    "military_rank"	TEXT NOT NULL,
                    "governorate"	TEXT NOT NULL,
                    "mobile_number"	NUMERIC NOT NULL,
                    "civil_registry"	NUMERIC NOT NULL,
                    "the_group"	TEXT NOT NULL,
                    "the_remaining_holidays"	NUMERIC NOT NULL,
                    "user_code"	NUMERIC,
                    PRIMARY KEY("military_number")
                );
                """
                # Execute the SQL statement to create the table
                cursor.execute(create_table_sql)

                # SQL statement to insert data into the table
                insert_data_sql = """
                INSERT INTO users (military_number, name, general_number, military_rank, governorate, mobile_number, civil_registry, the_group, the_remaining_holidays, user_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """

                # Execute the SQL statement to insert data
                cursor.execute(
                    insert_data_sql,
                    (
                        military_number,
                        name,
                        general_number,
                        military_rank,
                        governorate,
                        mobile_number,
                        civil_registry,
                        the_group,
                        the_remaining_holidays,
                        user_code,
                    ),
                )

                # Commit the changes and close the connection
                conn.commit()
                conn.close()
                print("done")

        except Exception as e:
            print(f"Error: {e}")
            return

    def search_user_by_military_number(self, military_number):
        # Calculate all durations of absence
        try:
            self.calculate_all_durations_of_absence()
        except Exception as e:
            print(f"Error: {e}")
            return None

        # Connect to the agents database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # Define the SQL query to search for a user by military number
        # Define the query
        query = """
        SELECT military_number, name, general_number, military_rank, governorate, mobile_number, civil_registry, the_group, the_remaining_holidays,user_code
        FROM users
        WHERE military_number = ?
        """

        # Execute the query
        cursor.execute(query, (military_number,))
        result = cursor.fetchone()

        # Close the database connection
        # Close the connection
        conn.close()

        # If a result is found, create a dictionary with the user data
        if result:
            agent_data = {
                "military_number": result[0],
                "name": result[1],
                "general_number": result[2],
                "military_rank": result[3],
                "governorate": result[4],
                "mobile_number": result[5],
                "civil_registry": result[6],
                "the_group": result[7],
                "the_remaining_holidays": result[8],
                "user_code": result[9],
            }

            # Set the content of the Agent_Data text browser with the user data
            # Display the result in Agent_Data text browser
            self.Agent_Data.setHtml(
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
                '<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">الاسم:{agent_data['name']}"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">الرتبة : {agent_data['military_rank']}</span></p>"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\"> الرقم الخاص : {agent_data['military_number']}</span></p>\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">الرقم العام : {agent_data['general_number']}</span></p>\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">السجل : {agent_data['civil_registry']}</span></p>\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">الجوال : {agent_data['mobile_number']} </span></p>\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">المجموعة : {agent_data['the_group']}</span></p></body></html>"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">الملاك : {agent_data['governorate']}</span></p>\n"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\"> المتبقي من الرصيد : {agent_data['the_remaining_holidays']} </span></p></body></html>"
                f"<p align=\"right\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">اسم المستخدم : {self.search_user_by_code(agent_data['user_code'])}</span></p></body></html>"
            )

            # Search for the current holiday of the user
            try:
                results = self.search_holidays_by_military_number(military_number)
                self.Holidays_History.setRowCount(
                    len(results)
                )  # Set the row count to the number of results
                for row_num, row_data in enumerate(results):
                    for col_num, data in enumerate(row_data):
                        self.Holidays_History.setItem(
                            row_num, col_num, QtWidgets.QTableWidgetItem(str(data))
                        )

                while_holiday = self.check_current_holiday(military_number)
                unchecked_holiday = self.check_in_date_status(military_number)
                if unchecked_holiday != False:
                    print(unchecked_holiday)
                    print(while_holiday)
                    # self.Started_Box.setChecked(False)
                    if while_holiday == False:
                        currnet_holiday = unchecked_holiday
                        # self.Started_Box.setChecked(False)
                        self.save_hijri_date_if_checked(
                            currnet_holiday["start_Date"],
                            currnet_holiday["return_date"],
                            military_number,
                            self.Started_Box,
                        )
                        self.Current_Holiday_Kind.setText(
                            f"نوع الاجازة : {currnet_holiday['the_kind_of_holiday']}"
                        )
                        self.Current_Holiday_Duration.setText(
                            f"مدة الاجازة : {currnet_holiday['duration_of_vacation']}"
                        )
                        self.Current_Holiday_Start.setText(
                            f"تاريخ البدء : {currnet_holiday['start_Date']}"
                        )
                        self.Current_Holiday_End.setText(
                            f"تاريخ الانتهاء : {currnet_holiday['return_date']}"
                        )
                        self.Absence_Period.setText(
                            f"فترة الغياب : {currnet_holiday['duration_of_absence']}"
                        )
                        self.Remaining_Days.setText(
                            f"الايام المتبقية : {currnet_holiday['remaining_days']}"
                        )

                    else:
                        currnet_holiday = while_holiday
                        self.Current_Holiday_Kind.setText(
                            f"نوع الاجازة : {currnet_holiday['the_kind_of_holiday']}"
                        )
                        self.Current_Holiday_Duration.setText(
                            f"مدة الاجازة : {currnet_holiday['duration_of_vacation']}"
                        )
                        self.Current_Holiday_Start.setText(
                            f"تاريخ البدء : {currnet_holiday['start_Date']}"
                        )
                        self.Current_Holiday_End.setText(
                            f"تاريخ الانتهاء : {currnet_holiday['return_date']}"
                        )
                        self.Absence_Period.setText(
                            f"فترة الغياب : {currnet_holiday['duration_of_absence']}"
                        )
                        self.Remaining_Days.setText(
                            f"الايام المتبقية : {currnet_holiday['remaining_days']}"
                        )
                else:
                    self.Current_Holiday_Kind.setText(f"نوع الاجازة : ")
                    self.Current_Holiday_Duration.setText(f"مدة الاجازة : ")
                    self.Current_Holiday_Start.setText(f"تاريخ البدء : ")
                    self.Current_Holiday_End.setText(f"تاريخ الانتهاء : ")
                    self.Absence_Period.setText(f"فترة الغياب : ")
                    self.Remaining_Days.setText(f"الايام المتبقية : ")

            except Exception as e:
                print(f"Error occurred: {e}")
            if self.Started_Box.isChecked():
                print("good")
                # self.save_check_in_date(military_number)

        else:
            self.Agent_Data.setHtml("لا يوجد فرد بهذه البيانات")

        return agent_data if result else False

    def setupUi(self, MainWindow):
        self.alert_new_absentees
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_placeholder_text)
        self.timer.timeout.connect(self.populate_table)
        self.timer.timeout.connect(self.uptodate_history)
        self.timer.timeout.connect(self.check_and_display_absents)
        self.timer.start(1000)  # Update every second
        MainWindow.setObjectName("MMS")
        MainWindow.resize(1142, 724)
        MainWindow.setWindowIcon(QIcon("icon.png"))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(30, 20, 1081, 651))
        self.tabWidget.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.tabWidget.setObjectName("tabWidget")
        self.main = QtWidgets.QWidget()
        self.main.setObjectName("main")
        self.Military_Code = QtWidgets.QLineEdit(self.main)
        self.Military_Code.setGeometry(QtCore.QRect(945, 20, 113, 20))
        self.Military_Code.setText("")
        self.Military_Code.setObjectName("Military_Code")
        self.Agent_Data = QtWidgets.QTextBrowser(self.main)
        self.Agent_Data.setGeometry(QtCore.QRect(640, 60, 421, 181))
        self.Agent_Data.setObjectName("Agent_Data")
        self.Search_Bycode = QtWidgets.QPushButton(self.main)
        self.Search_Bycode.setGeometry(QtCore.QRect(855, 20, 75, 23))
        self.Search_Bycode.setObjectName("Search_Bycode")
        self.Search_Bycode.clicked.connect(
            lambda: self.search_user_by_military_number(self.Military_Code.text())
        )

        self.Currnet_Holiday = QtWidgets.QFrame(self.main)
        self.Currnet_Holiday.setGeometry(QtCore.QRect(860, 250, 201, 181))
        self.Currnet_Holiday.setAutoFillBackground(False)
        self.Currnet_Holiday.setStyleSheet("background-color: rgb(223, 223, 223);")
        self.Currnet_Holiday.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Currnet_Holiday.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Currnet_Holiday.setObjectName("Currnet_Holiday")
        self.Started_Box = QtWidgets.QCheckBox(self.Currnet_Holiday)
        self.Started_Box.setGeometry(QtCore.QRect(50, 150, 101, 21))
        self.Started_Box.setObjectName("Started_Box")
        self.Started_Box.stateChanged.connect(self.update_check_in_date)
        self.Currnet_Holiday_label = QtWidgets.QLabel(self.Currnet_Holiday)
        self.Currnet_Holiday_label.setGeometry(QtCore.QRect(60, 0, 71, 20))
        self.Currnet_Holiday_label.setObjectName("Currnet_Holiday_label")
        self.formLayoutWidget_2 = QtWidgets.QWidget(self.Currnet_Holiday)
        self.formLayoutWidget_2.setGeometry(QtCore.QRect(20, 30, 160, 110))
        self.formLayoutWidget_2.setObjectName("formLayoutWidget_2")
        self.formLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_2)
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2.setObjectName("formLayout_2")
        self.Current_Holiday_Kind = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Current_Holiday_Kind.setObjectName("Current_Holiday_Kind")
        self.formLayout_2.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.Current_Holiday_Kind
        )
        self.Current_Holiday_Duration = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Current_Holiday_Duration.setObjectName("Current_Holiday_Duration")
        self.formLayout_2.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.Current_Holiday_Duration
        )
        self.Current_Holiday_Start = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Current_Holiday_Start.setObjectName("Current_Holiday_Start")
        self.formLayout_2.setWidget(
            2, QtWidgets.QFormLayout.LabelRole, self.Current_Holiday_Start
        )
        self.Current_Holiday_End = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Current_Holiday_End.setObjectName("Current_Holiday_End")
        self.formLayout_2.setWidget(
            3, QtWidgets.QFormLayout.LabelRole, self.Current_Holiday_End
        )
        self.Absence_Period = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Absence_Period.setObjectName("Absence_Period")
        self.formLayout_2.setWidget(
            4, QtWidgets.QFormLayout.LabelRole, self.Absence_Period
        )
        self.Remaining_Days = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.Remaining_Days.setObjectName("Remaining_Days")
        self.formLayout_2.setWidget(
            5, QtWidgets.QFormLayout.LabelRole, self.Remaining_Days
        )
        self.Add_Holiday_Frame = QtWidgets.QFrame(self.main)
        self.Add_Holiday_Frame.setGeometry(QtCore.QRect(640, 250, 201, 181))
        self.Add_Holiday_Frame.setStyleSheet("background-color: rgb(223, 223, 223);")
        self.Add_Holiday_Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Add_Holiday_Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Add_Holiday_Frame.setObjectName("Add_Holiday_Frame")
        self.Add_Holiday_btn = QtWidgets.QPushButton(self.Add_Holiday_Frame)
        self.Add_Holiday_btn.setGeometry(QtCore.QRect(60, 150, 75, 23))
        self.Add_Holiday_btn.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.Add_Holiday_btn.setObjectName("Add_Holiday_btn")
        self.Add_Holiday_btn.clicked.connect(
            lambda: self.add_holiday(
                str(self.Military_Code.text()),
                str(self.comboBox.currentText()),
                str(self.Holiday_Duration_input.text()),
                str(self.Holiday_Start_input.text()),
                str(self.Holiday_End_input.text()),
            )
        )
        self.formLayoutWidget = QtWidgets.QWidget(self.Add_Holiday_Frame)
        self.formLayoutWidget.setGeometry(QtCore.QRect(20, 30, 160, 111))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.Holiday_Duration = QtWidgets.QLabel(self.formLayoutWidget)
        self.Holiday_Duration.setObjectName("Holiday_Duration")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.Holiday_Duration
        )
        self.Holiday_Duration_input = QtWidgets.QSpinBox(self.formLayoutWidget)
        self.Holiday_Duration_input.setObjectName("Holiday_Duration_input")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.Holiday_Duration_input
        )
        self.Holiday_Start = QtWidgets.QLabel(self.formLayoutWidget)
        self.Holiday_Start.setObjectName("Holiday_Start")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.Holiday_Start
        )
        self.Holiday_Start_input = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.Holiday_Start_input.setObjectName("Holiday_Start_input")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.Holiday_Start_input
        )
        self.Holiday_End = QtWidgets.QLabel(self.formLayoutWidget)
        self.Holiday_End.setObjectName("Holiday_End")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.Holiday_End)
        self.Holiday_End_input = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.Holiday_End_input.setObjectName("Holiday_End_input")
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.Holiday_End_input
        )
        self.comboBox = QtWidgets.QComboBox(self.formLayoutWidget)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.comboBox)
        self.Holiday_Kind = QtWidgets.QLabel(self.formLayoutWidget)
        self.Holiday_Kind.setObjectName("Holiday_Kind")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.Holiday_Kind)
        self.Holidays_History = QtWidgets.QTableWidget(self.main)
        self.Holidays_History.setGeometry(QtCore.QRect(10, 60, 621, 371))
        self.Holidays_History.setRowCount(60)
        self.Holidays_History.setColumnCount(7)
        self.Holidays_History.setObjectName("Holidays_History")
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setItem(0, 2, item)
        item = QtWidgets.QTableWidgetItem()
        self.Holidays_History.setItem(0, 3, item)
        self.label = QtWidgets.QLabel(self.main)
        self.label.setGeometry(QtCore.QRect(110, 330, 71, 20))
        self.label.setText("")
        self.label.setObjectName("label")
        self.print_1 = QtWidgets.QPushButton(self.main)
        self.print_1.setGeometry(QtCore.QRect(240, 470, 141, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.print_1.setFont(font)
        self.print_1.setObjectName("print_1")
        self.print_1.clicked.connect(
            lambda: self.run_holiday_history_dialog(
                str(self.Military_Code.text()),
                self.get_name_by_military_number(str(self.Military_Code.text())),
            )
        )
        self.edit_1 = QtWidgets.QPushButton(self.main)
        self.edit_1.setGeometry(QtCore.QRect(240, 540, 141, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.edit_1.setFont(font)
        self.edit_1.setObjectName("edit_1")
        self.edit_1.clicked.connect(
            lambda: self.open_edit_History(self.Military_Code.text())
        )
        self.alert_section = QtWidgets.QTableWidget(self.main)
        self.alert_section.setGeometry(QtCore.QRect(640, 450, 421, 161))
        self.alert_section.setObjectName("alert_section")
        self.alert_section.setColumnCount(2)
        self.alert_section.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.alert_section.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.alert_section.setHorizontalHeaderItem(1, item)
        self.alert_section.horizontalHeader().setDefaultSectionSize(210)
        self.tabWidget.addTab(self.main, "")
        self.add_agent = QtWidgets.QWidget()
        self.add_agent.setObjectName("add_agent")
        self.Military_Number = QtWidgets.QLabel(self.add_agent)
        self.Military_Number.setGeometry(QtCore.QRect(950, 90, 111, 20))
        self.Military_Number.setStyleSheet(" font-size: 15px;")
        self.Military_Number.setObjectName("Military_Number")
        self.Mobile_Number = QtWidgets.QLabel(self.add_agent)
        self.Mobile_Number.setGeometry(QtCore.QRect(950, 140, 81, 31))
        self.Mobile_Number.setStyleSheet(" font-size: 15px;")
        self.Mobile_Number.setObjectName("Mobile_Number")
        self.General_Number = QtWidgets.QLabel(self.add_agent)
        self.General_Number.setGeometry(QtCore.QRect(960, 60, 71, 16))
        self.General_Number.setStyleSheet(" font-size: 15px;")
        self.General_Number.setObjectName("General_Number")
        self.Military_Rank = QtWidgets.QLabel(self.add_agent)
        self.Military_Rank.setGeometry(QtCore.QRect(960, 240, 47, 21))
        self.Military_Rank.setStyleSheet(" font-size: 15px;")
        self.Military_Rank.setObjectName("Military_Rank")
        self.Governorate = QtWidgets.QLabel(self.add_agent)
        self.Governorate.setGeometry(QtCore.QRect(910, 210, 101, 21))
        self.Governorate.setStyleSheet(" font-size: 15px;")
        self.Governorate.setObjectName("Governorate")
        self.Civil_Registry = QtWidgets.QLabel(self.add_agent)
        self.Civil_Registry.setGeometry(QtCore.QRect(950, 120, 111, 20))
        self.Civil_Registry.setStyleSheet(" font-size: 15px;")
        self.Civil_Registry.setObjectName("Civil_Registry")
        self.The_Group = QtWidgets.QLabel(self.add_agent)
        self.The_Group.setGeometry(QtCore.QRect(930, 170, 101, 31))
        self.The_Group.setStyleSheet(" font-size: 15px;")
        self.The_Group.setObjectName("The_Group")
        self.Name = QtWidgets.QLabel(self.add_agent)
        self.Name.setGeometry(QtCore.QRect(960, 30, 48, 18))
        self.Name.setStyleSheet(" font-size: 15px;")
        self.Name.setObjectName("Name")
        self.Name_input = QtWidgets.QLineEdit(self.add_agent)
        self.Name_input.setGeometry(QtCore.QRect(740, 30, 211, 21))
        self.Name_input.setText("")
        self.Name_input.setObjectName("Name_input")
        self.General_number_input = QtWidgets.QLineEdit(self.add_agent)
        self.General_number_input.setGeometry(QtCore.QRect(740, 60, 211, 21))
        self.General_number_input.setText("")
        self.General_number_input.setObjectName("General_number_input")
        self.Military_Number_input = QtWidgets.QLineEdit(self.add_agent)
        self.Military_Number_input.setGeometry(QtCore.QRect(740, 90, 211, 21))
        self.Military_Number_input.setText("")
        self.Military_Number_input.setObjectName("Military_Number_input")
        self.Civil_Registry_input = QtWidgets.QLineEdit(self.add_agent)
        self.Civil_Registry_input.setGeometry(QtCore.QRect(740, 120, 211, 21))
        self.Civil_Registry_input.setText("")
        self.Civil_Registry_input.setObjectName("Civil_Registry_input")
        self.Mobile_Number_input = QtWidgets.QLineEdit(self.add_agent)
        self.Mobile_Number_input.setGeometry(QtCore.QRect(740, 150, 211, 21))
        self.Mobile_Number_input.setText("")
        self.Mobile_Number_input.setObjectName("Mobile_Number_input")
        self.The_Group_input = QtWidgets.QLineEdit(self.add_agent)
        self.The_Group_input.setGeometry(QtCore.QRect(740, 180, 211, 21))
        self.The_Group_input.setText("")
        self.The_Group_input.setObjectName("The_Group_input")
        self.Governorate_input = QtWidgets.QLineEdit(self.add_agent)
        self.Governorate_input.setGeometry(QtCore.QRect(740, 210, 211, 21))
        self.Governorate_input.setText("")
        self.Governorate_input.setObjectName("Governorate_input")
        self.Military_Rank_input = QtWidgets.QLineEdit(self.add_agent)
        self.Military_Rank_input.setGeometry(QtCore.QRect(740, 240, 211, 21))
        self.Military_Rank_input.setText("")
        self.Military_Rank_input.setObjectName("Military_Rank_input")
        self.Add_Agent_btn = QtWidgets.QPushButton(self.add_agent)
        self.Add_Agent_btn.setGeometry(QtCore.QRect(800, 280, 101, 31))
        self.Add_Agent_btn.setStyleSheet(" font-size: 15px;")
        self.Add_Agent_btn.setObjectName("Add_Agent_btn")
        self.Add_Agent_btn.clicked.connect(
            lambda: self.save_agent_data(
                str(self.Military_Number_input.text()),
                str(self.Name_input.text()),
                str(self.General_number_input.text()),
                str(self.Military_Rank_input.text()),
                str(self.Governorate_input.text()),
                str(self.Mobile_Number_input.text()),
                str(self.Civil_Registry_input.text()),
                str(self.The_Group_input.text()),
            )
        )
        self.agents_section = QtWidgets.QTableWidget(self.add_agent)
        self.agents_section.setGeometry(QtCore.QRect(15, 30, 701, 591))
        self.agents_section.setObjectName("agents_section")
        self.agents_section.setColumnCount(9)
        self.agents_section.setRowCount(22)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(9, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(10, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(11, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(12, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(13, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(14, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(15, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(16, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(17, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(18, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(19, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(20, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setVerticalHeaderItem(21, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.agents_section.setHorizontalHeaderItem(8, item)
        self.edit_2 = QtWidgets.QPushButton(self.add_agent)
        self.edit_2.setGeometry(QtCore.QRect(760, 540, 141, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.edit_2.setFont(font)
        self.edit_2.setObjectName("edit_2")
        self.edit_2.clicked.connect(lambda: self.open_edit_Agent())

        font = QtGui.QFont()
        font.setPointSize(12)

        self.tabWidget.addTab(self.add_agent, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1142, 21))
        self.menubar.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.Add_User = QtWidgets.QAction(MainWindow)
        self.Add_User.setObjectName("Add_User")
        self.Add_User.triggered.connect(lambda: self.show_add_admin_dialog())
        self.menu.addAction(self.Add_User)
        self.menubar.addAction(self.menu.menuAction())
        self.change_admin = QtWidgets.QAction(MainWindow)
        self.change_admin.setObjectName("change_admin")
        self.change_admin.triggered.connect(lambda: self.change_admin_tr())
        self.menu.addAction(self.change_admin)
        self.menubar.addAction(self.menu.menuAction())
        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.Military_Code.setPlaceholderText(_translate("MainWindow", "الرقم العسكري"))
        self.Holiday_Start_input.setText(
            _translate("MainWindow", str((self.hijri_date())))
        )
        self.Agent_Data.setHtml(
            _translate(
                "MainWindow",
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
                '<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
                '<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;"><br /></p></body></html>',
            )
        )
        self.Search_Bycode.setText(_translate("MainWindow", "بحث"))
        self.Search_Bycode.setShortcut(_translate("MainWindow", "Return"))
        self.Started_Box.setText(_translate("MainWindow", "تم مباشره العمل "))
        self.Currnet_Holiday_label.setText(_translate("MainWindow", "الاجازة الحالية"))
        self.Current_Holiday_Kind.setText(_translate("MainWindow", "نوع الاجازة:"))
        self.Current_Holiday_Duration.setText(_translate("MainWindow", "مدة الاجازة:"))
        self.Current_Holiday_Start.setText(_translate("MainWindow", "تاريخ البداية:"))
        self.Current_Holiday_End.setText(_translate("MainWindow", "تاريخ العودة:"))
        self.Absence_Period.setText(_translate("MainWindow", "مدة التطويف :"))
        self.Remaining_Days.setText(_translate("MainWindow", "المتبقي:"))
        self.Add_Holiday_btn.setText(_translate("MainWindow", "اضافة اجازة"))
        self.Holiday_Duration.setText(_translate("MainWindow", "مدة الاجازة :"))
        self.Holiday_Start.setText(_translate("MainWindow", "تاريخ البداية :"))
        self.Holiday_End.setText(_translate("MainWindow", "تاريخ العودة :"))
        self.comboBox.setItemText(0, _translate("MainWindow", "اعتيادية"))
        self.comboBox.setItemText(1, _translate("MainWindow", "عرضية"))
        self.Holiday_Kind.setText(_translate("MainWindow", "نوع الاجازة :"))
        item = self.Holidays_History.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "الرقم العسكرى"))
        item = self.Holidays_History.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "نوع الاجازة"))
        item = self.Holidays_History.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "مدة الاجازة"))
        item = self.Holidays_History.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "تاربخ البداية"))
        item = self.Holidays_History.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "تاربخ النهابة"))
        item = self.Holidays_History.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "مدة التطويف"))
        item = self.Holidays_History.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "اسم المستخدم"))
        # item = self.Holidays_History.horizontalHeaderItem(7)
        # item.setText(_translate("MainWindow", "تاريخ العودة"))
        __sortingEnabled = self.Holidays_History.isSortingEnabled()
        self.Holidays_History.setSortingEnabled(False)
        self.Holidays_History.setSortingEnabled(__sortingEnabled)
        self.print_1.setText(_translate("MainWindow", "طباعة"))
        self.print_1.setShortcut(_translate("MainWindow", "F1"))
        self.edit_1.setText(_translate("MainWindow", "تعديل"))
        self.edit_1.setShortcut(_translate("MainWindow", "F2"))
        item = self.alert_section.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "الرقم الخاص"))
        item = self.alert_section.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "مدة التطويف"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.main), _translate("MainWindow", "الرئيسية")
        )
        self.Military_Number.setText(_translate("MainWindow", "الرقم العسكري :"))
        self.Mobile_Number.setText(_translate("MainWindow", "رقم الجوال :"))
        self.General_Number.setText(_translate("MainWindow", "الرقم العام : "))
        self.Military_Rank.setText(_translate("MainWindow", "الرتبة :"))
        self.Governorate.setText(_translate("MainWindow", "الملاك :"))
        self.Civil_Registry.setText(_translate("MainWindow", "السجل المدني :"))
        self.The_Group.setText(_translate("MainWindow", "المجموعة :"))
        self.Name.setText(_translate("MainWindow", "الاسم :"))
        self.Add_Agent_btn.setText(_translate("MainWindow", "اضافة فرد"))
        item = self.agents_section.verticalHeaderItem(0)
        item.setText(_translate("MainWindow", "1"))
        item = self.agents_section.verticalHeaderItem(1)
        item.setText(_translate("MainWindow", "2"))
        item = self.agents_section.verticalHeaderItem(2)
        item.setText(_translate("MainWindow", "4"))
        item = self.agents_section.verticalHeaderItem(3)
        item.setText(_translate("MainWindow", "5"))
        item = self.agents_section.verticalHeaderItem(4)
        item.setText(_translate("MainWindow", "6"))
        item = self.agents_section.verticalHeaderItem(5)
        item.setText(_translate("MainWindow", "7"))
        item = self.agents_section.verticalHeaderItem(6)
        item.setText(_translate("MainWindow", "8"))
        item = self.agents_section.verticalHeaderItem(7)
        item.setText(_translate("MainWindow", "9"))
        item = self.agents_section.verticalHeaderItem(8)
        item.setText(_translate("MainWindow", "10"))
        item = self.agents_section.verticalHeaderItem(9)
        item.setText(_translate("MainWindow", "11"))
        item = self.agents_section.verticalHeaderItem(10)
        item.setText(_translate("MainWindow", "12"))
        item = self.agents_section.verticalHeaderItem(11)
        item.setText(_translate("MainWindow", "13"))
        item = self.agents_section.verticalHeaderItem(12)
        item.setText(_translate("MainWindow", "14"))
        item = self.agents_section.verticalHeaderItem(13)
        item.setText(_translate("MainWindow", "15"))
        item = self.agents_section.verticalHeaderItem(14)
        item.setText(_translate("MainWindow", "16"))
        item = self.agents_section.verticalHeaderItem(15)
        item.setText(_translate("MainWindow", "17"))
        item = self.agents_section.verticalHeaderItem(16)
        item.setText(_translate("MainWindow", "18"))
        item = self.agents_section.verticalHeaderItem(17)
        item.setText(_translate("MainWindow", "19"))
        item = self.agents_section.verticalHeaderItem(18)
        item.setText(_translate("MainWindow", "20"))
        item = self.agents_section.verticalHeaderItem(19)
        item.setText(_translate("MainWindow", "21"))
        item = self.agents_section.verticalHeaderItem(20)
        item.setText(_translate("MainWindow", "22"))
        item = self.agents_section.verticalHeaderItem(21)
        item.setText(_translate("MainWindow", "23"))
        item = self.agents_section.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "الاسم "))
        item = self.agents_section.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "الرتية"))
        item = self.agents_section.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "الرقم الخاص"))
        item = self.agents_section.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "الرقم العام"))
        item = self.agents_section.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "السجل"))
        item = self.agents_section.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "الجوال"))
        item = self.agents_section.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "المجموعة"))
        item = self.agents_section.horizontalHeaderItem(7)
        item.setText(_translate("MainWindow", "الملاك"))
        item = self.agents_section.horizontalHeaderItem(8)
        item.setText(_translate("MainWindow", "المتبقي من الرصيد"))
        self.edit_2.setText(_translate("MainWindow", "تعديل"))
        self.edit_2.setShortcut(_translate("MainWindow", "F2"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.add_agent),
            _translate("MainWindow", "ادارة الافراد"),
        )
        self.menu.setTitle(_translate("MainWindow", "مدير الوحدة"))
        self.Add_User.setText(_translate("MainWindow", "اضافه مستخدم"))
        self.change_admin.setText(_translate("MainWindow", "تغير الادمن و الكود"))