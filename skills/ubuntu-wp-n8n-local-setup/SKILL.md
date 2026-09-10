---
name: ubuntu-wp-n8n-local-setup
description: Setup WordPress + n8n lokal di VM Ubuntu
---
# Ubuntu WordPress + n8n Local Setup (VirtualBox Bridged)

## Context
VM Ubuntu 24.04 di VirtualBox. Bridged network adapter.
IP VM: 192.168.18.14
Testing dari host (komputer luar) pakai browser biasa tanpa SSH tunnel.

## Status Session (Hari ini)

### Layanan yang udah jalan
| Layanan | Port | Status |
|---|---|---|
| Nginx (WordPress) | 80 | Running |
| Nginx (n8n proxy) | 81 | Running |
| MariaDB | 3306 local | Running |
| PHP 8.3-FPM | socket | Running |
| Docker n8n container | 5679 internal -> 5679 | Running |
| UFW firewall | 80, 443, 81, 5679 allow | Configured |

### File & Data
- WordPress files: /var/www/wordpress/
- WordPress config: /var/www/wordpress/wp-config.php
- Database: wordpress (user: wpuser / pass: wppass123)
- n8n data volume: /opt/n8n-local/
- n8n container name: n8n-local

### URL Testing
- WordPress instalasi: http://192.168.18.14/
- n8n editor: http://192.168.18.14:81/

## Langkah yang udah dilakukan

### 1. Bersihkan server dari konfig lama
- Hapus nginx config lama (karirpro.biz.id, default)
- Hapus /var/www/wordpress, database wordpress, user wpuser
- Hapus container n8n lama dan /opt/n8n
- Install ulang: MariaDB, PHP 8.3 + extensions, Nginx, Docker

### 2. Setup WordPress
- Download WordPress latest.zip, extract ke /var/www/wordpress
- Buat wp-config.php dengan database credentials
- Buat Nginx config (/etc/nginx/sites-available/localhost-wp) listen port 80

### 3. Setup n8n via Docker
- Pull image n8nio/n8n:latest
- Run container: docker run -d --name n8n-local -p 5679:5678 -v /opt/n8n-local:/home/node/.n8n -e GENERIC_TIMEZONE=Asia/Jakarta -e N8N_SECURE_COOKIE=false n8nio/n8n
- Setup Nginx reverse proxy port 81 -> 127.0.0.1:5679

### 4. Firewall (UFW)
- allow 80/tcp, 443/tcp, 81/tcp (sudah ada dari sebelumnya)
- allow 5679/tcp (kalau perlu direct access, tapi nggak dipakai karena Nginx proxy)

## Notes & Masalah yang kejadian

### Masalah 1: n8n port 5678 redirect ke WordPress
- Penyebab: Di HOST komputer, ada service yang listen di port 5678 (bukan di VM). Saat browse http://192.168.18.14:5678, host merespons sendiri (HTML WordPress) bukan VM.
- Solusi: Ganti port n8n di VM jadi 5679, setup Nginx proxy di port 81 (port yang udah diallow di UFW).

### Masalah 2: curl ke 192.168.18.14:5679 failed dari dalam VM
- Penyebab: UFW firewall block port 5679 dari external.
- Solusi: Bukan buka 5679, tapi setup Nginx proxy di port 81 (sudah diallow).

## Langkah besok (Lanjutan)

### 1. Complete WordPress instalasi
- Bukaa http://192.168.18.14/ dari browser host
- Isi: Site Title, Username, Password, Email
- Install WordPress

### 2. Setup n8n auto-post workflow
- Login ke http://192.168.18.14:81/
- Buat credentials: WordPress API (jika perlu)
- Buat workflow untuk auto-post (contoh: blog RSS -> WordPress, atau social media auto-post)

### 3. Setup domain + SSL (kalau lo udah punya domain)
- Setup Nginx config untuk domain beneran
- Install certbot: sudo apt install certbot python3-certbot-nginx
- Buat SSL cert: sudo certbot --nginx -d domain.com

### 4. Production deployment
- Ubah wp-config.php hardcoded credentials ke yang lebih secure
- Setup auto-start Docker container
- Setup monitoring/logging

## Perintah penting (reference)

### Cek status services
```bash
sudo systemctl is-active mariadb php8.3-fpm nginx
sudo docker ps | grep n8n-local
sudo ufw status
ss -tlnp | grep -E ':(80|81|5679)\b'
```

### Restart services
```bash
sudo systemctl restart nginx
sudo systemctl restart php8.3-fpm
sudo docker restart n8n-local
```

### Nginx config test
```bash
sudo nginx -t
```

### Cek log
```bash
sudo docker logs n8n-local --tail 50
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database WordPress
```bash
sudo mysql -u wpuser -p wppass123 -e "USE wordpress; SHOW TABLES;"
```

### Hapus & reset
```bash
# Hapus WordPress
sudo rm -rf /var/www/wordpress
sudo mysql -e "DROP DATABASE IF EXISTS wordpress;"
sudo mysql -e "DROP USER IF EXISTS 'wpuser'@'localhost';"

# Hapus n8n
sudo docker rm -f n8n-local
sudo rm -rf /opt/n8n-local

# Hapus Nginx config
sudo rm /etc/nginx/sites-enabled/localhost-wp
sudo rm /etc/nginx/sites-enabled/n8n-local
sudo systemctl reload nginx
```
