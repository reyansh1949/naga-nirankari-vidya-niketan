# Naga Nirankari Vidya Niketan — Hindi Setup

## Features
- Class 9, 10, 11, 12
- Physics, Chemistry, Biology, Maths
- Admin login
- Chapter create karna
- Phone se video file upload
- Student side par chapter aur videos dekhna
- SQLite database; uploaded files `data/videos/` mein

## Termux par setup
1. Termux ko trusted source se install/update karein.
2. Termux khol kar chalayein:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python zip -y
   ```
3. ZIP file ko Download folder mein rakhein. Agar ZIP Termux home mein hai:
   ```bash
   cd ~
   unzip naga_nirankari_vidya_niketan.zip
   cd naga_nirankari_vidya_niketan
   ```
   Agar ZIP Downloads folder mein hai, pehle:
   ```bash
   termux-setup-storage
   cd ~/storage/downloads
   unzip naga_nirankari_vidya_niketan.zip
   cd naga_nirankari_vidya_niketan
   ```
4. Admin password ko apne password se set karein **pehli baar app chalane se pehle**:
   ```bash
   export ADMIN_PASSWORD='ApnaStrongPasswordYahan'
   ```
   `ApnaStrongPasswordYahan` ko apne password se replace karein. Password mein spaces avoid karein.
5. Start:
   ```bash
   bash run.sh
   ```
6. Browser mein kholein: `http://127.0.0.1:5000`
7. Admin login: `http://127.0.0.1:5000/admin/login`
   - Password wahi hai jo `ADMIN_PASSWORD` mein set kiya tha.
   - Agar pehle app default password ke saath start kar di, to band karein (Ctrl+C), `data/admin_hash.txt` delete karein, phir password set karke dobara start karein:
     ```bash
     rm data/admin_hash.txt
     export ADMIN_PASSWORD='ApnaStrongPasswordYahan'
     bash run.sh
     ```

## Admin se video add karna
1. Admin Panel kholein aur login karein.
2. Pehle Class, Subject aur Chapter name bhar kar **Add Chapter** karein.
3. Upload form mein chapter select karein, topic/video title likhein.
4. Phone se video file select karein aur **Upload Video** dabayein.
5. Students homepage se class → subject → chapter par ja sakte hain.

## Important
- Default max video size 500 MB hai. Badi files ke liye start karne se pehle:
  ```bash
  export MAX_UPLOAD_MB=1000
  ```
  Isse upload limit 1000 MB hogi, lekin phone aur server mein utni free storage/RAM aur stable connection hona chahiye.
- Local website sirf aapke phone par chalti hai. Dusre logon ko internet par website dene ke liye hosting, domain/URL, backups aur secure configuration chahiye.
- `data/` folder mein database, admin password hash aur uploaded videos hain. Is folder ka backup rakhein.
- Sirf aise videos upload karein jinke use/distribution ki permission aapke paas ho.
- Starter version local testing ke liye hai. Public hosting se pehle HTTPS, CSRF protection, rate limiting, secure admin password management aur cloud/server storage configuration add karna chahiye.
