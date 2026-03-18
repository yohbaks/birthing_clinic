# 🌸 BirthCare Clinic Management System

A complete Django-based management system for maternity and lying-in clinics. Built for the Philippines healthcare setting with PhilHealth support, DOH reporting exports, and Asia/Manila timezone.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install django pillow reportlab

# 2. Apply migrations
python manage.py migrate

# 3. Start the server
python manage.py runserver
```

Open **http://127.0.0.1:8000**

**Default credentials:** `admin` / `Admin2026!`

---

## 📦 Feature Overview

### 🏥 Clinical
| Module | Features |
|--------|----------|
| **Patients** | Registration with auto record numbers (PAT-YYYY-NNNN), risk classification (Low/Moderate/High), OB history (G/P/A), LMP→EDD auto-calculation, emergency contacts, soft deactivate/reactivate |
| **Prenatal Care** | Visit recording, BP/weight/FHR/fundal height/temp vitals, risk flagging, lab requests, ultrasound records, GA auto-calculation from LMP, follow-up scheduling, prenatal history per patient |
| **Appointments** | Scheduling, type classification, status tracking, queue management with call/done/skip controls, live auto-refresh display board |
| **Labor & Delivery** | Admission with attending midwife + doctor assignment, labor monitoring (partograph-style), delivery timing fields (labor start, full dilation, placenta delivery, EBL), complication tracking, referral logging |
| **Newborn Records** | Auto Baby ID (NB-YYYY-NNNN), APGAR scores, birth measurements, Vit K/eye prophylaxis/NBS interventions, immunization tracking, discharge recording |

### ⚙️ Operations
| Module | Features |
|--------|----------|
| **Inventory** | Item management with auto codes (ITEM-NNNNN), stock-in/out transactions, batch/expiry tracking, low-stock and near-expiry alerts, supplier management with purchase orders |
| **Billing** | Bill creation with line items and discount support, generate bill from delivery shortcut, edit unpaid bills, waive bills (indigent/PhilHealth), payment recording (Cash/GCash/PhilHealth/Bank Transfer), auto OR numbers, printable HTML receipts, PDF Statement of Account |

### 📊 Reports & Exports
- Dashboard with live delivery/financial stats and Chart.js visualizations
- Daily patient census
- Monthly delivery report (by type, complications, maternal/newborn outcomes)
- Monthly statistical report (DOH-style: patients, prenatal, delivery, newborns, collections)
- Newborn summary report (birth weight distribution, APGAR trends, intervention coverage, monthly chart)
- Daily collection report
- **CSV export** for: Patients, Deliveries, Newborns, Collections, Prenatal Visits — with date-range filters
- **PDF export** for: Patient Summary Card, Prenatal Visit Record, Delivery Certificate, Statement of Account, Newborn Record

### 🔒 Admin & Security
- **Role-Based Access Control** — enforced on every view with `@role_required` decorator
- **Complete audit trail** — signal-based auto-logging of all CREATE/UPDATE/DELETE on 15 clinical models, with before/after field diff viewer
- Staff management: add, edit, deactivate, reactivate
- Inactive patient management
- **Clinic Settings page** — configure clinic name, address, PhilHealth accreditation #, DOH license #, head physician, default billing rates; used in all PDF letterheads

---

## 🔑 Auto-Generated Record Numbers

| Record | Format | Example |
|--------|--------|---------|
| Patient | `PAT-YYYY-NNNN` | `PAT-2026-0001` |
| Newborn | `NB-YYYY-NNNN` | `NB-2026-0001` |
| Bill | `BILL-YYYY-NNNNN` | `BILL-2026-00001` |
| Receipt/OR | `OR-YYYY-NNNNN` | `OR-2026-00001` |
| Purchase Order | `PO-YYYY-NNNN` | `PO-2026-0001` |
| Inventory Item | `ITEM-NNNNN` | `ITEM-00001` |
| Employee | `EMP-NNNN` | `EMP-0001` |

---

## 👥 Role-Based Access Control

| Role | Access |
|------|--------|
| **Super Admin** | Full access to everything |
| **Admin** | Full access to everything |
| **Doctor** | Clinical records, prenatal, delivery, newborn, billing view |
| **Midwife** | Clinical records, prenatal, delivery, newborn, billing view |
| **Nurse** | Clinical records, prenatal, delivery, newborn |
| **Cashier** | Patient view (for billing), billing full access, reports |
| **Receptionist** | Patients, appointments, delivery/newborn view |
| **Inventory Clerk** | Inventory and purchase orders only |

Unauthorized access redirects to dashboard with an error message. The sidebar automatically hides sections the logged-in user cannot access.

---

## 🗺️ URL Structure

```
/                              → Redirect to dashboard
/accounts/login/               → Login
/accounts/staff/               → Staff list
/accounts/clinic-settings/     → Clinic settings (admin)

