import pandas as pd
import sqlite3
from PyQt5.QtWidgets import QApplication, QFileDialog

def browse_file(file_type="Excel"):
    # Create an instance of QApplication
    app = QApplication([])

    # Set the file dialog title and filter based on file type
    if file_type == "Excel":
        dialog_title = "Select Excel File"
        file_filter = "Excel Files (*.xlsx *.xls)"
    elif file_type == "Database":
        dialog_title = "Select SQLite Database"
        file_filter = "SQLite Database Files (*.db)"

    # Open a file dialog to select the file
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(
        None, 
        dialog_title, 
        "", 
        file_filter
    )
    
    # Exit the QApplication
    app.exit()
    
    return file_path

def insert_data_to_db(excel_file_path, db_path):
    # Define the correct column mappings
    column_mapping = {
        'الأســـــــــــــــــــــــــــــــــــم': 'name',
        'الرتبة': 'military_rank',
        'الرقم الخاص': 'military_number',
        'الرقم العام': 'general_number',
        'رقم السجل': 'civil_registry',
        'رقم الجوال': 'mobile_number',
        'الملاك': 'governorate'  # Corrected mapping
    }
    
    # Load the Excel file
    df = pd.read_excel(excel_file_path)

    # Strip any leading or trailing spaces from column names
    df.columns = df.columns.str.strip()

    # Rename the DataFrame columns to match the database columns
    df = df.rename(columns=column_mapping)
    
    # Set default values for columns not present in the Excel file
    df['the_remaining_holidays'] = 60
    df['user_code'] = "0000"  # Set user_code to 0000
    df['the_group'] = "غير معرف"  # Set the_group to "غير معرف"

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert or update data into the database
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO users (name, military_rank, military_number, general_number, civil_registry,
                                   mobile_number, governorate, the_remaining_holidays, user_code, the_group)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['name'], row['military_rank'], row['military_number'], row['general_number'],
                row['civil_registry'], row['mobile_number'], row['governorate'],
                row['the_remaining_holidays'], row['user_code'], row['the_group']
            ))
        except sqlite3.IntegrityError:
            # If a UNIQUE constraint error occurs, update the existing record
            cursor.execute('''
                UPDATE users
                SET name = ?, military_rank = ?, general_number = ?, civil_registry = ?,
                    mobile_number = ?, governorate = ?, the_remaining_holidays = ?, user_code = ?, the_group = ?
                WHERE military_number = ?
            ''', (
                row['name'], row['military_rank'], row['general_number'], row['civil_registry'],
                row['mobile_number'], row['governorate'], row['the_remaining_holidays'], row['user_code'],
                row['the_group'], row['military_number']
            ))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Data inserted/updated successfully.")

# Example usage:
if __name__ == "__main__":
    excel_file_path = browse_file(file_type="Excel")
    if excel_file_path:
        db_file_path = browse_file(file_type="Database")
        if db_file_path:
            insert_data_to_db(excel_file_path, db_file_path)
