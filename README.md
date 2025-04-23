# Documentation BukuKu

## 🔧 Instalasi & Menjalankan

1. **Install dependensi:**
```bash
pip install flask flask-cors mysql-connector-python python-dotenv
```

2. **Buat file `.env`** dan isi dengan konfigurasi database:
```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD= 
MYSQL_PORT=3308

BOOK_SERVICE_PORT=5000
LOAN_SERVICE_PORT=5001
USER_SERVICE_PORT=5002
AI_SERVICE_PORT=5003

MYSQL_DB_BOOK=book_management_uts_db 
MYSQL_DB_LOAN=loan_management_uts_db 
MYSQL_DB_USER=user_management_uts_db

URL=http://localhost
```

3. **Jalankan service (masing-masing beda terminal):**
```bash
python -m http.server 8000
py book_service.py
py user_service.py
py loan_service.py
py ai_service.py
```

# API Documentation

---

# 📖 BookService API Documentation
BookService adalah bagian dari sistem manajemen perpustakaan yang menangani operasi terkait buku. API ini dibangun menggunakan Flask dan terhubung dengan MySQL.

---

Default port: `5000`

---

## 📂 Daftar Endpoint

### `GET /books`
Ambil semua data buku.
- **Response 200**: 
```json
[
  {
    "id": 1,
    "title": "Example Book",
    "author": "John Doe",
    "isbn": "1234567890",
    "total_copies": 5,
    "available_copies": 2,
    "cover_url": "http://example.com/cover.jpg"
  },
  {
    "id": 2,
    "title": "Example Book 2",
    "author": "Mary Jane",
    "isbn": "3344556677",
    "total_copies": 5,
    "available_copies": 2,
    "cover_url": "http://example.com/cover.jpg"
  },
]
```
- **Response 500**: `{ "error": "Error message" }`

---

### `GET /books/<book_id>`
Ambil data buku berdasarkan ID.
- **Response 200**:
```json
{
  "id": 1,
  "title": "Example Book",
  "author": "John Doe",
  "isbn": "1234567890",
  "total_copies": 5,
  "available_copies": 2,
  "cover_url": "http://example.com/cover.jpg"
}
```
- **Response 404**: `{ "error": "Book not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `POST /books`
Tambah buku baru.
- **Request Body JSON**:
```json
{
  "title": "New Book",
  "author": "Jane Smith",
  "isbn": "1122334455",
  "total_copies": 4,
  "available_copies": 4,
  "cover_url": "http://example.com/cover.jpg"
}
```
- **Response 201**: `{ "message": "Book created successfully", "book_id": 1 }`
- **Response 500**: `{ "error": "Error message" }`

---

### `PUT /books/<book_id>`
Update data lengkap buku berdasarkan ID.
- **Request Body JSON**:
```json
{
  "title": "Updated Book",
  "author": "Jane Smith",
  "isbn": "1122334455",
  "total_copies": 4,
  "available_copies": 3,
  "cover_url": "http://example.com/cover.jpg"
}
```
- **Response 200**: `{ "message": "Book updated successfully" }`
- **Response 404**: `{ "error": "Book not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `PUT /books/<book_id>/availability`
Update jumlah `available_copies` buku secara dinamis (tambah/kurang 1).
- **Request Body JSON**:
```json
{
  "increment": true
}
```
- `increment: true` → tambah 1
- `increment: false` → kurangi 1

- **Response 200**:
```json
{
  "message": "Book availability updated",
  "available_copies": 3
}
```
- **Response 400**: Validasi stok (misalnya habis atau sudah penuh)
- **Response 404**: `{ "error": "Book not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `DELETE /books/<book_id>`
Hapus buku berdasarkan ID.
- **Response 200**: `{ "message": "Book deleted successfully" }`
- **Response 404**: `{ "error": "Book not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `GET /books/search?q=keyword`
Cari buku berdasarkan `title` atau `author`.
- **Query Param**: `q` (kata kunci pencarian)
- **Response 200**: Array hasil pencarian
- **Response 400**: `{ "error": "Query parameter 'q' is required" }`
- **Response 500**: `{ "error": "Error message" }`

---

# 📖 UserService API Documentation

UserService adalah bagian dari sistem manajemen perpustakaan yang menangani data pengguna dan integrasi dengan LoanService untuk menampilkan histori peminjaman.

---

Default port: `5002`

---

## 📂 Daftar Endpoint

### `GET /users`
Ambil semua user.
- **Response 200**:
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "loan_history": 2
  },
  {
    "id": 1,
    "name": "Mary Jane",
    "email": "jane@example.com",
    "loan_history": 3
  }
]
```
- **Response 500**: `{ "error": "Error message" }`

---

### `GET /users/<user_id>`
Ambil data user berdasarkan ID beserta jumlah pinjaman.
- **Response 200**:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "loan_history": 2
}
```
- **Response 404**: `{ "error": "User not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `POST /users`
Tambahkan user baru.
- **Request Body JSON**:
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```
- **Response 201**: `{ "message": "User created successfully", "user_id": 1 }`
- **Response 500**: `{ "error": "Error message" }`

