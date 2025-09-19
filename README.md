# 🕹️ Game Night Timer — Google AIY Voice Kit v1

A DIY **Game Night Buzzer** project built with the **Google AIY Voice Kit v1**.  
Repurpose the kit’s built-in button, LED, and speaker into a **one-button, chess-clock-style timer** for board games and card games.  

Press the button → your turn ends → the next player’s countdown starts.  
When time runs out, the speaker plays a buzzer sound and the LED signals timeout.  

---

## ✨ Features
- Uses the **Google AIY Voice Kit v1** as an all-in-one enclosure  
- Big button for turn switching  
- Built-in speaker for buzzer sounds  
- LED status indicator  
- Auto-starts on boot via `systemd`  

---

## 🛠️ Requirements
- Google AIY Voice Kit v1 (discontinued)  
- Raspberry Pi 3 (required for the AIY Voice Kit v1)  
- microSD card (8 GB minimum, flashed with **Raspberry Pi OS Legacy, 32-bit Bullseye**)  
- Internet connection for package installation
- Small Phillips head screwdriver to connect speaker to voice hat

---

## 📦 Setup Instructions

### 1. Assemble the Voice Kit
Follow the kit’s original assembly guide so the button, LED, and speaker are connected.  

### 2. Flash Raspberry Pi OS (Legacy)
Download and flash **Raspberry Pi OS Legacy (Bullseye)** to your microSD card.  
Boot your Pi and expand the filesystem on first boot.  

### 3. Update the OS
```bash
sudo apt update && sudo apt upgrade -y
```

### 4. Enable the Voice HAT overlay
```bash
echo "dtoverlay=googlevoicehat-soundcard" | sudo tee -a /boot/config.txt
sudo reboot
```

### 5. Test the speaker
```bash
speaker-test -t sine -f 1000 -l 1
```

### 6. Install libraries
```bash
sudo apt install -y git python3-pip python3-rpi.gpio python3-smbus python3-gpiozero
```

### 7. Install the AIY Python library
```bash
git clone https://github.com/google/aiyprojects-raspbian.git
cd aiyprojects-raspbian/src
sudo pip3 install .
```

### 8. Clone this Repository
```bash
git clone https://github.com/carolinedunn/game-night-timer-aiy-voice-kit.git
```

### 9. Run the test files
See tutorial video

## ▶️ Running the Timer on Boot

### 1. Prepare environment
```bash
sudo usermod -a -G audio <your-username>
sudo mkdir -p /opt/aiy
sudo cp ~/Documents/AIY/timer-aiy.py /opt/aiy/
sudo chmod +x /opt/aiy/timer-aiy.py
```

### 2. Create a systemd service
```bash
sudo nano /etc/systemd/system/aiy-timer.service
```

### Paste the following (replace <your-username> with your Pi username):
```bash
[Unit]
Description=AIY Two-Player Timer
Wants=sound.target alsa-restore.service
After=local-fs.target sound.target alsa-restore.service syslog.target

[Service]
Type=simple
User=<your-username>
Group=audio
WorkingDirectory=/opt/aiy
Environment=PYTHONUNBUFFERED=1
Environment=HOME=/home/<your-username>

ExecStartPre=/bin/sh -c 'for i in $(seq 1 20); do aplay -l | grep -qi "voicehat\|googlevoicehat\|snd_rpi_googlevoicehat" && exit 0; sleep 1; done; echo "AIY sound card not detected"; exit 1'
ExecStartPre=/usr/bin/amixer -q -c 0 sset Master 85% unmute || /usr/bin/true
ExecStartPre=/usr/bin/amixer -q -c 0 sset Headphone 85% unmute || /usr/bin/true
ExecStartPre=/usr/bin/amixer -q -c 0 sset PCM 85% unmute || /usr/bin/true

ExecStart=/usr/bin/python3 /opt/aiy/timer-aiy.py
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

```

### 3. Configure ALSA defaults
Create /etc/asound.conf so audio services don’t depend on per-user config:
```bash
sudo tee /etc/asound.conf >/dev/null <<EOF
defaults.pcm.card 1
defaults.ctl.card 1
EOF
```

Restart ALSA:
```bash
sudo systemctl restart alsa-restore.service 2>/dev/null || true
sudo alsactl init || true
```

### 4. Test audio
```bash
aplay -l
aplay -L | sed -n '1,200p'
sudo -u <your-username> aplay /usr/share/sounds/alsa/Front_Center.wav
```

### 5. Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable aiy-timer.service
sudo systemctl start aiy-timer.service
sudo reboot
```

---

## ▶️ Tutorial Video
🎥 YouTube tutorial: [Google AIY Voice Kit v1 Game Night Timer](https://youtu.be/WSQV_xoQzLM)  

---

## 🖥️ Usage
- Press the kit’s big button to start Player 1.
- Each press flips turns between players.
- The LED indicates active state and timeout.
- The built-in speaker plays buzzer sounds at timeout.

---

## 📂 Project Series
This is part of my **Game Night Buzzer** series:  
- [Episode 1: Raspberry Pi LED Timer](https://youtu.be/0G3-ISume2o)  
- [Episode 2: Raspberry Pi LCD Timer](https://youtu.be/WSQV_xoQzLM)  
- [Episode 3: Raspberry Pi Bluetooth Speaker Timer](https://youtu.be/rIc2U7KOW9k)  
- Episode 4+: Pico & Arduino builds  

---

## 📖 License
MIT License — free to use, remix, and share.  
Attribution appreciated: link back to [Caroline Dunn’s channel](https://www.youtube.com/caroline).  

---

## 📚 Author
Created by **Caroline Dunn**  
- 🌐 [carolinedunn.org](https://carolinedunn.org)  
- 📺 [YouTube.com/Caroline](https://www.youtube.com/caroline)  
- 📘 [A Woman’s Guide to Winning in Tech](https://amzn.to/3YxHVO7)  
