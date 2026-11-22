FROM node:22-alpine

ARG FIREBASE_TOOLS_VERSION=15.37.0
RUN npm install --global --no-audit --no-fund "firebase-tools@${FIREBASE_TOOLS_VERSION}" \
    && npm cache clean --force

WORKDIR /home/node
COPY --chown=node:node firebase.json ./

USER node

EXPOSE 9099 4000

CMD ["firebase", "emulators:start", "--only", "auth,ui", "--project", "demo-climanuvem"]
