# Nik_kiT web (ui) image (P0). nginx serving a placeholder that proxies /api → app.
# In P5 this image will serve the real Expo web build instead of the placeholder.
FROM nginx:1.27-alpine

COPY infra/ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY infra/ui/html/ /usr/share/nginx/html/
