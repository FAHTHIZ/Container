/* SPDX-License-Identifier: Apache-2.0 */
(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const history = [];
  let busy = false;
  const token = () => sessionStorage.getItem("container_access_token") || "";
  const headers = () => ({Authorization: `Bearer ${token()}`, "Content-Type": "application/json"});
  function append(role, content, failed = false) {
    const article = document.createElement("article");
    article.className = `chat-message ${role}${failed ? " error" : ""}`;
    const label = document.createElement("span");
    label.className = "chat-role";
    label.textContent = role === "user" ? "YOU" : "CONTAINER";
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = content;
    article.append(label, bubble);
    $("#chat-messages").append(article);
    $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
    return bubble;
  }
  async function status() {
    if (!token()) return;
    try {
      const response = await fetch("/api/v1/chat/status", {headers: headers()});
      const data = await response.json();
      $("#chat-connection").textContent = data.configured ? `Connected · ${data.model}` : "Intelligence not connected";
      $("#core-status").textContent = data.configured ? "Intelligence connected" : "Awaiting inference connection";
      $("#core-model").textContent = data.model || "Not configured";
    } catch {
      $("#chat-connection").textContent = "Connection unavailable";
      $("#core-status").textContent = "Status unavailable";
    }
  }
  async function send(event) {
    event.preventDefault();
    if (busy) return;
    const input = $("#chat-input");
    const content = input.value.trim();
    if (!content) return;
    history.push({role:"user", content});
    append("user", content);
    input.value = "";
    busy = true;
    $("#chat-send").disabled = true;
    const pending = append("assistant", "Connecting to Container Intelligence…");
    try {
      const response = await fetch("/api/v1/chat/completions", {
        method:"POST", headers:headers(), body:JSON.stringify({messages:history})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status}).`);
      history.push(data.message);
      pending.textContent = data.message.content;
    } catch (error) {
      pending.textContent = error.message || "The request could not be completed.";
      pending.parentElement.classList.add("error");
    } finally {
      busy = false;
      $("#chat-send").disabled = false;
      input.focus();
      status();
    }
  }
  function initialize() {
    if (!$("#chat-form")) return;
    $("#chat-form").addEventListener("submit", send);
    $("#chat-input").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); $("#chat-form").requestSubmit(); }
    });
    $("#core-toggle").addEventListener("click", () => {
      const panel = $("#core-panel");
      panel.hidden = !panel.hidden;
      $("#core-toggle").setAttribute("aria-expanded", String(!panel.hidden));
    });
    document.addEventListener("container:authenticated", status);
    status();
  }
  document.addEventListener("DOMContentLoaded", initialize);
})();
