FROM node:20.19.4-alpine3.21



WORKDIR /app

COPY package*.json ./

RUN npm install

ADD public /app/public
ADD src /app/src
ADD tests /app/tests
COPY *.js /app/
COPY *.ts /app/
COPY tsconfig.json /app/
COPY jsconfig.json /app/

RUN npm run build

RUN npm install -g serve

CMD ["npm", "run", "serve"]

EXPOSE 8080