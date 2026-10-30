/* SPDX-License-Identifier: Apache-2.0 */
(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  let history = [];
  let conversationId = "";
  let busy = false;
  let inspectedModel = null;

  const token = () => sessionStorage.getItem("container_access_token") || "";
  const headers = () => ({
    Authorization: `Bearer ${token()}`,
    "Content-Type": "application/json",
    Accept: "application/json",
  });

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

  function showWelcome() {
    $("#chat-messages").replaceChildren();
    const card = document.createElement("div");
    card.className = "welcome-card";
    const mark = document.createElement("span");
    mark.className = "welcome-mark";
    mark.textContent = "C";
    const title = document.createElement("h2");
    title.textContent = "Your facility is ready.";
    const detail = document.createElement("p");
    detail.textContent = "Ask a question, inspect a model repository, or start a new conversation.";
    card.append(mark, title, detail);
    $("#chat-messages").append(card);
  }

  async function readJson(response) {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string" ? data.detail : `Request failed (${response.status}).`,
      );
    }
    return data;
  }

  async function refreshStatus() {
    if (!token()) return;
    try {
      const response = await fetch("/api/v1/chat/status", {headers: headers()});
      const data = await readJson(response);
      $("#chat-connection").textContent = data.configured
        ? `Connected · ${data.model}`
        : "Intelligence not connected";
      $("#core-status").textContent = data.configured
        ? "Intelligence connected"
        : "Awaiting inference connection";
      $("#core-model").textContent = data.model || "Not configured";
    } catch {
      $("#chat-connection").textContent = "Connection unavailable";
      $("#core-status").textContent = "Status unavailable";
    }
  }

  async function restoreConversation() {
    if (!token()) return;
    try {
      const conversationsResponse = await fetch(
        "/api/v1/chat/conversations",
        {headers: headers()},
      );
      const conversations = await readJson(conversationsResponse);
      if (!Array.isArray(conversations) || conversations.length === 0) {
        conversationId = "";
        history = [];
        localStorage.removeItem("container_conversation_id");
        showWelcome();
        return;
      }

      const rememberedId = localStorage.getItem("container_conversation_id") || "";
      conversationId = conversations.some((item) => item.id === rememberedId)
        ? rememberedId
        : conversations[0].id;
      localStorage.setItem("container_conversation_id", conversationId);

      const messagesResponse = await fetch(
        `/api/v1/chat/conversations/${encodeURIComponent(conversationId)}/messages`,
        {headers: headers()},
      );
      const messages = await readJson(messagesResponse);
      history = messages.map((message) => ({
        role: message.role,
        content: message.content,
      }));
      $("#chat-messages").replaceChildren();
      for (const message of history) append(message.role, message.content);
      if (history.length === 0) showWelcome();
    } catch (error) {
      append("assistant", error.message || "Could not restore conversation history.", true);
    }
  }

  async function send(event) {
    event.preventDefault();
    if (busy) return;
    const input = $("#chat-input");
    const content = input.value.trim();
    if (!content) return;

    const userMessage = {role: "user", content};
    history.push(userMessage);
    append("user", content);
    input.value = "";
    busy = true;
    $("#chat-send").disabled = true;
    const pending = append("assistant", "Connecting to Container Intelligence…");

    try {
      const response = await fetch("/api/v1/chat/completions", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          conversation_id: conversationId || null,
          messages: [{role: "user", content}],
        }),
      });
      const data = await readJson(response);
      conversationId = data.conversation_id;
      localStorage.setItem("container_conversation_id", conversationId);
      history.push(data.message);
      pending.textContent = data.message.content;
    } catch (error) {
      history.pop();
      pending.textContent = error.message || "The request could not be completed.";
      pending.parentElement.classList.add("error");
    } finally {
      busy = false;
      $("#chat-send").disabled = false;
      input.focus();
      refreshStatus();
    }
  }

  function newConversation() {
    if (busy) return;
    conversationId = "";
    history = [];
    localStorage.removeItem("container_conversation_id");
    showWelcome();
    $("#chat-input").focus();
  }

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
        method: "POST",
        headers: headers(),
        body: JSON.stringify({url: $("#model-url-input").value.trim()}),
      });
      const data = await readJson(response);
      inspectedModel = data;
      output.replaceChildren();

      const title = document.createElement("strong");
      title.textContent = data.model_id;
      const detail = document.createElement("p");
      detail.textContent = [
        data.pipeline_tag || "Unknown task",
        data.library_name || "Unknown library",
        data.license || "License not identified",
        `${data.file_count} repository files`,
      ].join(" · ");
      const note = document.createElement("p");
      note.textContent = data.note;
      const register = document.createElement("button");
      register.type = "button";
      register.className = "primary-button";
      register.textContent = "Add model to my facility";
      register.addEventListener("click", () => registerInspectedModel(data, output, register));
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

  async function registerInspectedModel(modelInfo, output, button) {
    button.disabled = true;
    try {
      const workspacesResponse = await fetch("/api/v1/workspaces", {headers: headers()});
      const workspaces = await readJson(workspacesResponse);
      if (!workspaces.length) throw new Error("Create a workspace before adding a model.");

      const projectsResponse = await fetch(
        `/api/v1/workspaces/${encodeURIComponent(workspaces[0].id)}/projects`,
        {headers: headers()},
      );
      let projects = await readJson(projectsResponse);
      if (!projects.length) {
        const createdResponse = await fetch(
          `/api/v1/workspaces/${encodeURIComponent(workspaces[0].id)}/projects`,
          {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({
              name: "My Models",
              description: "Models registered in this Container facility.",
            }),
          },
        );
        projects = [await readJson(createdResponse)];
      }

      const modelResponse = await fetch(
        `/api/v1/projects/${encodeURIComponent(projects[0].id)}/models`,
        {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            name: modelInfo.name,
            model_family: modelInfo.library_name || null,
            origin: "imported",
            description: `Source: ${modelInfo.model_id}`,
          }),
        },
      );
      const model = await readJson(modelResponse);
      const versionResponse = await fetch(
        `/api/v1/models/${encodeURIComponent(model.id)}/versions`,
        {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            version_label: "source",
            format: "other",
            source_uri: `https://huggingface.co/${modelInfo.model_id}`,
            license_id: modelInfo.license || null,
            details: {
              pipeline_tag: modelInfo.pipeline_tag,
              library_name: modelInfo.library_name,
              file_count: modelInfo.file_count,
            },
          }),
        },
      );
      await readJson(versionResponse);
      output.replaceChildren();
      const done = document.createElement("p");
      done.textContent = "Model source added. Its files have not been downloaded or executed.";
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
    $("#chat-form").addEventListener("submit", send);
    $("#chat-input").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        $("#chat-form").requestSubmit();
      }
    });
    $("#new-chat").addEventListener("click", newConversation);
    $("#core-toggle").addEventListener("click", () => {
      const panel = $("#core-panel");
      panel.hidden = !panel.hidden;
      $("#core-toggle").setAttribute("aria-expanded", String(!panel.hidden));
    });
    $("#attach-model").addEventListener("click", () => {
      $("#model-url-form").hidden = false;
      $("#model-url-input").focus();
    });
    $("#close-model-url").addEventListener("click", () => {
      $("#model-url-form").hidden = true;
    });
    $("#model-url-form").addEventListener("submit", inspectModel);

    document.addEventListener("container:authenticated", () => {
      refreshStatus();
      restoreConversation();
    });
    document.addEventListener("container:signed-out", () => {
      conversationId = "";
      history = [];
      showWelcome();
    });
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();
