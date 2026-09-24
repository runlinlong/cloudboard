"use strict";
const byId = (id) => document.getElementById(id);
const labels = {todo: "To do", in_progress: "In progress", done: "Done"};
let loading = false;

function message(text, error = false) {
  byId("message").textContent = text;
  byId("message").className = error ? "error" : "";
}

async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers: {"Content-Type": "application/json"}, signal: AbortSignal.timeout(12000)});
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request could not be completed.");
  return data;
}

function taskCard(task) {
  const card = document.createElement("article");
  card.className = "task-card" + (task.status === "done" ? " is-done" : "");
  const top = document.createElement("div");
  top.className = "task-top";
  const badge = document.createElement("span");
  badge.className = "badge " + task.priority;
  badge.textContent = task.priority + " priority";
  const remove = document.createElement("button");
  remove.className = "delete-task";
  remove.textContent = "×";
  remove.title = "Delete task";
  remove.setAttribute("aria-label", "Delete " + task.title);
  remove.addEventListener("click", async () => {
    if (!confirm(`Delete “${task.title}”?`)) return;
    remove.disabled = true;
    try { await api(`/api/tasks/${task.id}`, {method: "DELETE"}); await load(); message("Task deleted."); }
    catch (error) { message(error.message, true); }
    finally { remove.disabled = false; }
  });
  top.append(badge, remove);
  const title = document.createElement("h4");
  title.textContent = task.title;
  const footer = document.createElement("div");
  footer.className = "task-footer";
  const date = document.createElement("time");
  date.dateTime = task.created_at;
  date.textContent = new Date(task.created_at).toLocaleDateString("en-GB", {day: "numeric", month: "short"});
  const status = document.createElement("select");
  status.setAttribute("aria-label", "Status of " + task.title);
  for (const [value, label] of Object.entries(labels)) {
    const option = document.createElement("option");
    option.value = value; option.textContent = label; option.selected = value === task.status;
    status.append(option);
  }
  status.addEventListener("change", async () => {
    status.disabled = true;
    try { await api(`/api/tasks/${task.id}`, {method: "PATCH", body: JSON.stringify({status: status.value})}); await load(); message("Task updated."); }
    catch (error) { status.value = task.status; message(error.message, true); }
    finally { status.disabled = false; }
  });
  footer.append(date, status); card.append(top, title, footer); return card;
}

async function load() {
  if (loading) return;
  loading = true; byId("refresh").disabled = true;
  try {
    const data = await api("/api/dashboard");
    byId("total").textContent = data.summary.total;
    byId("in-progress").textContent = data.summary.in_progress;
    byId("done").textContent = data.summary.done;
    byId("rate").textContent = data.summary.completion_percent + "%";
    byId("progress").value = data.summary.completion_percent;
    byId("task-count").textContent = data.summary.total;
    for (const status of Object.keys(labels)) {
      const list = byId(status + "-list"); list.replaceChildren();
      const tasks = data.tasks.filter((task) => task.status === status);
      byId(status + "-count").textContent = tasks.length;
      if (tasks.length) tasks.forEach((task) => list.append(taskCard(task)));
      else {
        const empty = document.createElement("div"); empty.className = "empty";
        const icon = document.createElement("span"); icon.textContent = status === "done" ? "✓" : "＋";
        empty.append(icon, document.createTextNode(status === "todo" ? "A fresh start. Add your first task." : status === "done" ? "Your next small win belongs here." : "Ready when you are.")); list.append(empty);
      }
    }
    byId("instances").textContent = `Dashboard instance: ${data.instances.dashboard} · Task API instance: ${data.instances.tasks}`;
    byId("sync-status").textContent = "● Synced at " + new Date().toLocaleTimeString();
  } catch (error) {
    message(error.message, true);
    byId("sync-status").textContent = "Unable to sync · press Refresh to retry";
    throw error;
  } finally { loading = false; byId("refresh").disabled = false; }
}

byId("task-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button"); button.disabled = true;
  try {
    await api("/api/tasks", {method: "POST", body: JSON.stringify({title: byId("title").value, priority: byId("priority").value})});
    byId("title").value = ""; await load(); message("Task added. One step closer."); byId("title").focus();
  } catch (error) { message(error.message, true); }
  finally { button.disabled = false; }
});
byId("refresh").addEventListener("click", () => { message(""); load().catch(() => {}); });
load().catch(() => {});
