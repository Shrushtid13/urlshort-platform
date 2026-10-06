// k6 load test. Build FAILS if thresholds are breached.
// Run: k6 run -e BASE_URL=http://localhost:8000 scripts/loadtest.js
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  stages: [
    { duration: "10s", target: 20 },
    { duration: "20s", target: 50 },
    { duration: "5s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],      // <1% errors
    http_req_duration: ["p(95)<400"],    // p95 under 400ms
    checks: ["rate>0.99"],
  },
};

export function setup() {
  const res = http.post(`${BASE}/api/v1/links`, JSON.stringify({ url: "https://example.com/load" }),
    { headers: { "Content-Type": "application/json" } });
  return { code: res.json("code") };
}

export default function (data) {
  const r = http.get(`${BASE}/${data.code}`, { redirects: 0 });
  check(r, { "redirect 307": (x) => x.status === 307 });
  if (Math.random() < 0.1) {
    const c = http.post(`${BASE}/api/v1/links`, JSON.stringify({ url: "https://example.com/new" }),
      { headers: { "Content-Type": "application/json" } });
    check(c, { "created 201": (x) => x.status === 201 });
  }
  sleep(0.1);
}
