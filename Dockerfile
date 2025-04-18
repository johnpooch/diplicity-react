FROM node:current-alpine
RUN apk add --no-cache bash

RUN mkdir -p /home/node/app
RUN chown -R node:node /home/node/app

WORKDIR /home/node/app

COPY package.json package-lock.json ./
RUN chown node:node package.json package-lock.json

RUN npm install

COPY . .

EXPOSE 5173