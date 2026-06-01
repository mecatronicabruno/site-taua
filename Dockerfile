# ============================================================
#  Tauá Fernandes — static site (nginx)
#  Single-stage: a tiny nginx image serving the static files.
# ============================================================
FROM nginx:1.27-alpine

# Drop the stock server block, add ours.
RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/nginx.conf /etc/nginx/conf.d/site.conf

# Static assets only (explicit copy — no source/config junk in the web root).
COPY index.html robots.txt sitemap.xml site.webmanifest /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/

EXPOSE 80

# Fail fast if the config is invalid at build time.
RUN nginx -t

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/healthz || exit 1
