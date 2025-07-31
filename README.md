# 🛡️ Malicious Extension Detection

Malicious Extension Detection is a Python-based tool to identify **malicious Chrome extensions** by intercepting and analyzing their network behavior using `mitmproxy`. It detects actions such as **keylogging**, **screen capturing**, and **unauthorized traffic** to external domains.

---

## ✨ Features

- 🔍 Real-time network traffic interception
- 🧠 Behavioral analysis of browser extensions
- 📊 Risk scoring system
- 🚨 Pop-up alerts for suspicious behavior
- ⚙️ Configurable detection rules

---

## 🖥️ System Requirements

- Python 3.7 or higher
- Chrome browser
- OS: Windows, Linux, or macOS
- Admin access (for root certificate installation)

---

## 🧰 Prerequisites

### ✅ 1. Install Required Python Packages

✅ 2. Set Up System Proxy
To analyze all network activity, route your system traffic through a proxy (e.g., 127.0.0.1:8080).

📌 Windows
Go to Settings → Network & Internet → Proxy

Enable Manual proxy setup

Set:

Address: 127.0.0.1

Port: 8080

📌 Linux/macOS
Set environment variables in your shell:
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080

✅ 3. Install mitmproxy

pip install mitmproxy
Or download from: https://mitmproxy.org

🔐 Installing the mitmproxy Root Certificate
To intercept HTTPS traffic, you must install and trust mitmproxy’s root certificate.

🪟 Windows
Start mitmproxy in terminal:
mitmproxy
In your browser, open: http://mitm.it

Download the Windows certificate.

Press Win + R, type mmc, and press Enter.

Go to:

File → Add/Remove Snap-in

Add Certificates for Computer Account

Navigate to:

pgsql
Copy
Edit
Trusted Root Certification Authorities → Certificates
Right-click → All Tasks → Import

Choose the downloaded .cer file and complete the wizard.

Restart your browser (or system) to apply.

```bash
pip install mitmproxy watchdog requests psutil
