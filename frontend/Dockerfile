# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG VITE_BACKEND_HTTP=http://localhost:8000
ARG VITE_BACKEND_WS=ws://localhost:8000
ENV VITE_BACKEND_HTTP=${VITE_BACKEND_HTTP}
ENV VITE_BACKEND_WS=${VITE_BACKEND_WS}
RUN npm run build

# --- serve stage ---
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
