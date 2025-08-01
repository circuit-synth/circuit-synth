# Circuit-Synth Website

Simple website for Circuit-Synth with automatic Digital Ocean deployment.

## 🚀 Deploy to Digital Ocean

**One command setup:**

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Clone and run setup
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth/website
sudo ./setup.sh
```

**That's it!** Your website will automatically update every hour from GitHub.

## 🔄 How It Works

- **Systemd Timer**: Runs `git pull` every hour automatically
- **Auto-Copy**: Updates HTML/CSS files from `website/` directory  
- **Nginx Reload**: Serves updated content immediately

## ⏰ Managing Updates

```bash
# Check timer status
sudo systemctl status circuit-synth-update.timer

# View update logs  
sudo journalctl -u circuit-synth-update.service -f

# Manual update (don't wait for timer)
sudo systemctl start circuit-synth-update.service

# See when next update is scheduled
systemctl list-timers circuit-synth-update.timer
```

## 📁 Files

- `index.html` - Main website page
- `style.css` - Website styles
- `setup.sh` - Digital Ocean deployment script
- `circuit-synth-update.service` - Systemd service for git pull
- `circuit-synth-update.timer` - Hourly timer
- `README.md` - This file

## 🌐 Usage

1. Edit `index.html` and `style.css` 
2. Push changes to GitHub
3. Wait up to 1 hour for automatic deployment
4. Or trigger manual update: `sudo systemctl start circuit-synth-update.service`