# Dockerfile for CO2Ops AWS Sustainability Frontend Console
FROM nginx:alpine

# Install gettext (for envsubst) and curl
RUN apk add --no-cache gettext curl

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend static assets (HTML, JS, CSS, images)
COPY . /usr/share/nginx/html/

# Ensure entrypoint is executable and has unix line endings
RUN sed -i 's/\r$//' /usr/share/nginx/html/entrypoint.sh && \
    chmod +x /usr/share/nginx/html/entrypoint.sh

# Expose standard HTTP port
EXPOSE 80

# Run entrypoint to render env.js and start nginx
ENTRYPOINT ["/usr/share/nginx/html/entrypoint.sh"]