# MTNSPEC Deployment & FinTech Integration Guide | Zimbabwe 2026
> **Hosting The National Mineral Intelligence Hub under `mining.mtnspec.co.zw`**

---

## 🌐 1. Cloudflare DNS Configuration

Since `mtnspec.co.zw` is managed via **Cloudflare DNS**, setting up the subdomain takes less than 60 seconds:

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Select the domain **`mtnspec.co.zw`**.
3. Go to **DNS** &rarr; **Records** &rarr; click **Add record**.
4. Configure:
   * **Type:** `A` (or `CNAME` if pointing to an existing server hostname or Render/Vercel URL)
   * **Name:** `mining`
   * **IPv4 address:** `[Your Server Public IP]` (e.g. `102.x.x.x` or VPS IP)
   * **Proxy status:** **Proxied (Orange Cloud ON)** &mdash; provides free SSL, DDoS protection, and worldwide CDN caching.
   * **TTL:** `Auto`
5. Click **Save**.

Your platform will now resolve securely at:
```
https://mining.mtnspec.co.zw
```

---

## 🚀 2. Server Deployment Options

### Option A: Direct Python / Systemd Service (Recommended for Linux VPS)

1. Clone or copy the repository onto the server:
   ```bash
   cd /var/www
   git clone https://github.com/MTN-spec/The-National-mineral-Intelligence-Hub.git
   cd The-National-mineral-Intelligence-Hub
   ```

2. Set up Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install uvicorn fastapi qrcode[pil]
   ```

3. Enable the systemd service:
   ```bash
   sudo cp mining_mtnspec.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable mining_mtnspec
   sudo systemctl start mining_mtnspec
   sudo systemctl status mining_mtnspec
   ```

4. Configure Nginx reverse proxy:
   ```bash
   sudo cp mtnspec_mining_nginx.conf /etc/nginx/sites-available/mining.mtnspec.co.zw
   sudo ln -s /etc/nginx/sites-available/mining.mtnspec.co.zw /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

---

### Option B: Docker / Docker Compose (One-Command Launch)

```bash
docker compose up -d --build
```
Your service will be listening on port `8000` with automated restarts enabled.

---

## 💳 3. Unified FinTech Architecture (Change It™ + EcoCash)

The platform unites **MTNSPEC's Change It™ Engine** with **EcoCash Mobile Escrow**:

| Feature | MTNSPEC Change It™ (`mtnspec.co.zw`) | EcoCash Mobile Money |
|---|---|---|
| **Role** | Instant P2P Ore & Transport Settlement | Merchant Escrow & Cashout Gateway |
| **Speed** | Sub-second (<200ms) cashless | USSD Push Notification |
| **Fee Structure** | 0% Subsidized for Artisanal Syndicates | Standard Statutory Tariff |
| **Asset Backing** | USD + ZiG convertible ledger | Reserve Bank of Zimbabwe (RBZ) ZiG Escrow |
| **Target Use** | Panning lot payouts, diesel refunds, claim peer transfers | Royalties, MMCZ compliance inspection fees |

### API Endpoints:
* `GET  /api/fintech/wallet` &mdash; Returns live liquidity across both Change It and EcoCash.
* `POST /api/fintech/transfer` &mdash; Instant P2P transfer between registered miners/carriers.
* `POST /api/fintech/pay` &mdash; Official ore transit permit fees and royalty payments.
* `POST /api/permits/generate` &mdash; Issues cryptographic transit QR with MTNSPEC verification signature.

---

## 🔗 4. Linking from `mtnspec.co.zw` Main Website

To integrate the Mineral Hub into your existing live site ([`mtnspec.co.zw`](https://mtnspec.co.zw)), add this menu item to the navigation in your site's `index.html`:

```html
<!-- Inside <header> <nav> <ul> -->
<li>
    <a href="https://mining.mtnspec.co.zw" target="_blank" class="btn-nav" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-weight: 700;">
        <i class="fas fa-gem"></i> Mineral Hub
    </a>
</li>
```

And in the **Services** or **About** section of `mtnspec.co.zw`:
```html
<div class="card tilt-card">
    <i class="fas fa-satellite"></i>
    <h4>Mineral Intelligence</h4>
    <p>Sovereign Earth Observation, Sentinel-2 spectral indices, and artisanal mining cadastre for Zimbabwe 2026.</p>
    <a href="https://mining.mtnspec.co.zw" target="_blank" style="color: var(--primary-color); font-weight: 600; font-size: 0.9rem;">
        Launch Platform &rarr;
    </a>
</div>
```
