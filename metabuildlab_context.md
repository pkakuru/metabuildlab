## 🧭 Meta Build Lab – Project Context for Cursor

### 🛡️ Project Overview

The **Meta Build Lab Office Management System** is a Django-based internal management platform designed for a civil engineering and materials testing laboratory in Uganda.

It will be used by directors, lab managers, office staff, and technicians to handle **quotations, invoices, client records, test jobs, lab operations, and reports** — all under one unified system.

The project is being developed inside **Cursor IDE** using the “skeleton-first” approach: first building the structure (login, sidebar, top navbar, role-based access) and then adding feature modules incrementally.

---

### 👥 Users and Roles

1. **Director** – Full access to all modules and system configuration.
2. **Lab Manager** – Manages jobs, quotations, and pricing; views finance summaries.
3. **Office Staff** – Handles client registration, quotations, invoices, and receipts.
4. **Technician** – Works on assigned jobs, uploads results, views personal worklist.

---

### 📦 Core Modules (Main System Sections)

Each module is accessible from the **top navbar**. Selecting a module updates the **left sidebar** with its related menus.

| Module         | Purpose / Content                                         |
| -------------- | --------------------------------------------------------- |
| **Sales**      | Quotations, Clients, Leads, Contracts                     |
| **Operations** | Jobs, Samples Intake, Technician Worklist, Results Review |
| **Pricing**    | Master Price List, Categories, Tests & Parameters         |
| **Finance**    | Invoices, Payments, Receipts, Revenue Reports             |
| **Config**     | Users & Roles, Labs, Instruments, Test Catalog, Audit Log |

---

### 🎨 UI Layout Summary

The system uses a **Bootstrap 5 dashboard layout**:

* **Top Navbar (Horizontal):** Displays the 5 main modules.

  * Left: Meta Build Lab logo
  * Center: Active module highlight (Sales, Operations, etc.)
  * Right: Logged-in user info and dropdown (Profile, Settings, Logout)
* **Left Sidebar (Vertical):** Displays contextual links based on the active module and user role.
* **Main Content Area:** Displays each module’s page (e.g., quotations table, job tracker, etc.).
* **Responsive Design:** Sidebar collapses on small screens with a toggle button.

---

### 🔐 Authentication & Access

* Custom `User` model extending Django’s `AbstractUser` with a `role` field.
* Login/logout system using Django’s auth views.
* Middleware restricts access to certain modules based on user role.
* Sidebar and top navbar dynamically render links based on the logged-in user’s role.

---

### ⚙️ Technical Stack

* **Backend:** Django 5.x
* **Frontend:** Bootstrap 5, HTML5, JavaScript
* **Database:** SQLite (development), PostgreSQL (production-ready)
* **Reporting:** Chart.js for analytics; `reportlab` for PDF generation
* **Environment:** Cursor IDE + Git for version control

---

### 🚧 Development Approach (Phased Plan)

1. **Phase 1 – Skeleton Build**

   * Django setup + authentication
   * Base HTML templates (`base.html`, `login.html`, `dashboard.html`)
   * Sidebar + Top Navbar navigation system
   * Role-based visibility and routing

2. **Phase 2 – Sales Module**

   * Client and Quotation management
   * PDF quotation generation
   * Search and filter for clients and quotes

3. **Phase 3 – Operations Module**

   * Job tracking, samples intake, technician assignments
   * Results upload and review

4. **Phase 4 – Finance Module**

   * Invoices, payments, receipts, and revenue analytics

5. **Phase 5 – Reports and Config**

   * Turnaround reports, test analytics
   * User management, labs, instruments, and catalog

---

### 💡 Cursor Instructions (for Co-Coding)

When using vibe coding in Cursor, keep these instructions in context:

* Generate Bootstrap-based templates (no React or frontend frameworks).
* Always use Django’s `templates`, `views`, and `urls.py` structure.
* When creating CRUD pages, use Django `ModelForm` for form handling.
* Use context variables for passing role-based UI elements.
* Keep code modular — each module (sales, operations, etc.) gets its own app folder.

---

### 🏁 End Goal

Deliver a professional, role-based, full-stack Django system with a consistent UI and extendable architecture — initially for **Meta Build Lab** (single tenant), but structured to allow multi-lab support in the future if needed.
