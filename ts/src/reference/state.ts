import { existsSync, readFileSync, writeFileSync } from "node:fs";
import type { StateRecord, StateStore } from "../state.js";

interface StoredFile {
  records: StateRecord[];
  checkpoints: Record<string, string>;
}

/**
 * Minimal StateStore backed by a single JSON file.
 *
 * Not meant for production use — it exists so the HCP interfaces have a
 * working implementation to test against and to copy from, and its JSON
 * shape is the same as the Python reference SDK's `JsonFileStateStore`.
 */
export class JsonFileStateStore implements StateStore {
  private readonly path: string;

  constructor(path: string) {
    this.path = path;
    if (!existsSync(path)) {
      this.save({ records: [], checkpoints: {} });
    }
  }

  private load(): StoredFile {
    return JSON.parse(readFileSync(this.path, "utf-8")) as StoredFile;
  }

  private save(data: StoredFile): void {
    writeFileSync(this.path, JSON.stringify(data, null, 2));
  }

  read(key: string): StateRecord | null {
    const records = this.load().records.filter((r) => r.key === key);
    return records.length > 0 ? records[records.length - 1] : null;
  }

  write(key: string, value: unknown, by: string): StateRecord {
    const record: StateRecord = { key, value, by, at: new Date().toISOString() };
    const data = this.load();
    data.records.push(record);
    this.save(data);
    return record;
  }

  history(key: string): StateRecord[] {
    return this.load().records.filter((r) => r.key === key);
  }

  checkpoint(label: string): string {
    const data = this.load();
    const existing = data.checkpoints[label];
    if (existing !== undefined) {
      return existing;
    }
    const checkpointId = `${label}-${Object.keys(data.checkpoints).length}`;
    data.checkpoints[label] = checkpointId;
    this.save(data);
    return checkpointId;
  }
}
