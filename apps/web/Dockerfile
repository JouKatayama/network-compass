FROM node:24-bookworm-slim@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03 AS base

ENV NEXT_TELEMETRY_DISABLED=1 \
    PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable && corepack prepare pnpm@10.34.5 --activate

FROM base AS dependencies

WORKDIR /workspace

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile --filter @network-compass/web...

FROM dependencies AS builder

COPY apps/web ./apps/web
RUN pnpm --filter @network-compass/web build

FROM base AS runner

ENV NODE_ENV=production

WORKDIR /workspace

COPY --from=builder /workspace/package.json ./package.json
COPY --from=builder /workspace/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=builder /workspace/node_modules ./node_modules
COPY --from=builder /workspace/apps/web ./apps/web

EXPOSE 3000

CMD ["pnpm", "--filter", "@network-compass/web", "start"]
