FROM node:26-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund && npm cache clean --force


FROM node:26-alpine

WORKDIR /app

ARG EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
ARG EXPO_PUBLIC_DEFAULT_LANGUAGE=es
ARG EXPO_PUBLIC_TEST_MODE=false
ENV EXPO_PUBLIC_BACKEND_URL=${EXPO_PUBLIC_BACKEND_URL}
ENV EXPO_PUBLIC_DEFAULT_LANGUAGE=${EXPO_PUBLIC_DEFAULT_LANGUAGE}
ENV EXPO_PUBLIC_TEST_MODE=${EXPO_PUBLIC_TEST_MODE}
ENV CI=1

COPY --from=deps --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node package.json package-lock.json ./
COPY --chown=node:node app ./app
COPY --chown=node:node assets ./assets
COPY --chown=node:node components ./components
COPY --chown=node:node hooks ./hooks
COPY --chown=node:node src ./src
COPY --chown=node:node app.json tsconfig.json ./

RUN chown node:node /app

USER node

EXPOSE 8081

CMD ["npx", "expo", "start", "--web", "--host", "lan"]