/patients/                     → Patient list
/patients/add/                 → Register patient
/patients/<pk>/                → Patient profile
/patients/inactive/            → Inactive patients

/prenatal/                     → Prenatal visits list
/prenatal/add/                 → Record visit
/prenatal/<pk>/                → Visit detail

/appointments/                 → Appointment list
/appointments/queue/manage/    → Queue management (staff)
/appointments/queue/           → Queue display board (public)

/delivery/                     → Delivery list
/delivery/admit/               → Admit patient
/delivery/<pk>/                → Delivery detail + update

/newborn/                      → Newborn list
/newborn/add/                  → Register newborn

/inventory/                    → Inventory list
/inventory/purchase-orders/    → Purchase orders
/inventory/suppliers/          → Suppliers

/billing/                      → Bill list
/billing/add/                  → Create bill
/billing/from-delivery/<pk>/   → Create bill from delivery (shortcut)

/dashboard/                    → Main dashboard
/dashboard/monthly/            → Monthly statistical report
/dashboard/newborn-summary/    → Newborn summary report
/dashboard/export/             → CSV data export center
/dashboard/pdf/patient/<pk>/   → Patient summary PDF
/dashboard/pdf/prenatal/<pk>/  → Prenatal visit PDF
/dashboard/pdf/delivery/<pk>/  → Delivery certificate PDF
/dashboard/pdf/bill/<pk>/      → Statement of Account PDF
/dashboard/pdf/newborn/<pk>/   → Newborn record PDF

