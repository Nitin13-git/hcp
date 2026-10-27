// Step 2 of the interop proof: a Node-driven process resumes the SAME
// session a Python process started — using nothing but the session id
// and the shared state file. Reads Python's write to prove it's readable,
// then continues the session: writes its own finding, checkpoints again.

import { JsonFileStateStore, FileLifecycle, resume } from "../ts/dist/src/reference/index.js";

const [, , statePath, sessionId] = process.argv;
if (!statePath || !sessionId) {
  console.error("usage: node 02_node_continue.mjs <state-path> <session-id>");
  process.exit(1);
}

const EXPECTED_TASK = "cross-language interop proof: recon then verify";

const state = new JsonFileStateStore(statePath);
const lifecycle = new FileLifecycle(state);

const handle = resume(state, sessionId);
if (handle.task !== EXPECTED_TASK) {
  throw new Error(
    `resume() read back the wrong task from Python-written state: ${JSON.stringify(handle.task)}`,
  );
}

const pythonFinding = state.read("finding:1");
if (pythonFinding === null || pythonFinding.value.source !== "python") {
  throw new Error("could not read Python's finding:1 record from the shared state file");
}

state.write(
  "finding:2",
  { source: "typescript", detail: "exploit attempt succeeded" },
  "node-session",
);
const checkpointId = lifecycle.checkpoint(handle);

console.log(
  `node resumed session ${handle.session_id} (task: "${handle.task}"), ` +
    `read Python's finding:1, wrote finding:2, checkpoint ${checkpointId}`,
);
