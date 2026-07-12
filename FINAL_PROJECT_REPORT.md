# FINAL PROJECT REPORT
## Simple LMS Extended Backend – Paket 3: Assessment & Certificate

---

## Identitas
| | |
|---|---|
| **Nama** | *(Berlian Kusumayuda)* |
| **NIM** | *(A11.2023.15247)* |
| **Kelas** | A11.4602 – Pemrograman Sisi Server |
| **URL Repository** | *(https://github.com/berlliankusumayuda/Final-Project.git)* |

---

## Deskripsi Project

Simple LMS Extended Backend adalah sistem backend Learning Management System yang dibangun menggunakan Django + Django Ninja (REST API) dengan PostgreSQL sebagai database. Project ini merupakan kelanjutan dari tugas capstone dengan penambahan fitur **Assessment & Certificate** (Paket 3).

Sistem mendukung tiga role: **Admin**, **Instructor**, dan **Student**, masing-masing dengan hak akses yang berbeda-beda.

---

## Fitur Dasar yang Sudah Berjalan

- ✅ **Authentication JWT** – Register, Login, Refresh token, profil user
- ✅ **Role-based Access Control** – Admin, Instructor, Student
- ✅ **Course API** – CRUD course dengan filter, search, publish workflow
- ✅ **Section & Lesson** – Struktur kurikulum bertingkat
- ✅ **Enrollment** – Student enroll ke course
- ✅ **Progress** – Tracking progress per lesson, auto-complete enrollment
- ✅ **Category** – Kategorisasi course
- ✅ **Docker & Docker Compose** – Seluruh service berjalan via Docker
- ✅ **PostgreSQL** – Database utama dengan migration
- ✅ **Swagger/OpenAPI** – Dokumentasi API di `/api/v1/docs`
- ✅ **Django Admin** – Panel admin di `/admin/`
- ✅ **Seed Demo Data** – Command `seed_demo` untuk data awal

---

## Fitur Tambahan yang Dipilih (Paket 3 – Assessment & Certificate)

| No | Fitur | Kategori | Poin | Status |
|---|---|---|---|---|
| 1 | Quiz dan question bank | B. Assessment | 15 | ✅ Selesai |
| 2 | Submit quiz dan scoring otomatis | B. Assessment | 15 | ✅ Selesai |
| 3 | Attempt limit, passing grade, riwayat | B. Assessment | 15 | ✅ Selesai |
| 4 | Certificate generation | B. Assessment | 15 | ✅ Selesai |
| **Total** | | | **60 (maks 50)** | |

---

## Penjelasan Implementasi

### 1. Quiz dan Question Bank (15 poin)
Model `Quiz` terhubung ke `Course` (dan opsional ke `Lesson`). Setiap quiz punya pengaturan:
- `passing_grade` – skor minimum untuk lulus (%)
- `attempt_limit` – batas percobaan (0 = tidak terbatas)
- `time_limit_minutes` – batas waktu (0 = tidak ada batas)
- `randomize_questions` / `randomize_choices` – acak soal dan pilihan

Model `Question` mendukung soal pilihan ganda dengan bobot poin masing-masing (`points`). Setiap soal punya field `explanation` yang ditampilkan setelah jawaban dikumpulkan.

Model `Choice` menyimpan pilihan jawaban dengan flag `is_correct`.

Endpoint instructor:
- `POST /quizzes` – buat quiz
- `POST /quizzes/{id}/questions` – tambah soal beserta pilihan sekaligus
- `GET /quizzes/{id}/questions` – lihat soal+jawaban (hanya instructor/admin)

### 2. Submit Quiz & Scoring Otomatis (15 poin)
Endpoint `POST /quizzes/{id}/submit` menerima array `answers` berisi `question_id` dan `choice_id`.

Sistem melakukan:
1. Validasi enrollment dan attempt limit
2. Cocokkan pilihan dengan jawaban benar di database
3. Hitung poin per soal dan total skor (persentase)
4. Simpan `QuizAttempt` dengan status `graded` dan hasil skor
5. Simpan `AttemptAnswer` per soal dengan flag `is_correct` dan `points_earned`
6. Return detail hasil beserta jawaban benar dan penjelasan (explanation)

Soal yang tidak dijawab dihitung 0 poin secara otomatis.

### 3. Attempt Limit, Passing Grade, Riwayat (15 poin)
- `attempt_limit` dicek sebelum submit – jika sudah mencapai batas, return 400
- Jika sudah pernah lulus (passed=True), tidak bisa mencoba lagi
- Endpoint `GET /quizzes/{id}/status` menampilkan: attempts_used, attempts_allowed, best_score, can_attempt, passed
- Endpoint `GET /quizzes/{id}/attempts` menampilkan riwayat semua attempt student
- Endpoint `GET /quizzes/{id}/attempts/{aid}` menampilkan detail attempt lengkap dengan jawaban

### 4. Certificate Generation (15 poin)
Sertifikat otomatis dibuat ketika:
- Student berhasil melewati quiz (passed=True) **DAN**
- Enrollment student pada course sudah berstatus `completed`

Sertifikat dapat juga diminta manual melalui `POST /certificates/generate/{course_id}` selama course sudah selesai.

Sistem menghasilkan file PDF (menggunakan WeasyPrint) atau HTML fallback dengan desain sertifikat formal:
- Nama student dan course
- Nama instructor
- Tanggal issued
- Kode unik (UUID) untuk verifikasi

Endpoint verifikasi publik `GET /certificates/verify/{code}` dapat diakses tanpa autentikasi untuk membuktikan keaslian sertifikat.

---

## Cara Menjalankan Project

```bash
git clone <repo-url>
cd simple_lms
cp .env.example .env
docker compose up --build
```

Akses:
- **Swagger**: http://localhost:8000/api/v1/docs
- **Admin**: http://localhost:8000/admin/

---

## Akun Demo

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@1234 |
| Instructor | instructor1 | Instructor@1234 |
| Student | student1 | Student@1234 |
| Student | student2 | Student@1234 |

---

## Endpoint Penting untuk Diuji

### Flow Assessment
1. Login sebagai `instructor1` → dapatkan token
2. `GET /api/v1/courses` → catat course_id (misal: 1)
3. `POST /api/v1/assessments/courses/1/quizzes` → buat quiz
4. `POST /api/v1/assessments/courses/1/quizzes/1/questions` → tambah soal
5. Login sebagai `student1` → dapatkan token
6. `POST /api/v1/courses/1/enroll` → enroll
7. `GET /api/v1/assessments/courses/1/quizzes/1` → lihat soal (tanpa jawaban)
8. `GET /api/v1/assessments/courses/1/quizzes/1/status` → cek attempt
9. `POST /api/v1/assessments/courses/1/quizzes/1/submit` → kumpulkan jawaban
10. `GET /api/v1/assessments/courses/1/quizzes/1/attempts` → riwayat attempt

### Flow Certificate
1. Login sebagai `student1`
2. `POST /api/v1/courses/1/progress` → tandai semua lesson selesai (agar enrollment completed)
3. `POST /api/v1/certificates/generate/1` → minta sertifikat
4. `GET /api/v1/certificates/my` → lihat sertifikat
5. `GET /api/v1/certificates/verify/{unique_code}` → verifikasi (tanpa login)

---

## Screenshot / Bukti Pengujian

*(Tambahkan screenshot Swagger, Postman, atau output test di sini)*

Test dijalankan dengan:
```bash
docker compose run --rm web python manage.py test tests --verbosity=2
```

---

## Kendala dan Solusi

| Kendala | Solusi |
|---|---|
| WeasyPrint membutuhkan library sistem (cairo, pango) | Menambahkan apt-get install di Dockerfile; menambahkan fallback HTML jika WeasyPrint gagal |
| Quiz yang sudah dilewati tidak boleh dicoba lagi | Menambahkan pengecekan `passed=True` sebelum submit baru |
| Certificate hanya dibuat setelah enrollment selesai | Fungsi `_maybe_generate_certificate` mengecek status enrollment sebelum generate |

---

## Kesimpulan

Final project ini berhasil mengimplementasikan seluruh komponen wajib LMS serta fitur tambahan Paket 3 (Assessment & Certificate). Sistem sudah:
- Dapat dijalankan dengan satu perintah `docker compose up --build`
- Memiliki API yang terdokumentasi di Swagger
- Memiliki sistem quiz dengan soal pilihan ganda, scoring otomatis, batas attempt, dan passing grade
- Menghasilkan sertifikat dengan kode unik yang dapat diverifikasi secara publik
- Dilengkapi 25+ test case yang mencakup auth, RBAC, quiz, dan certificate

Pengerjaan project ini memberikan pengalaman nyata dalam membangun backend yang modular, aman, dan terdokumentasi dengan baik.
