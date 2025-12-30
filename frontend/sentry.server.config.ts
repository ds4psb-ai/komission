// This file configures the initialization of Sentry on the server.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
    dsn: process.env.SENTRY_DSN,

    // Only enable in production
    enabled: process.env.NODE_ENV === 'production',

    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions

    // Ignore common server-side errors
    ignoreErrors: [
        'ECONNREFUSED',
        'ETIMEDOUT',
    ],

    // Extra context
    initialScope: {
        tags: {
            app: 'komission-server',
        },
    },
});
