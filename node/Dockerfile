FROM node:20

WORKDIR /app
COPY package.json .
RUN npm install

COPY index.mjs .

CMD ["node", "index.mjs"]