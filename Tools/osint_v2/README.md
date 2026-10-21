# 🔎 osint_v2

**OSINT focused on finding people.** Start from a single piece of data (email, name, username or phone number) and it gathers everything available in open sources into one report: social media accounts, data breaches, profiles and ready-to-open searches.

Free. No API keys. No sign-up required.

---

## ⚡ Quick install

```bash
git clone https://github.com/JRXsec/OSCP-Master.git && cd OSCP-Master/Tools/osint_v2

pip3 install --break-system-packages -r requirements.txt

python3 main.py
```

---

## 🧠 How it works

1. **You give it one piece of data** about the person. It automatically detects whether it's an email, a name, a username or a phone number.
2. **It queries every source at once**, with a progress bar for each one. If one fails, the rest keep going.
3. **It shows you the results** in the terminal and generates an **HTML report** with clickable links and a search filter, which opens automatically in your browser.

> The tool's interface is in Spanish.

---

## 👤 What it finds from each input

| You start with… | You get |
|---|---|
| 📧 **Email** | Data breaches it appears in, Gravatar profile, sites where it's registered and accounts with the same username |
| 🪪 **Full name** | Every combination of the name (Pepe Pepito García → Pepe García, Pepe Pepito…), with and without accents, searched across ~700 sites, Google and LinkedIn |
| 🏷️ **Username** | Accounts with that username on ~700 sites |
| 📱 **Phone** | Country, region, carrier, line type, WhatsApp and Telegram links, and searches for the number in all its formats |
| 🌐 **Domain** | WHOIS, DNS, subdomains and the services it uses |

---

## 🛠️ Usage

```bash
python3 main.py                          # interactive menu
python3 main.py pepe@gmail.com           # auto-detects the input type
python3 main.py "Pepe Pepito García"     # full name
python3 main.py +34600123456             # phone number
```

Reports are saved in `reports/`.

---

## ⚠️ Disclaimer

For **educational use and authorized investigations only**. Respect privacy and the data protection laws of your country (GDPR in Europe).
