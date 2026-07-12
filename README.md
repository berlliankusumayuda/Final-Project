# Simple LMS – Extended Backend

> **Mata Kuliah**: Pemrograman Sisi Server (A11.4602)  
> **Program Studi**: Teknik Informatika – Universitas Dian Nuswantoro  
> **Pengajar**: Fahri Firdausillah, S.Kom, M.CS

## 📌 Fitur Tambahan: Paket 3 – Assessment & Certificate (60 Poin)

| Fitur | Poin |
|---|---|
| Quiz dan question bank | 15 |
| Submit quiz dan scoring otomatis | 15 |
| Attempt limit, passing grade, riwayat | 15 |
| Certificate generation | 15 |
| **Total** | **60 (dihitung maks 50)** |

---

## 🚀 Cara Menjalankan

### Prasyarat
- Docker & Docker Compose terinstall

### Langkah

```bash
# 1. Clone repository
git clone <repo-url>
cd simple_lms

# 2. Salin file environment
cp .env.example .env

# 3. Jalankan dengan Docker Compose
docker compose up --build

# 4. Akses Swagger UI
open http://localhost:8000/api/v1/docs
```

> Data demo otomatis di-seed saat container pertama kali dijalankan.

---

## 👤 Akun Demo

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Instructor | `instructor1` | `Instructor@1234` |
| Student | `student1` | `Student@1234` |
| Student | `student2` | `Student@1234` |

---

## 📋 Endpoint Utama

### 🔐 Authentication
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/api/v1/auth/register` | Daftar akun baru |
| POST | `/api/v1/auth/login` | Login, dapat JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Profil saat ini |

### 📚 Courses
| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/v1/courses` | Daftar course (publik) |
| POST | `/api/v1/courses` | Buat course (instructor/admin) |
| POST | `/api/v1/courses/{id}/enroll` | Daftar kursus (student) |
| GET | `/api/v1/courses/enrollments/my` | Daftar enrollments saya |
| POST | `/api/v1/courses/{id}/progress` | Update progress lesson |

### 📝 Assessments (Paket 3)
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/api/v1/assessments/courses/{id}/quizzes` | Buat quiz (instructor) |
| GET | `/api/v1/assessments/courses/{id}/quizzes` | Daftar quiz |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}` | Detail quiz (soal tanpa jawaban) |
| POST | `/api/v1/assessments/courses/{id}/quizzes/{qid}/questions` | Tambah soal |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}/questions` | Daftar soal+jawaban (instructor) |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}/status` | Status attempt saya |
| POST | `/api/v1/assessments/courses/{id}/quizzes/{qid}/submit` | Submit quiz & auto-scoring |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}/attempts` | Riwayat attempt saya |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}/attempts/{aid}` | Detail attempt |
| GET | `/api/v1/assessments/courses/{id}/quizzes/{qid}/all-attempts` | Semua attempt (instructor) |

### 🎓 Certificates
| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/v1/certificates/my` | Sertifikat saya |
| POST | `/api/v1/certificates/generate/{course_id}` | Minta sertifikat (course harus selesai) |
| GET | `/api/v1/certificates/verify/{code}` | Verifikasi sertifikat (publik) |
| GET | `/api/v1/certificates/admin/all` | Semua sertifikat (admin) |

---

## 🧪 Menjalankan Test

```bash
# Dari dalam container
docker compose exec web python manage.py test tests --verbosity=2

# Atau langsung
docker compose run --rm web python manage.py test tests
```

---

## 🏗 Arsitektur Project

```
simple_lms/
├── apps/
│   ├── users/          # Auth, Role, User model
│   ├── courses/        # Category, Course, Section, Lesson, Enrollment, Progress
│   ├── assessments/    # Quiz, Question, Choice, QuizAttempt, AttemptAnswer
│   └── certificates/   # Certificate + PDF generation
├── config/             # Django settings, URLs
├── tests/              # Unit & API tests
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## 🔑 Cara Test di Swagger

1. Buka http://localhost:8000/api/v1/docs
2. POST `/api/v1/auth/login` dengan `student1 / Student@1234`
3. Copy `access` token → klik **Authorize** → paste `<token>`
4. Gunakan endpoint yang diinginkan

---

## 📸 Swagger UI
Tersedia di: `http://localhost:8000/api/v1/docs`

## 🗄 Django Admin
Tersedia di: `http://localhost:8000/admin/` (login: `admin / Admin@1234`)
