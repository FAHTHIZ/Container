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
  let inspectedModel = null;
  async function inspectModel(event) {
    event.preventDefault();
    const output = $("#model-url-result");
    output.replaceChildren();
    const submit = event.currentTarget.querySelector("button[type='submit']");
    submit.disabled = true;
    const statusLine = document.createElement("p");
    statusLine.textContent = "Inspecting repository metadata…";
    output.append(statusLine);
    try {
      const response = await fetch("/api/v1/model-sources/inspect", {
        method:"POST", headers:headers(),
        body:JSON.stringify({url:$("#model-url-input").value.trim()})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not inspect this repository.");
      inspectedModel = data;
      output.replaceChildren();
      const title = document.createElement("strong");
      title.textContent = data.model_id;
      const detail = document.createElement("p");
      detail.textContent = [data.pipeline_tag || "Unknown task", data.library_name || "Unknown library", data.license || "License not identified", `${data.file_count} repository files`].join(" · ");
      const note = document.createElement("p");
      note.textContent = data.note;
      const register = document.createElement("button");
      register.type = "button";
      register.className = "primary-button";
      register.textContent = "Add model to my facility";
      register.addEventListener("click", registerInspectedModel);
      output.append(title, detail, note, register);
    } catch (error) {
      output.replaceChildren();
      const message = document.createElement("p");
      message.className = "form-message";
      message.textContent = error.message;
      output.append(message);
    } finally {
      submit.disabled = false;
    }
  }
  async function registerInspectedModel() {
    if (!inspectedModel) return;
    const output = $("#model-url-result");
    const button = output.querySelector("button");
    button.disabled = true;
    try {
      const workspaces = await (await fetch("/api/v1/workspaces", {headers:headers()})).json();
      if (!Array.isArray(workspaces) || !workspaces.length) throw new Error("Create a workspace before adding a model.");
      let projects = await (await fetch(`/api/v1/workspaces/${encodeURIComponent(workspaces[0].id)}/projects`, {headers:headers()})).json();
      if (!projects.length) {
        const created = await fetch(`/api/v1/workspaces/${encodeURIComponent(workspaces[0].id)}/projects`, {
          method:"POST", headers:headers(), body:JSON.stringify({name:"My Models",description:"Models imported into this Container facility."})
        });
        if (!created.ok) throw new Error("Could not create a model project.");
        projects = [await created.json()];
      }
      const createdModel = await fetch(`/api/v1/projects/${encodeURIComponent(projects[0].id)}/models`, {
        method:"POST", headers:headers(),
        body:JSON.stringify({name:inspectedModel.name,model_family:inspectedModel.library_name || null,origin:"imported",description:`Imported source: ${inspectedModel.model_id}`})
      });
      const model = await createdModel.json();
      if (!createdModel.ok) throw new Error(model.detail || "Could not register this model.");
      const versionResponse = await fetch(`/api/v1/models/${encodeURIComponent(model.id)}/versions`, {
        method:"POST", headers:headers(),
        body:JSON.stringify({version_label:"source",format:"other",source_uri:`https://huggingface.co/${inspectedModel.model_id}`,license_id:inspectedModel.license || null,details:{pipeline_tag:inspectedModel.pipeline_tag,library_name:inspectedModel.library_name,file_count:inspectedModel.file_count}})
      });
      if (!versionResponse.ok) throw new Error("The model record was created, but its source version could not be saved.");
      output.replaceChildren();
      const done = document.createElement("p");
      done.textContent = "Model source added to your facility. We have not downloaded or run its files; the next step is secure weight import and runtime compatibility checks.";
      output.append(done);
    } catch (error) {
      const message = document.createElement("p");
      message.className = "form-message";
      message.textContent = error.message;
      output.append(message);
      button.disabled = false;
    }
  }
  function initialize() {
    if (!$("#chat-form")) return;
    $("#chat-form").addEventListener("submit", send);\n    $("#attach-model").addEventListener("click", () => { $("#model-url-form").hidden = false; $("#model-url-input").focus(); });\n    $("#close-model-url").addEventListener("click", () => { $("#model-url-form").hidden = true; });\n    $("#model-url-form").addEventListener("submit", inspectModel);
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
