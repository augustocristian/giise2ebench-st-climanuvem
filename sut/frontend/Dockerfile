FROM node:22-alpine

WORKDIR /app

ARG EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
ARG EXPO_PUBLIC_DEFAULT_LANGUAGE=es
ARG EXPO_PUBLIC_TEST_MODE=false
ENV EXPO_PUBLIC_BACKEND_URL=${EXPO_PUBLIC_BACKEND_URL}
ENV EXPO_PUBLIC_DEFAULT_LANGUAGE=${EXPO_PUBLIC_DEFAULT_LANGUAGE}
ENV EXPO_PUBLIC_TEST_MODE=${EXPO_PUBLIC_TEST_MODE}
ENV CI=1

COPY package.json package-lock.json ./
RUN npm ci \
    && chown -R node:node /app

COPY --chown=node:node app ./app
COPY --chown=node:node assets ./assets
COPY --chown=node:node components ./components
COPY --chown=node:node constants ./constants
COPY --chown=node:node hooks ./hooks
COPY --chown=node:node src ./src
COPY --chown=node:node app.json tsconfig.json ./

USER node

EXPOSE 8081

CMD ["npx", "expo", "start", "--web", "--host", "lan"]
