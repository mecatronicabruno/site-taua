# Deploy — Tauá Fernandes

Static site (HTML/CSS/JS) hosted on **Amazon S3** (static website hosting),
fronted by **Cloudflare** (proxy/CDN + TLS). Push to `main` → GitHub Actions
runs `aws s3 sync` and purges the Cloudflare cache.

```
push to main ─▶ GitHub Actions (ubuntu runner)
                 │  aws s3 sync ./ → s3://tauafernandes.com.br
                 └▶ POST Cloudflare /purge_cache
visitor ─▶ Cloudflare (TLS, CDN) ─HTTP─▶ S3 website endpoint
```

> **Why the bucket is named `tauafernandes.com.br`:** Cloudflare forwards the
> visitor's `Host` header to the origin. An S3 *website* endpoint selects the
> bucket by that `Host`, so the bucket name must match the domain exactly.

## Files

| File | Purpose |
|---|---|
| `.github/workflows/deploy.yml` | CI/CD: `aws s3 sync` + Cloudflare purge (push to `main`) |

The `Dockerfile`, `docker-compose.swarm.yml` and `deploy/nginx.conf` are leftover
from the old Hetzner/Swarm setup — **no longer used** by the pipeline. Keep the
`Dockerfile` if you want `docker run` for local preview; otherwise delete all three.

## One-time AWS setup

Run locally (you already have the AWS CLI). Adjust `BUCKET`/`REGION` if you
changed them in `deploy.yml`.

```bash
BUCKET=tauafernandes.com.br
REGION=us-east-1

# 1. Create the bucket (you already did this). us-east-1 takes NO LocationConstraint;
#    for any other region add: --create-bucket-configuration LocationConstraint="$REGION"
aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"

# 2. Enable static website hosting (single-page site → 404s fall back to index)
aws s3 website "s3://$BUCKET" --index-document index.html --error-document index.html

# 3. Make objects public-readable (website endpoints require this; no OAC like CloudFront)
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-policy --bucket "$BUCKET" --policy "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{\"Sid\":\"PublicRead\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::$BUCKET/*\"}]
}"
```

Note the **website endpoint** printed by step 2 (also under S3 console →
bucket → Properties → Static website hosting), e.g.
`tauafernandes.com.br.s3-website-us-east-1.amazonaws.com`. You'll point
Cloudflare at it.

### IAM user for CI

Create a user with **only** these permissions and use its access key as the
GitHub secrets below:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::tauafernandes.com.br" },
    { "Effect": "Allow", "Action": ["s3:PutObject", "s3:DeleteObject"], "Resource": "arn:aws:s3:::tauafernandes.com.br/*" }
  ]
}
```

## GitHub Secrets

`Settings → Secrets and variables → Actions → New repository secret`:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Access key of the CI IAM user |
| `AWS_SECRET_ACCESS_KEY` | Its secret |
| `CLOUDFLARE_API_TOKEN` | Token with **Zone → Cache Purge** on `tauafernandes.com.br` (optional) |
| `CLOUDFLARE_ZONE_ID` | Zone ID (Cloudflare → Overview → API section) (optional) |

> Without the Cloudflare secrets the deploy still works — it just skips the purge,
> and the edge cache clears on its own (HTML revalidates fast; assets are immutable).

## Cloudflare setup

### 1. DNS — proxied CNAMEs to the S3 website endpoint

| Type | Name | Content | Proxy |
|---|---|---|---|
| `CNAME` | `tauafernandes.com.br` (`@`) | `tauafernandes.com.br.s3-website-us-east-1.amazonaws.com` | Proxied 🟠 |
| `CNAME` | `www` | `tauafernandes.com.br.s3-website-us-east-1.amazonaws.com` | Proxied 🟠 |

Cloudflare flattens the apex CNAME automatically. Use **your** exact endpoint
from the S3 console (the region suffix differs per region).

### 2. SSL/TLS mode: **Flexible**

`SSL/TLS → Overview → Flexible`. S3 website endpoints speak **HTTP only**, so
Cloudflare terminates HTTPS for the visitor and talks HTTP to S3. Also turn on
`SSL/TLS → Edge Certificates → Always Use HTTPS`.

> Origin leg (Cloudflare→S3) is unencrypted. Fine for a fully public static site
> with no secrets. Want end-to-end TLS? Point Cloudflare at the **REST** endpoint
> (`<bucket>.s3.<region>.amazonaws.com`, supports HTTPS) with mode **Full**, and
> add a Rule rewriting `/` → `/index.html` (REST endpoints don't serve an index
> document). More moving parts — only worth it if you need it.

### 3. Redirect `www` → apex

`www` hits the origin as `Host: www.tauafernandes.com.br`, which the bucket
doesn't match. Send it to the apex **before** it reaches S3 — `Rules → Redirect
Rules → Create`:

- **If** `Hostname equals www.tauafernandes.com.br`
- **Then** Dynamic redirect → `concat("https://tauafernandes.com.br", http.request.uri.path)`, status **301**.

## Deploy

```bash
git push origin main          # or run the workflow manually from the Actions tab
```

## Verify after deploy

```bash
curl -I https://tauafernandes.com.br          # 200, server: cloudflare
curl -I https://www.tauafernandes.com.br       # 301 → https://tauafernandes.com.br
# Direct S3 (bypasses Cloudflare) — sanity check the origin:
curl -I http://tauafernandes.com.br.s3-website-us-east-1.amazonaws.com
```

## Rollback

S3 keeps no history unless versioning is on. Simplest: `git revert` / `git checkout`
the previous commit and push — the workflow re-syncs. For instant rollback, enable
bucket versioning and restore prior object versions.
