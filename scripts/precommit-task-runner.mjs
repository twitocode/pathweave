import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execSync, spawnSync } from "node:child_process";
import picomatch from "picomatch";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const configPath = path.join(repoRoot, "precommit.tasks.json");
const runAll = process.argv.includes("--all");

function getStagedFiles() {
  if (runAll) {
    return [];
  }
  const output = execSync("git diff --cached --name-only --diff-filter=ACMR", {
    cwd: repoRoot,
    encoding: "utf8",
  });
  return output
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function shouldRunTask(task, stagedFiles) {
  if (runAll) {
    return true;
  }
  const include = task.include ?? [];
  if (include.length === 0) {
    return true;
  }
  const matcher = picomatch(include, { dot: true });
  return stagedFiles.some((file) => matcher(file));
}

function runTask(task) {
  const taskCwd = task.cwd ? path.join(repoRoot, task.cwd) : repoRoot;
  const args = Array.isArray(task.args) ? task.args : [];
  console.log(`\n▶ ${task.name}`);
  const result = spawnSync(task.command, args, {
    cwd: taskCwd,
    stdio: "inherit",
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

const config = JSON.parse(readFileSync(configPath, "utf8"));
const tasks = Array.isArray(config.tasks) ? config.tasks : [];
const stagedFiles = getStagedFiles();

if (!runAll && stagedFiles.length === 0) {
  console.log("No staged files detected. Skipping pre-commit tasks.");
  process.exit(0);
}

const matchingTasks = tasks.filter((task) => shouldRunTask(task, stagedFiles));

if (matchingTasks.length === 0) {
  console.log("No matching tasks for staged files.");
  process.exit(0);
}

for (const task of matchingTasks) {
  runTask(task);
}

console.log("\nAll pre-commit tasks passed.");
