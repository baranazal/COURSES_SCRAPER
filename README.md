# 🤖 BAU Course Monitor Bot

A smart bot that monitors course changes on the BAU (Balqa' Applied University) course portal and sends notifications via Telegram whenever changes are detected.

## ✨ Features
- 🔍 Real-time course monitoring (status, timings, rooms, lecturers)
- 📱 Instant Telegram notifications
- 📊 Detailed logging system for debugging
- 📈 Performance monitoring with health reports
- 🔄 Automatic error recovery
- ⚡ Low latency updates

## 📋 Prerequisites
- 🐍 Python 3.8 or higher
- 🔑 Telegram bot token (obtain from [BotFather](https://core.telegram.org/bots#botfather))
- 💬 Telegram chat IDs for notifications
- 🌐 Stable internet connection

## 🚀 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bau-course-monitor-bot.git
   cd bau-course-monitor-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the bot:
   ```bash
   # In config.py
   BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
   CHAT_IDS = ["YOUR_CHAT_ID_HERE"]
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## ⚙️ Configuration Options
```python
config_dict = {
    "college_param1": ["Engineering", "Business", "Arts"],  # Add your colleges
    "degree_param0": ["Bachelor", "Master"],               # Available degrees
    "academic_department_param2": ["CS", "IT", "IS"],      # Department codes
    "refresh_interval": 300,                               # Check interval in seconds
    "notification_format": "detailed",                     # "basic" or "detailed"
    "debug_mode": False                                    # Enable for verbose logging
}
```

## 📦 Dependencies
```plaintext
pandas>=1.5.0         # Data processing
requests>=2.28.0      # HTTP requests
python-telegram-bot>=20.0.0  # Telegram integration
asyncio>=3.4.3        # Async operations
logging>=0.4.9.6      # Logging system
```

## ⚠️ Known Issues & Solutions
| Issue | Status | Solution |
|-------|---------|------------|
| Empty or NaN Values in Data | ✅ Fixed | Standardized empty values using consistent placeholder (`''`) |
| Rate Limiting and API Overload | ✅ Fixed | Implemented rate-limiting with `asyncio.Semaphore` and request interval |
| Inconsistent Status Codes | ✅ Fixed | Added status mapping system (`1` → `Available`, etc.) |
| Duplicate Notifications | ✅ Fixed | Implemented notification cooldown mechanism |
| CSV File Corruption | ✅ Fixed | Standardized to `utf-8-sig` encoding |
| Error Handling for API Failures | ✅ Fixed | Added robust error handling with retry mechanism |

## 📝 Logging
```plaintext
logs/
  ├── bot.log           # Main log file
  ├── errors.log        # Error-specific logs
  └── changes.log       # Course changes history
```

## 🔧 Troubleshooting
Common issues and solutions:
1. **Bot not responding:**
   ```bash
   # Check bot status
   python scripts/check_status.py
   ```

2. **Missing notifications:**
   - Verify Telegram token
   - Check internet connection
   - Confirm chat IDs

## 🚀 Deployment Tips
1. **Using PM2:**
   ```bash
   pm2 start main.py --name "bau-bot"
   pm2 save
   ```

2. **Using Docker:**
   ```bash
   docker build -t bau-bot .
   docker run -d bau-bot
   ```

3. **Using Systemd:**
   ```bash
   sudo systemctl enable bau-bot
   sudo systemctl start bau-bot
   ```

## 👥 Contributing
1. 🍴 Fork the repository
2. 🌿 Create your feature branch: `git checkout -b feature/AmazingFeature`
3. 💾 Commit your changes: `git commit -m 'Add AmazingFeature'`
4. 📤 Push to the branch: `git push origin feature/AmazingFeature`
5. 🔄 Open a Pull Request

## 📈 Performance Monitoring
The bot includes built-in performance monitoring:
- CPU usage
- Memory consumption
- Response times
- API call statistics

Access metrics via:
```bash
python scripts/metrics.py --format json
```

## 📄 License
This project is licensed under the MIT License

## 📞 Support
- 📧 Email: bara.naser002@gmail.com
- 💬 Telegram: @bara2025
- 📱 Discord: not_solid

## 🙏 Acknowledgments
- Telegram Bot API Team
- Open Source Community

---
Made with love.
