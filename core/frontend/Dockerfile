# Simple nginx stage to serve MACHETE HTML
FROM nginx:alpine

# Copy MACHETE HTML file
COPY fallback.html /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
