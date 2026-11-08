FROM node:22-alpine
WORKDIR /game
COPY --chown=node:node mobile/ mobile/
COPY --chown=node:node server/server.cjs server/server.cjs
ENV HOST=0.0.0.0 PORT=8787 NODE_ENV=production
USER node
EXPOSE 8787
CMD ["node", "server/server.cjs"]
