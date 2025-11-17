import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 500 },
    { duration: "1m", target: 2000 },
    { duration: "30s", target: 0 },
  ],
};

export default function () {
  const res = http.get("http://localhost:8000/api/candles/AAPL?limit=200");
  check(res, {
    "status is 200": (r) => r.status === 200,
    "latency < 150ms": (r) => r.timings.duration < 150,
  });
  sleep(0.5);
}
