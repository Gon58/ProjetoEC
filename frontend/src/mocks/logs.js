export const logs = [
  {
    id: 1,
    timestamp: "2026-03-16 10:12:05",
    source: "Steam API",
    database: "postgres",
    description: "Imported latest skin price updates for 20 items.",
  },
  {
    id: 2,
    timestamp: "2026-03-16 10:14:22",
    source: "User upload",
    database: "mongo",
    description: "Added new dataset from user CSV ingestion.",
  },
  {
    id: 3,
    timestamp: "2026-03-16 10:20:10",
    source: "Scheduled job",
    database: "postgres",
    description: "Synced daily liquidity metrics with market API.",
  },
  {
    id: 4,
    timestamp: "2026-03-16 10:33:50",
    source: "Webhook",
    database: "mongo",
    description: "Received event-driven price correction update.",
  },
];
