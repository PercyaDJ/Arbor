# ARBOR Frontend
# Build multi-stage : Node pour le build, Nginx pour servir

# --- Stage 1 : Build ---
FROM node:20-alpine AS build

WORKDIR /app

# Installer les dépendances
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copier le code source et builder
COPY . .
RUN npm run build

# --- Stage 2 : Serve avec Nginx ---
FROM nginx:alpine

# Copier la config Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copier les fichiers buildés
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
