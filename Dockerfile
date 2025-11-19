FROM nginx:alpine
COPY swelly-launch-static.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
