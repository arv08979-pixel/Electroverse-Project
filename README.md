# Electroverse Project

## Goal
To capture video feed, identify objects, encrypt, store, and decrypt the data.

---

## Frontend
Built using **React + Vite**

This template provides a minimal setup to get React working in Vite with HMR and ESLint rules.

### Plugins used
- @vitejs/plugin-react – uses Babel for Fast Refresh
- @vitejs/plugin-react-swc – uses SWC for Fast Refresh

### React Compiler
The React Compiler is enabled in this project.  
Refer to the documentation: https://react.dev/learn/react-compiler

> Note: This may impact Vite dev and build performance.

---

## Backend
- Video capture and recording
- Object detection
- Encryption and decryption
- Secure video storage

---

## Quick start

1. Copy `.env.template` to `.env` and fill values.
2. Create virtualenv and install requirements: `pip install -r requirements.txt`.
3. Run MongoDB and set `EV_MONGO` if needed.
4. Start backend: `python backend/main.py` to start the recorder, CV processor, encryptor, and server threads.

## Project Structure
 
---

## Production deployment (concise)

Use a reverse proxy (nginx) to terminate TLS and proxy requests to the Flask process. Keep `EV_SECURE_COOKIES=true` and run the app behind HTTPS so `ev_token` cookies are marked `Secure` and `HttpOnly`.

Example nginx site (replace domain and paths):

```
server {
	listen 80;
	server_name your.domain.example;
	return 301 https://$host$request_uri;
}

server {
	listen 443 ssl http2;
	server_name your.domain.example;

	ssl_certificate /etc/letsencrypt/live/your.domain.example/fullchain.pem;
	ssl_certificate_key /etc/letsencrypt/live/your.domain.example/privkey.pem;

	location / {
		proxy_pass http://127.0.0.1:5000/;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection "upgrade";
	}
}
```

Systemd service (example for `backend`):

```
[Unit]
Description=Electroverse backend
After=network.target mongod.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/repo
EnvironmentFile=/path/to/repo/.env
ExecStart=/usr/bin/python3 backend/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Notes:
- Use a production-grade WSGI server (gunicorn) if you refactor the app to be a pure WSGI app. The current `main.py` orchestrates threads; for production you may split services (recorder, cv, encryptor) and run the server as a separate WSGI service behind nginx.
- Obtain certificates with Certbot and set `EV_SSL_CERT`/`EV_SSL_KEY` only if you want Flask to bind HTTPS directly (recommended: let nginx handle TLS).
- Verify `EV_SECRET_KEY` is strong and rotate it securely if needed.


for ssh key
```
 openssl req -x509 -newkey rsa:2048 -keyout localhost-key.pem -out localhost-cert.pem -days 365 -nodes -subj "/CN=localhost"
 ```