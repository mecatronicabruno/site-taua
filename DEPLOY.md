# Deploy — Tauá Fernandes

Static site (HTML/CSS/JS) served by **nginx**, deployed to the **Hetzner** server
via **Docker Swarm + Traefik**, fronted by **Cloudflare** (proxy/CDN).
Pipeline mirrors `drome-site`: a self-hosted GitHub runner on the server does
`rsync → docker build → docker stack deploy → Cloudflare purge`.

```
push to main ─▶ GitHub Actions (self-hosted runner on the server)
                 │  rsync ./ → /root/apps/taua-site
                 │  docker build -t taua-site:<sha>
                 │  docker stack deploy taua-site
                 └▶ Traefik routes tauafernandes.com.br → nginx :80
                    Cloudflare (proxy) ─▶ Traefik (TLS, Let's Encrypt)
```

## Files

| File | Purpose |
|---|---|
| `.github/workflows/deploy.yml` | CI/CD pipeline (push to `main`) |
| `Dockerfile` | `nginx:1.27-alpine` serving the static files |
| `deploy/nginx.conf` | server block: gzip, cache headers, `/healthz`, security headers |
| `docker-compose.swarm.yml` | Swarm service + Traefik labels (TLS, redirects) |

## One-time setup

### 1. GitHub repository
- Push this repo to GitHub with the default branch **`main`**.
- The deploy runs on the existing **self-hosted runner** labeled `self-hosted, development`
  (the same one `drome-site` uses — already installed on the Hetzner server). No new runner needed.

### 2. GitHub Secrets
`Settings → Secrets and variables → Actions → New repository secret`:

| Secret | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare token with **Zone → Cache Purge** permission for `tauafernandes.com.br` |
| `CLOUDFLARE_ZONE_ID` | Zone ID of `tauafernandes.com.br` (Cloudflare → Overview → API section) |

> If the secrets are absent the deploy still works — it just skips the cache purge.

### 3. Cloudflare DNS (proxied)
Point the domain at the Hetzner server IP, **proxy ON (orange cloud)**:

| Type | Name | Content | Proxy |
|---|---|---|---|
| `A` | `tauafernandes.com.br` (`@`) | `<HETZNER_IP>` | Proxied |
| `CNAME` | `www` | `tauafernandes.com.br` | Proxied |

- **SSL/TLS mode: `Full (strict)`** — Traefik presents a real Let's Encrypt cert at the origin.
- `www` → apex (`tauafernandes.com.br`) is 301-redirected by Traefik (canonical = apex).

> **Cert note:** Traefik obtains the LE cert via the shared `letsencryptresolver`
> (same mechanism as `drome-site`). If first issuance ever fails behind the proxy,
> temporarily set the DNS records to **DNS-only (grey cloud)**, let the cert issue,
> then turn the proxy back on.

## Deploy

Just push:

```bash
git push origin main
```

…or trigger manually from the **Actions** tab (`workflow_dispatch`).

## Verify after deploy

```bash
# on the server
docker stack services taua-site
curl -I https://tauafernandes.com.br            # 200, served via Traefik/Cloudflare
curl -I https://www.tauafernandes.com.br        # 301 → https://tauafernandes.com.br
curl -s  https://tauafernandes.com.br/healthz   # ok
```

## Rollback

```bash
# list image tags on the server
docker images taua-site
# redeploy a previous tag
cd /root/apps/taua-site
sed -i "s|image: taua-site:latest|image: taua-site:<previous_sha>|" docker-compose.swarm.yml
docker stack deploy -c docker-compose.swarm.yml taua-site
```
