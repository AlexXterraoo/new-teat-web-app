# RailVPN - FastAPI & Xray on Railway

A lightweight, stable, and easy-to-deploy VLESS-WebSocket proxy and management panel designed to run seamlessly on [Railway](https://railway.app).

---

## 🚀 Architecture & Overview / معماری و ساختار پروژه

* 🌐 **Nginx (Port 8080):** دروازه ورودی و پروکسی معکوس برای مدیریت مسیرهای وب‌سکت و بررسی سلامت سرور (`/health` و `/railvpn`).
* 💻 **FastAPI (Port 8081):** پنل مدیریت مبتنی بر پایتون برای نظارت بر وضعیت کاربران و ترافیک.
* ⚡ **Xray Core (Port 10000):** هسته قدرتمند و پرسرعت برای پردازش اتصالات پروتکل VLESS.

---

## ⚠️ Important Security Warning / هشدار امنیتی مهم

> پیش از استقرار نهایی، حتماً **UUIDهای پیش‌فرض** موجود در فایل `config.json` (بخش `clients`) را تغییر داده و مقادیر کاملاً اختصاصی و رندوم خود را جایگزین کنید. استفاده از UUIDهای مشترک یا پیش‌فرض باعث تداخل جدی در اتصال و ترافیک خواهد شد! 🔒
> 
> Make sure to generate your own unique UUIDs and replace the sample ones in the `config.json` file. Using shared UUIDs will cause connection conflicts.

---

## 🔗 VLESS Connection Template / فرمول لینک اتصال

```text
vless://YOUR_UUID@YOUR_RAILWAY_APP.up.railway.app:443?encryption=none&security=tls&sni=YOUR_RAILWAY_APP.up.railway.app&type=ws&path=%2Frailvpn#username
📌 راهنمای جایگذاری مقادیر:

    🔑 به جای عبارت YOUR_UUID: یکی از UUIDهای رندوم و اختصاصی خودتان (همان‌هایی که داخل فایل config.json ست کرده‌اید) را قرار دهید.

    🌐 به جای عبارت YOUR_RAILWAY_APP.up.railway.app: آدرس دامنه فعال پروژه‌تان در رایلی (یا هر دامین اختصاصی دیگری) را وارد کنید.

    👤 به جای عبارت username: یک نام دلخواه و نمایشی برای کانفیگ خود بنویسید (مثل user1 یا sdido) تا در برنامه‌ی کلاینت شناسایی شود.
