from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
from config import Config

app = Flask(__name__)
CORS(app)

# Fungsi untuk menghitung skor prioritas
def calculate_priority_score(book, loans):
    recent_loans = 0
    cutoff_date = datetime.now() - timedelta(days=30)

    for loan in loans:
        # Coba parse tanggal dalam berbagai format
        try:
            # Format dari database biasanya YYYY-MM-DD
            loan_date_str = loan['loan_date']
            if 'T' in loan_date_str:
                loan_date_str = loan_date_str.split('T')[0]
            elif 'GMT' in loan_date_str:
                # Jika format seperti "Tue, 22 Apr 2025 00:00:00 GMT"
                loan_date_str = ' '.join(loan_date_str.split()[1:4])  # Ambil "22 Apr 2025"
            
            # Parse tanggal
            loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d')
        except ValueError:
            try:
                loan_date = datetime.strptime(loan_date_str, '%d %b %Y')
            except ValueError:
                continue  # Skip jika format tidak dikenali

        if loan_date >= cutoff_date:
            recent_loans += 1

    # Hitung persentase stok tersedia
    stock_percentage = (book['available_copies'] / book['total_copies']) * 100 if book['total_copies'] > 0 else 0

    # Skor prioritas
    priority_score = recent_loans * 10  # 10 poin per peminjaman
    if stock_percentage < 30:
        priority_score += 50
    elif stock_percentage < 50:
        priority_score += 20

    return priority_score

@app.route('/priority-books', methods=['GET'])
def get_priority_books():
    try:
        book_response = requests.get('http://localhost:5000/books')
        if book_response.status_code != 200:
            return jsonify({"error": "Failed to fetch books"}), 500
        books = book_response.json()

        loan_response = requests.get('http://localhost:5001/loans')
        if loan_response.status_code != 200:
            return jsonify({"error": "Failed to fetch loans"}), 500
        all_loans = loan_response.json()

        priority_books = []
        for book in books:
            book_loans = [loan for loan in all_loans if loan['book_id'] == book['id']]
            score = calculate_priority_score(book, book_loans)
            
            # Tampilkan buku jika ada setidaknya 2 peminjaman atau stok rendah
            if score >= 20 or book['available_copies'] <= 1:  # Ubah ambang batas
                priority_books.append({
                    "id": book['id'],
                    "title": book['title'],
                    "author": book['author'],
                    "available_copies": book['available_copies'],
                    "total_copies": book['total_copies'],
                    "priority_score": score,
                    "message": "High demand book" if score >= 50 else "Monitor stock"
                })

        priority_books.sort(key=lambda x: x['priority_score'], reverse=True)
        return jsonify(priority_books), 200
    except Exception as e:
        app.logger.error(f"Error calculating priority books: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.AI_SERVICE_PORT)