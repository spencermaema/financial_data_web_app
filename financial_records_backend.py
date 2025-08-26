from flask import Flask, request, jsonify
from flask_cors import CORS 
from decimal import Decimal # to cast numpy.int64 to Decimal format used in database
import mysql.connector
from mysql.connector import Error
import pandas as pd

app = Flask(__name__)
CORS(app) #Allows requests from a different origin
DB_CONFIG ={
'host': 'localhost',
'database': 'financial_db',
'username': 'moahloli',
'password': 'r@ndom_p@$wd'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Create the users and financials tables"""
    connection = get_db_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        # Create users table
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
        """
        cursor.execute(users_table)
        
        # Create financials table
        financials_table = """
        CREATE TABLE IF NOT EXISTS financial_records (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            year INT NOT NULL,
            month INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
        cursor.execute(financials_table)
        
        # Commit the changes
        connection.commit()
        print("Tables created successfully!")
        return True
        
    except Error as e:
        print(f"Error creating tables: {e}")
        return False
    
    finally:
        cursor.close()
        connection.close()

def insert_sample_data():
    """Insert some sample data"""
    connection = get_db_connection()
    if connection is None:
        return
    
    cursor = connection.cursor()
    
    try:
        # Insert sample users
        users_data = [
            ("Alice",),
            ("Bob",),
            ("Charlie",)
        ]
        cursor.executemany("INSERT INTO users (name) VALUES (%s)", users_data)
        
        # Insert sample financial records
        financials_data = [
            (1, 2024, 1, 2500.00),
            (1, 2024, 2, 2600.00),
            (2, 2024, 1, 3200.00),
            (2, 2024, 2, 3150.00),
            (3, 2024, 1, 1800.00)
        ]
        cursor.executemany(
            "INSERT INTO financial_records (user_id, year, month, amount) VALUES (%s, %s, %s, %s)",
            financials_data
        )
        
        connection.commit()
        print("Sample data inserted successfully!")
        
    except Error as e:
        print(f"Error inserting sample data: {e}")
    
    finally:
        cursor.close()
        connection.close()

@app.route('/api/finances/upload/<int:userId>/<int:year>', methods=['POST'])    
def upload_finances(userId, year):
    # Get the uploaded file from multipart/form-data
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    # Parse Excel file
    data = pd.read_excel(file)
    
    # Connect to database
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # Insert each row into financial_records
    for _, row in data.iterrows():
        cursor.execute(
            "INSERT INTO financial_records (user_id, year, month, amount) VALUES (%s, %s, %s, %s)",
            (userId, year, int(row['Month']), Decimal(str(row['Amount']))) # Casting month back to int and amount back to Decimal because pandas renders them as numpy.int64, which is incompatible with the database (double casting amount because direct casting to Decimal not supported).
        )
    
    # Save changes
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'message': 'Financial data uploaded successfully'}), 200

@app.route('/api/finances/<int:userId>/<int:year>', methods=['GET'])
def get_finances(userId, year):
    # Connect to database
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # Fetch financial records for the user and year
    cursor.execute(
        "SELECT month, amount FROM financial_records WHERE user_id = %s AND year = %s",
        (userId, year)
    )
    
    records = cursor.fetchall()
    cursor.close()
    connection.close()
    
    # Return records in JSON format
    result = []
    for record in records:
        result.append({
            'month': record[0],
            'amount': record[1]
        })
    
    return jsonify(result), 200

if __name__ == '__main__':
    # Initialize the database and insert sample data when the app starts
    create_tables()
    insert_sample_data()
    #Run the app
    app.run(debug=True)
