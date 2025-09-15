FROM node:20.19.4-alpine3.21 AS build

ARG ENVIRONMENT_NAME
ENV ENVIRONMENT_NAME=$ENVIRONMENT_NAME

WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./
RUN npm install

# Copy only the necessary folders and files for the Vue app
ADD public /app/public
ADD src /app/src
ADD tests /app/tests
COPY *.js /app/
COPY *.ts /app/
COPY tsconfig.json /app/
COPY jsconfig.json /app/

# Remove previous .env file if it exists
RUN rm -f .env && echo "Removed previous .env file"

# Configure environment
COPY .env.$ENVIRONMENT_NAME .env
RUN echo "Copying .env.$ENVIRONMENT_NAME to .env"

# Remove comments from the .env file and export variables
RUN sed -i '/^#/d' .env && export $(cat .env | xargs)

# Show the contend of .env file
RUN cat .env

RUN source .env && echo "ENVIRONMENT_NAME is $ENVIRONMENT_NAME and NODE_ENV is $NODE_ENV" && npm run build

# Stage 2: Production with Brotli-enabled Nginx
FROM fholzer/nginx-brotli:v1.24.0

# Copy built files and configuration
COPY --from=build /app/dist /usr/share/nginx/html
COPY ./compose/production/vue3/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

ENTRYPOINT ["nginx"]

CMD ["-g", "daemon off;"]