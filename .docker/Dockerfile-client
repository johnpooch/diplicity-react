FROM node:current-alpine
RUN apk add --no-cache bash

RUN mkdir -p /app
RUN chown -R node:node /app

WORKDIR /app

COPY package.json package-lock.json ./
RUN chown node:node package.json package-lock.json

RUN npm install

COPY . .

EXPOSE 5173