# --- Stage 1: build the SPA ---------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# At build time the API URL is baked into the bundle (Vite env var).
# Production-mounted apps inside VK iframes hit /api on the same origin,
# so default to relative ("" → same origin) and let nginx proxy /api.
ARG VITE_API_URL=""
ARG VITE_MOCK_LAUNCH_PARAMS="true"
ENV VITE_API_URL=$VITE_API_URL \
    VITE_MOCK_LAUNCH_PARAMS=$VITE_MOCK_LAUNCH_PARAMS

COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# --- Stage 2: serve static via nginx ------------------------------------------
FROM nginx:1.27-alpine

# Remove default nginx welcome page and config.
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/miniapp.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
