FROM node:18-slim AS runtime

ENV NODE_ENV=production \
    PORT=8090

WORKDIR /usr/src/app

COPY package.json package-lock.json ./

RUN npm ci --omit=dev && npm cache clean --force

COPY src ./src

EXPOSE 8090

CMD ["node", "src/server.mjs"]
