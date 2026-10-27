import { createServer, type Server } from "node:http";
import { AddressInfo } from "node:net";
import assert from "node:assert/strict";
import { test } from "node:test";

import { HttpVerifier } from "../src/reference/index.js";

function startServer(): Promise<{ server: Server; url: string }> {
  return new Promise((resolve) => {
    const server = createServer((req, res) => {
      if (req.url === "/ok") {
        res.writeHead(200);
        res.end("flag{captured}");
      } else if (req.url === "/wrong-body") {
        res.writeHead(200);
        res.end("nothing to see here");
      } else {
        res.writeHead(404);
        res.end("not found");
      }
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address() as AddressInfo;
      resolve({ server, url: `http://127.0.0.1:${port}` });
    });
  });
}

function stopServer(server: Server): Promise<void> {
  return new Promise((resolve) => server.close(() => resolve()));
}

test("passes on matching status and body", async () => {
  const { server, url } = await startServer();
  try {
    const verifier = new HttpVerifier({ expectedStatus: 200, bodyContains: "flag{captured}" });
    const report = await verifier.run(`${url}/ok`);
    assert.equal(report.passed, true);
    assert.match(report.evidence, /flag\{captured\}/);
  } finally {
    await stopServer(server);
  }
});

test("fails on wrong status", async () => {
  const { server, url } = await startServer();
  try {
    const verifier = new HttpVerifier({ expectedStatus: 200 });
    const report = await verifier.run(`${url}/missing`);
    assert.equal(report.passed, false);
    assert.match(report.evidence, /status=404/);
  } finally {
    await stopServer(server);
  }
});

test("fails when body does not contain expected text", async () => {
  const { server, url } = await startServer();
  try {
    const verifier = new HttpVerifier({ expectedStatus: 200, bodyContains: "flag{captured}" });
    const report = await verifier.run(`${url}/wrong-body`);
    assert.equal(report.passed, false);
  } finally {
    await stopServer(server);
  }
});

test("status-only check ignores body", async () => {
  const { server, url } = await startServer();
  try {
    const verifier = new HttpVerifier({ expectedStatus: 200 });
    const report = await verifier.run(`${url}/wrong-body`);
    assert.equal(report.passed, true);
  } finally {
    await stopServer(server);
  }
});

test("fails when nothing is listening", async () => {
  const verifier = new HttpVerifier({ expectedStatus: 200, timeoutMs: 1000 });
  const report = await verifier.run("http://127.0.0.1:1/unreachable");
  assert.equal(report.passed, false);
  assert.match(report.evidence, /request failed/);
});