---

### `PUT /users/<user_id>`
Update user berdasarkan ID.
- **Request Body JSON**:
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```
- **Response 200**: `{ "message": "User updated successfully" }`
- **Response 404**: `{ "error": "User not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `DELETE /users/<user_id>`
Hapus user berdasarkan ID.
- **Response 200**: `{ "message": "User deleted successfully" }`
- **Response 404**: `{ "error": "User not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

# 📖 LoanService API Documentation

LoanService adalah bagian dari sistem manajemen perpustakaan yang menangani data peminjaman buku dan berinteraksi dengan BookService untuk memperbarui ketersediaan buku.

---

Default port: `5001`

---

## 📂 Daftar Endpoint

### `GET /loans`
Ambil semua data peminjaman buku.
- **Response 200**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "book_id": 2,
    "loan_date": "2025-04-18",
    "return_date": "2025-05-01"
  }
]
```
- **Response 500**: `{ "error": "Error message" }`

---

### `GET /loans/<loan_id>`
Ambil data peminjaman berdasarkan ID pinjaman.
- **Response 200**:
```json
{
  "id": 1,
  "user_id": 1,
  "book_id": 2,
  "loan_date": "2025-04-18",
  "return_date": "2025-05-01"
}
```
- **Response 404**: `{ "error": "Loan not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `POST /loans`
Tambah peminjaman buku.
- **Request Body JSON**:
```json
{
  "user_id": 1,
  "book_id": 2,
  "loan_date": "2025-04-18",
  "return_date": "2025-05-01"
}
```
- **Response 201**: `{ "message": "Loan created successfully", "loan_id": 1 }`
- **Response 400**: `{ "error": "Book is not available for loan" }`
- **Response 404**: `{ "error": "Book not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `PUT /loans/<loan_id>`
Update data peminjaman berdasarkan ID.
- **Request Body JSON**:
```json
{
  "user_id": 1,
  "book_id": 2,
  "loan_date": "2025-04-18",
  "return_date": "2025-05-05"
}
```
- **Response 200**: `{ "message": "Loan updated successfully" }`
- **Response 404**: `{ "error": "Loan not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `DELETE /loans/<loan_id>`
Hapus data peminjaman buku berdasarkan ID.
- **Response 200**: `{ "message": "Loan deleted successfully" }`
- **Response 404**: `{ "error": "Loan not found" }`
- **Response 500**: `{ "error": "Error message" }`

---

### `GET /loans/user/<user_id>`
Ambil semua peminjaman berdasarkan ID user.
- **Response 200**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "book_id": 2,
    "loan_date": "2025-04-18",
    "return_date": "2025-05-01"
  }
]
```
- **Response 500**: `{ "error": "Error message" }`

---