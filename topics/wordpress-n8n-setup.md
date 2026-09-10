# WordPress + n8n Setup (VM Ubuntu 192.168.18.14)

> Status terakhir: 2026-09-08. Lihat `sessions/2026-09/20260908_152707_24a829-wordpress-n8n-setup.md` untuk transcript lengkap.

## Ringkasan

VM Ubuntu 24.04 di VirtualBox (Bridged). IP: `192.168.18.14`. WordPress dan n8n di-setup di VM yang sama.

## Layanan yang jalan

| Layanan | Port | Akses dari host |
|---|---|---|
| WordPress (Nginx) | 80 | http://192.168.18.14/ |
| n8n (Nginx proxy) | 81 | http://192.168.18.14:81/ |
| MariaDB | 3306 | local only |
| PHP 8.3-FPM | socket | local |
| Docker n8n | 5679 | via Nginx port 81 |

## File & Credentials

- WordPress files: `/var/www/wordpress/`
- wp-config.php: `/var/www/wordpress/wp-config.php`
- Database: `wordpress`, user `wpuser` / pass `wppass123`
- n8n data volume: `/opt/n8n-local/`
- n8n container: `n8n-local`

## Perintah penting

```bash
# Cek status
sudo systemctl is-active mariadb php8.3-fpm nginx
sudo docker ps | grep n8n-local
sudo ufw status
ss -tlnp | grep -E ':(80|81|5679)\b'

# Restart
sudo systemctl restart nginx
sudo systemctl restart php8.3-fpm
sudo docker restart n8n-local

# Nginx test
sudo nginx -t

# Database check
sudo mysql -u wpuser -p wppass123 -e "USE wordpress; SHOW TABLES;"
```

## Masalah yang kejadian

### 1. n8n port 5678 redirect ke WordPress
Penyebab: di HOST komputer ada service yang listen di port 5678, bukan di VM.
Solusi: ganti port n8n di VM jadi 5679, setup Nginx proxy di port 81.

### 2. curl ke 5679 failed dari dalam VM
Penyebab: UFW firewall block port 5679 dari external.
Solusi: bukan buka 5679, tapi setup Nginx proxy di port 81 (sudah diallow UFW).

## Langkah besok (pending)

1. Complete WordPress instalasi via browser: http://192.168.18.14/
2. Login n8n: http://192.168.18.14:81/, setup workflow auto-post
3. Kalau ada domain, setup SSL dengan certbot
