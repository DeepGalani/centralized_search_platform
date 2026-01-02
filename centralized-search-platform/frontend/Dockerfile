FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Expose Vite default port
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