/auditlogs/                    → Audit trail (admin)
/admin/                        → Django admin panel
```

---

## 🏗️ Architecture

```
birthing_clinic/
├── accounts/          ← Staff auth, roles, ClinicSettings model
│   └── permissions.py ← RBAC decorator and permission groups
├── patients/          ← Patient records, emergency contacts
├── prenatal/          ← Prenatal visits, lab requests, ultrasounds
├── appointments/      ← Scheduling, queue management
├── delivery/          ← Labor & delivery, labor monitoring
├── newborn/           ← Newborn records, immunizations
├── inventory/         ← Stock, suppliers, purchase orders
├── billing/           ← Bills, payments, receipts
├── reports/           ← Dashboard, reports, PDF views, CSV exports
│   ├── views.py       ← Report views + CSV export views
│   └── pdf_views.py   ← ReportLab PDF generation
├── auditlogs/         ← Audit trail, signals, middleware
│   └── middleware.py  ← CurrentUserMiddleware + signal setup
└── templates/         ← All HTML templates (Bootstrap 5)
```

---

## ⚙️ Settings

Edit `birthing_clinic/settings.py`:

```python
TIME_ZONE = 'Asia/Manila'   # Philippines timezone (UTC+8)
DEBUG = True                 # Set False for production
SECRET_KEY = '...'          # Change in production!
```

**PostgreSQL (production):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'birthcare_db',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Install: `pip install psycopg2-binary`

---

## 📋 Demo Data

The database ships pre-seeded with:
- 6 demo patients (low/moderate/high risk)
- 2 delivery records with labor monitoring and complications
- 2 newborn records with immunizations
- 10 inventory items with stock transactions
- 3 bills (paid, partial, unpaid)
- 1 admin account

---

## 🔧 Production Checklist

- [ ] Change `SECRET_KEY` in settings.py
- [ ] Set `DEBUG = False`
- [ ] Switch to PostgreSQL
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up media file serving (Nginx/S3)
- [ ] Configure Clinic Settings at `/accounts/clinic-settings/`
- [ ] Create staff accounts with appropriate roles
- [ ] Change admin password

---

*BirthCare Clinic Management System v6 — Django 6, Bootstrap 5, ReportLab · Philippines 🇵🇭*


---

## 📦 Features

### Clinical
| Module | Features |
|--------|----------|
| **Patients** | Registration, risk classification (Low/Moderate/High), obstetric history (G/P/A), EDD tracking, emergency contacts |
| **Prenatal Care** | Visit recording, vitals (BP, weight, FHR, fundal height, temp), risk flagging, lab requests, follow-up scheduling |
| **Appointments** | Booking, type classification, queue management, status updates |
| **Labor & Delivery** | Admission, labor monitoring (partograph-style), delivery outcome recording, complication tracking, referral logging |
| **Newborn Records** | Baby ID auto-generation, APGAR scores, measurements, interventions (Vit K, eye prophylaxis, NBS), immunization tracking |

### Operations
| Module | Features |
|--------|----------|
| **Inventory** | Item management with auto item codes, stock-in/out, batch/expiry tracking, low-stock alerts, supplier management |
| **Billing** | Bill generation with line items, discount support, payment recording (Cash/GCash/PhilHealth/Bank), OR auto-numbering, printable receipts |

### Reports
- Daily patient census
- Monthly delivery report
- Daily collection report
- Dashboard with 6-month delivery trend chart
- Low stock & near-expiry reports

### Admin
- Role-based staff accounts (Midwife, Doctor, Nurse, Cashier, Receptionist, Inventory Clerk, Admin)
- Complete audit trail with IP logging
- Django admin panel at `/admin/`

---

## 🏗️ Architecture

```
birthing_clinic/          ← Django project root
├── accounts/             ← Staff authentication & profiles
├── patients/             ← Patient records & emergency contacts
├── prenatal/             ← Prenatal visit tracking
├── appointments/         ← Scheduling & queue
├── delivery/             ← Labor & delivery management
├── newborn/              ← Newborn records & immunizations
├── inventory/            ← Stock management
├── billing/              ← Billing & payments
├── reports/              ← Dashboard & report views
├── auditlogs/            ← Activity audit trail
└── templates/            ← All HTML templates
```

---

## 🔑 Auto-Generated Record Numbers

| Record | Format | Example |
|--------|--------|---------|
| Patient | `PAT-YYYY-NNNN` | `PAT-2026-0001` |
| Newborn | `NB-YYYY-NNNN` | `NB-2026-0001` |
| Bill | `BILL-YYYY-NNNNN` | `BILL-2026-00001` |
| Receipt | `OR-YYYY-NNNNN` | `OR-2026-00001` |
| Purchase Order | `PO-YYYY-NNNN` | `PO-2026-0001` |
| Inventory Item | `ITEM-NNNNN` | `ITEM-00001` |
| Employee | `EMP-NNNN` | `EMP-0001` |

---

## 👥 Staff Roles & Permissions

| Role | Access |
|------|--------|
| Super Admin | Full access including user management |
| Admin | All clinical and operational access |
| Doctor | Clinical records, prenatal, delivery |
| Midwife | Prenatal, delivery, newborn |
| Nurse | Clinical records, patient care |
| Cashier | Billing and payments only |
| Receptionist | Appointments, patient registration |
| Inventory Clerk | Inventory management only |

---

## 🖥️ URL Structure

```
/                          → Dashboard
/accounts/login/           → Login page
/patients/                 → Patient list
/prenatal/                 → Prenatal visits
/appointments/             → Appointments & queue
/delivery/                 → Labor & delivery
/newborn/                  → Newborn records
/inventory/                → Stock management
/billing/                  → Billing & receipts
/accounts/staff/           → Staff management
/auditlogs/                → Audit trail
/dashboard/                → Reports dashboard
/admin/                    → Django admin
```

---

## ⚙️ Settings

Edit `birthing_clinic/settings.py`:

```python
TIME_ZONE = 'Asia/Manila'     # Change for your timezone
DEBUG = True                   # Set False for production
DATABASES = {                  # Default: SQLite (dev)
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

For **PostgreSQL** (production):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'birthcare_db',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 📊 Demo Data

Seeded on first run:
- 5 demo patients (various risk levels)
- 10 inventory items (medicines, supplies, newborn care)
- 1 supplier
- Admin account (`admin` / `admin1234`)

---

*BirthCare Clinic Management System — Built with Django 6, Bootstrap 5*
