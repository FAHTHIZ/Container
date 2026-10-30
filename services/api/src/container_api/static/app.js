/* SPDX-License-Identifier: Apache-2.0 */
(() => {
  "use strict";

  const API = "/api/v1";
  const $ = (selector) => document.querySelector(selector);
  const state = {
    token: sessionStorage.getItem("container_access_token") || "",
    authMode: "login",
    workspaces: [],
    projects: [],
    jobs: [],
    artifacts: [],
    models: [],
    modelVersions: [],
    selectedModelId: "",
    workspaceId: "",
    projectId: "",
    streamAbort: null,
  };

  const escapeText = (value) => String(value ?? "");
  const api = async (path, options = {}) => {
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");
    if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers,
      credentials: "same-origin",
    });
    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    const body = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
    if (!response.ok) {
      const message = typeof body === "object" && body?.detail
        ? (typeof body.detail === "string" ? body.detail : "Please check the submitted information.")
        : `Request failed (${response.status}).`;
      throw new Error(message);
    }
    return body;
  };

  const setMessage = (selector, message, good = false) => {
    const node = $(selector);
    node.textContent = message || "";
    node.classList.toggle("success-message", good);
  };

  function setAuthMode(mode) {
    state.authMode = mode;
    const registering = mode === "register";
    $("#auth-title").textContent = registering ? "Create your account" : "Welcome back";
    $("#auth-subtitle").textContent = registering
      ? "Set up your account and first workspace."
      : "Sign in to open your workspace.";
    $("#display-name-wrap").hidden = !registering;
    $("#workspace-name-wrap").hidden = !registering;
    $("#display-name").required = registering;
    $("#workspace-name").required = registering;
    $("#password").autocomplete = registering ? "new-password" : "current-password";
    $("#auth-submit").innerHTML = registering ? 'Create account <span>→</span>' : 'Sign in <span>→</span>';
    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
      button.classList.toggle("active", button.dataset.authMode === mode);
    });
    setMessage("#auth-error", "");
  }

  async function handleAuth(event) {
    event.preventDefault();
    const submit = $("#auth-submit");
    submit.disabled = true;
    setMessage("#auth-error", "");
    const payload = {
      email: $("#email").value.trim(),
      password: $("#password").value,
    };
    try {
      let result;
      if (state.authMode === "register") {
        payload.display_name = $("#display-name").value.trim();
        payload.workspace_name = $("#workspace-name").value.trim();
        result = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: {"Content-Type": "application/json", "Accept": "application/json"},
          body: JSON.stringify(payload),
          credentials: "same-origin",
        });
      } else {
        result = await fetch(`${API}/auth/login`, {
          method: "POST",
          headers: {"Content-Type": "application/json", "Accept": "application/json"},
          body: JSON.stringify(payload),
          credentials: "same-origin",
        });
      }
      const data = await result.json();
      if (!result.ok) {
        const detail = typeof data.detail === "string"
          ? data.detail
          : "The account details could not be accepted.";
        throw new Error(detail);
      }
      state.token = data.access_token;
      sessionStorage.setItem("container_access_token", state.token);
      await showStudio();
    } catch (error) {
      setMessage("#auth-error", error.message || "Unable to sign in.");
    } finally {
      submit.disabled = false;
    }
  }

  function showAuthenticatedView() {
    $("#auth-panel").hidden = true;
    $("#studio-panel").hidden = true;
    $("#chat-panel").hidden = false;
    $("#signout").hidden = false;
    document.dispatchEvent(new Event("container:authenticated"));
  }

  function signOut() {
    state.streamAbort?.abort();
    state.token = "";
    state.workspaces = [];
    state.projects = [];
    state.jobs = [];
    state.artifacts = [];
    state.models = [];
    state.modelVersions = [];
    state.selectedModelId = "";
    state.workspaceId = "";
    state.projectId = "";
    sessionStorage.removeItem("container_access_token");
    localStorage.removeItem("container_conversation_id");
    document.dispatchEvent(new Event("container:signed-out"));
    $("#studio-panel").hidden = true;
    $("#chat-panel").hidden = true;
    $("#auth-panel").hidden = false;
    $("#signout").hidden = true;
    setAuthMode("login");
  }

  async function showStudio() {
    try {
      await api("/auth/me");
      showAuthenticatedView();
      // The conversation is the primary surface; workspace controls remain available in the API.
    } catch (error) {
      signOut();
      setMessage("#auth-error", error.message || "Your session expired. Please sign in again.");
    }
  }

  async function loadWorkspaces() {
    state.workspaces = await api("/workspaces");
    $("#metric-workspaces").textContent = state.workspaces.length;
    const select = $("#workspace-select");
    select.replaceChildren();
    for (const workspace of state.workspaces) {
      const option = document.createElement("option");
      option.value = workspace.id;
      option.textContent = workspace.name;
      select.append(option);
    }
    if (!state.workspaces.some((workspace) => workspace.id === state.workspaceId)) {
      state.workspaceId = state.workspaces[0]?.id || "";
    }
    select.value = state.workspaceId;
    if (state.workspaceId) await loadProjects();
    else {
      state.projects = [];
      state.projectId = "";
      renderProjects();
      renderJobs();
      renderArtifacts();
      renderModels();
      renderVersions();
    }
  }

  async function loadProjects() {
    if (!state.workspaceId) return;
    state.projects = await api(`/workspaces/${encodeURIComponent(state.workspaceId)}/projects`);
    $("#metric-projects").textContent = state.projects.length;
    if (!state.projects.some((project) => project.id === state.projectId)) {
      state.projectId = state.projects[0]?.id || "";
    }
    renderProjects();
    await loadJobs();
    await loadArtifacts();
    await loadModels();
  }

  function renderProjects() {
    const container = $("#project-list");
    container.replaceChildren();
    $("#project-count").textContent = state.projects.length;
    if (!state.projects.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No projects yet. Create one to start a run.";
      container.append(empty);
    }
    for (const project of state.projects) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `project-item${project.id === state.projectId ? " selected" : ""}`;
      const info = document.createElement("span");
      const title = document.createElement("span");
      title.className = "item-title";
      title.textContent = project.name;
      const meta = document.createElement("span");
      meta.className = "item-meta";
      meta.textContent = project.description || "No description";
      info.append(title, meta);
      const arrow = document.createElement("span");
      arrow.className = "item-meta";
      arrow.textContent = project.id === state.projectId ? "SELECTED" : "OPEN →";
      button.append(info, arrow);
      button.addEventListener("click", async () => {
        state.projectId = project.id;
        renderProjects();
        await loadJobs();
        await loadArtifacts();
        await loadModels();
      });
      container.append(button);
    }
    const selected = state.projects.find((project) => project.id === state.projectId);
    $("#selected-project-name").textContent = selected?.name || "No project selected";
    $("#new-job-form").querySelector("button").disabled = !selected;
    $("#artifact-form").querySelector("button").disabled = !selected;
    $("#artifact-file").disabled = !selected;
  }

  async function loadArtifacts() {
    state.artifacts = state.projectId
      ? await api(`/projects/${encodeURIComponent(state.projectId)}/artifacts`)
      : [];
    renderArtifacts();
    renderArtifactChoices();
    renderVersions();
  }

  function renderArtifacts() {
    const container = $("#artifact-list");
    container.replaceChildren();
    $("#artifact-count").textContent = state.artifacts.length;
    if (!state.projectId || !state.artifacts.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = state.projectId
        ? "No project assets yet. Upload a file to attach it here."
        : "Select a project to view its assets.";
      container.append(empty);
      return;
    }
    for (const artifact of state.artifacts) {
      const item = document.createElement("div");
      item.className = "artifact-item";
      const info = document.createElement("span");
      info.className = "artifact-info";
      const name = document.createElement("span");
      name.className = "artifact-name";
      name.textContent = artifact.filename;
      const meta = document.createElement("span");
      meta.className = "artifact-meta";
      meta.textContent = `${formatBytes(artifact.size_bytes)} · ${artifact.sha256.slice(0, 12)}…`;
      info.append(name, meta);
      const download = document.createElement("button");
      download.type = "button";
      download.className = "artifact-download";
      download.textContent = "Download";
      download.setAttribute("aria-label", `Download ${artifact.filename}`);
      download.addEventListener("click", () => downloadArtifact(artifact));
      item.append(info, download);
      container.append(item);
    }
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }

  async function uploadArtifact(event) {
    event.preventDefault();
    const file = $("#artifact-file").files?.[0];
    if (!state.projectId || !file) {
      setMessage("#artifact-message", "Select a project and a file first.");
      return;
    }
    const button = event.currentTarget.querySelector("button[type='submit']");
    button.disabled = true;
    setMessage("#artifact-message", "Uploading asset…", true);
    try {
      const form = new FormData();
      form.append("file", file, file.name);
      await api(`/projects/${encodeURIComponent(state.projectId)}/artifacts`, {
        method: "POST",
        body: form,
      });
      $("#artifact-file").value = "";
      await loadArtifacts();
      setMessage("#artifact-message", "Asset uploaded and linked to this project.", true);
    } catch (error) {
      setMessage("#artifact-message", error.message || "The upload failed.");
    } finally {
      button.disabled = !state.projectId;
    }
  }

  async function downloadArtifact(artifact) {
    try {
      const headers = new Headers({"Accept": "application/octet-stream"});
      headers.set("Authorization", `Bearer ${state.token}`);
      const response = await fetch(
        `${API}/artifacts/${encodeURIComponent(artifact.id)}/download`,
        {headers, credentials: "same-origin"},
      );
      if (!response.ok) {
        const contentType = response.headers.get("content-type") || "";
        const details = contentType.includes("application/json")
          ? await response.json()
          : null;
        throw new Error(details?.detail || `Download failed (${response.status}).`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = artifact.filename;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      setMessage("#artifact-message", `Downloaded ${artifact.filename}.`, true);
    } catch (error) {
      setMessage("#artifact-message", error.message || "The download failed.");
    }
  }

  async function loadModels() {
    state.models = state.projectId
      ? await api(`/projects/${encodeURIComponent(state.projectId)}/models`)
      : [];
    if (!state.models.some((model) => model.id === state.selectedModelId)) {
      state.selectedModelId = state.models[0]?.id || "";
    }
    renderModels();
    await loadModelVersions();
  }

  function renderModels() {
    const container = $("#model-list");
    container.replaceChildren();
    $("#model-count").textContent = state.models.length;
    const createButton = $("#model-form").querySelector("button[type='submit']");
    createButton.disabled = !state.projectId;
    if (!state.models.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = state.projectId
        ? "No model records in this project yet."
        : "Select a project before registering a model.";
      container.append(empty);
    }
    for (const model of state.models) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `model-item${model.id === state.selectedModelId ? " selected" : ""}`;
      const info = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = model.name;
      const meta = document.createElement("small");
      meta.textContent = model.model_family || "Family not specified";
      info.append(title, meta);
      const origin = document.createElement("em");
      origin.textContent = model.origin.toUpperCase();
      button.append(info, origin);
      button.addEventListener("click", async () => {
        state.selectedModelId = model.id;
        renderModels();
        await loadModelVersions();
      });
      container.append(button);
    }
    const selected = state.models.find((model) => model.id === state.selectedModelId);
    $("#selected-model-card").hidden = !selected;
    $("#version-form").querySelector("button").disabled = !selected;
    if (selected) {
      $("#selected-model-name").textContent = selected.name;
      $("#selected-model-origin").textContent = selected.origin.toUpperCase();
    } else {
      state.modelVersions = [];
      $("#version-count").textContent = "0";
    }
    renderArtifactChoices();
  }

  async function loadModelVersions() {
    if (!state.selectedModelId) {
      state.modelVersions = [];
      renderVersions();
      return;
    }
    state.modelVersions = await api(
      `/models/${encodeURIComponent(state.selectedModelId)}/versions`
    );
    renderVersions();
  }

  function renderVersions() {
    const container = $("#version-list");
    if (!container) return;
    container.replaceChildren();
    $("#version-count").textContent = state.modelVersions.length;
    if (!state.modelVersions.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No versions recorded for this model yet.";
      container.append(empty);
      return;
    }
    for (const version of state.modelVersions) {
      const item = document.createElement("div");
      item.className = "version-item";
      const info = document.createElement("span");
      const label = document.createElement("strong");
      label.textContent = version.version_label;
      const meta = document.createElement("small");
      const artifact = state.artifacts.find((entry) => entry.id === version.artifact_id);
      meta.textContent = [
        version.format.toUpperCase(),
        version.quantization || "No quantization specified",
        artifact ? artifact.filename : "No linked artifact",
        version.license_id || "License not recorded",
      ].join(" · ");
      info.append(label, meta);
      const tag = document.createElement("span");
      tag.className = "state-chip";
      tag.textContent = "RECORDED";
      item.append(info, tag);
      container.append(item);
    }
  }

  function renderArtifactChoices() {
    const select = $("#version-artifact");
    if (!select) return;
    const selectedValue = select.value;
    select.replaceChildren();
    const none = document.createElement("option");
    none.value = "";
    none.textContent = "No artifact attached";
    select.append(none);
    for (const artifact of state.artifacts) {
      const option = document.createElement("option");
      option.value = artifact.id;
      option.textContent = `${artifact.filename} · ${formatBytes(artifact.size_bytes)}`;
      select.append(option);
    }
    if (state.artifacts.some((artifact) => artifact.id === selectedValue)) {
      select.value = selectedValue;
    }
  }

  async function createModel(event) {
    event.preventDefault();
    if (!state.projectId) {
      setMessage("#model-message", "Select a project first.");
      return;
    }
    const button = event.currentTarget.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const model = await api(
        `/projects/${encodeURIComponent(state.projectId)}/models`,
        {
          method: "POST",
          body: JSON.stringify({
            name: $("#model-name").value.trim(),
            model_family: $("#model-family").value.trim() || null,
            origin: $("#model-origin").value,
            description: $("#model-description").value.trim() || null,
          }),
        }
      );
      state.selectedModelId = model.id;
      $("#model-form").reset();
      await loadModels();
      setMessage("#model-message", "Model record created.", true);
    } catch (error) {
      setMessage("#model-message", error.message || "Unable to register this model.");
    } finally {
      button.disabled = !state.projectId;
    }
  }

  async function createModelVersion(event) {
    event.preventDefault();
    if (!state.selectedModelId) {
      setMessage("#model-message", "Select a model first.");
      return;
    }
    const button = event.currentTarget.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const artifactId = $("#version-artifact").value;
      await api(
        `/models/${encodeURIComponent(state.selectedModelId)}/versions`,
        {
          method: "POST",
          body: JSON.stringify({
            version_label: $("#version-label").value.trim(),
            format: $("#version-format").value,
            artifact_id: artifactId || null,
            quantization: $("#version-quantization").value.trim() || null,
            license_id: $("#version-license").value.trim() || null,
            source_uri: $("#version-source").value.trim() || null,
          }),
        }
      );
      $("#version-form").reset();
      renderArtifactChoices();
      await loadModelVersions();
      setMessage("#model-message", "Version metadata recorded.", true);
    } catch (error) {
      setMessage("#model-message", error.message || "Unable to add this model version.");
    } finally {
      button.disabled = !state.selectedModelId;
    }
  }

  function renderJobs() {
    const container = $("#job-list");
    container.replaceChildren();
    if (!state.jobs.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = state.projectId ? "No runs for this project yet." : "Choose a project to view its jobs.";
      container.append(empty);
    }
    for (const job of state.jobs) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `job-item${job.id === state.selectedJobId ? " selected" : ""}`;
      const info = document.createElement("span");
      const title = document.createElement("span");
      title.className = "item-title";
      title.textContent = job.payload?.message || job.kind;
      const meta = document.createElement("span");
      meta.className = "item-meta";
      meta.textContent = `${job.kind} · ${job.progress}% · ${new Date(job.created_at).toLocaleString()}`;
      info.append(title, meta);
      const status = document.createElement("span");
      status.className = `job-status ${job.status}`;
      status.textContent = job.status.toUpperCase();
      button.append(info, status);
      button.addEventListener("click", async () => selectJob(job.id));
      container.append(button);
    }
    const active = state.jobs.filter((job) => ["queued", "running"].includes(job.status)).length;
    $("#metric-active").textContent = active;
  }

  async function loadJobs() {
    state.streamAbort?.abort();
    state.jobs = state.projectId
      ? await api(`/projects/${encodeURIComponent(state.projectId)}/jobs`)
      : [];
    renderJobs();
    const current = state.jobs[0];
    if (current) await selectJob(current.id);
    else {
      $("#selected-project-state").textContent = "WAITING";
      $("#stream-state").textContent = "IDLE";
      $("#event-lines").replaceChildren();
      const empty = document.createElement("p");
      empty.textContent = "Waiting for a job event…";
      $("#event-lines").append(empty);
    }
  }

  function appendEvent(event) {
    const lines = $("#event-lines");
    if (lines.querySelector("p")) lines.replaceChildren();
    const line = document.createElement("div");
    line.className = "event-line";
    const time = document.createElement("span");
    time.textContent = new Date(event.created_at).toLocaleTimeString();
    const name = document.createElement("b");
    name.textContent = `  ${event.event_type}`;
    const detail = document.createElement("span");
    detail.textContent = `  ${JSON.stringify(event.payload || {})}`;
    line.append(time, name, detail);
    lines.append(line);
    lines.scrollTop = lines.scrollHeight;
  }

  async function selectJob(jobId) {
    state.selectedJobId = jobId;
    state.streamAbort?.abort();
    const job = await api(`/jobs/${encodeURIComponent(jobId)}`);
    $("#selected-project-state").textContent = job.status.toUpperCase();
    renderJobs();
    $("#event-lines").replaceChildren();
    const events = await api(`/jobs/${encodeURIComponent(jobId)}/events`);
    for (const event of events) appendEvent(event);
    connectEventStream(jobId, events.at(-1)?.id || "");
  }

  async function connectEventStream(jobId, lastEventId) {
    const controller = new AbortController();
    state.streamAbort = controller;
    $("#stream-state").textContent = "CONNECTING";
    try {
      const headers = new Headers({"Accept": "text/event-stream"});
      headers.set("Authorization", `Bearer ${state.token}`);
      if (lastEventId) headers.set("Last-Event-ID", lastEventId);
      const response = await fetch(`${API}/jobs/${encodeURIComponent(jobId)}/events/stream`, {
        headers,
        signal: controller.signal,
      });
      if (!response.ok || !response.body) throw new Error("Event stream unavailable.");
      $("#stream-state").textContent = "CONNECTED";
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, {stream: true});
        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) !== -1) {
          const message = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          const dataLine = message.split("\n").find((line) => line.startsWith("data:"));
          if (!dataLine) continue;
          try {
            const event = JSON.parse(dataLine.slice(5).trim());
            appendEvent(event);
            await refreshSelectedJob(jobId);
          } catch {
            // Ignore malformed or partial server-sent event payloads.
          }
        }
      }
      $("#stream-state").textContent = "CLOSED";
    } catch (error) {
      if (error.name !== "AbortError") {
        $("#stream-state").textContent = "DISCONNECTED";
      }
    }
  }

  async function refreshSelectedJob(jobId) {
    try {
      const job = await api(`/jobs/${encodeURIComponent(jobId)}`);
      const index = state.jobs.findIndex((item) => item.id === jobId);
      if (index !== -1) state.jobs[index] = job;
      $("#selected-project-state").textContent = job.status.toUpperCase();
      renderJobs();
    } catch {
      // A transient refresh error does not terminate the visible event stream.
    }
  }

  async function createWorkspace(event) {
    event.preventDefault();
    const input = $("#new-workspace-name");
    const button = event.currentTarget.querySelector("button[type='submit']");
    button.disabled = true;
    try {
      const workspace = await api("/workspaces", {
        method: "POST",
        body: JSON.stringify({name: input.value.trim()}),
      });
      state.workspaceId = workspace.id;
      input.value = "";
      $("#new-workspace-form").hidden = true;
      await loadWorkspaces();
      setMessage("#workspace-message", "Workspace created.", true);
    } catch (error) {
      setMessage("#workspace-message", error.message);
    } finally {
      button.disabled = false;
    }
  }

  async function createProject(event) {
    event.preventDefault();
    if (!state.workspaceId) {
      setMessage("#workspace-message", "Create a workspace first.");
      return;
    }
    const input = $("#new-project-name");
    try {
      const project = await api(`/workspaces/${encodeURIComponent(state.workspaceId)}/projects`, {
        method: "POST",
        body: JSON.stringify({name: input.value.trim()}),
      });
      input.value = "";
      state.projectId = project.id;
      await loadProjects();
      setMessage("#workspace-message", "Project created.", true);
    } catch (error) {
      setMessage("#workspace-message", error.message);
    }
  }

  async function createJob(event) {
    event.preventDefault();
    if (!state.projectId) {
      setMessage("#job-message-status", "Select a project first.");
      return;
    }
    const button = event.currentTarget.querySelector("button[type='submit']");
    button.disabled = true;
    setMessage("#job-message-status", "Submitting job…", true);
    try {
      const job = await api(`/projects/${encodeURIComponent(state.projectId)}/jobs`, {
        method: "POST",
        body: JSON.stringify({kind: "demo.echo", message: $("#job-message").value.trim()}),
      });
      await loadJobs();
      await selectJob(job.id);
      setMessage("#job-message-status", "Job submitted. The worker will process it when available.", true);
    } catch (error) {
      setMessage("#job-message-status", error.message);
    } finally {
      button.disabled = false;
    }
  }

  function initialize() {
    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
      button.addEventListener("click", () => setAuthMode(button.dataset.authMode));
    });
    $("#auth-form").addEventListener("submit", handleAuth);
    $("#signout").addEventListener("click", signOut);
    $("#workspace-select").addEventListener("change", async (event) => {
      state.workspaceId = event.target.value;
      state.projectId = "";
      await loadProjects();
    });
    $("#new-workspace-toggle").addEventListener("click", () => {
      $("#new-workspace-form").hidden = !$("#new-workspace-form").hidden;
      $("#new-workspace-name").focus();
    });
    $("#cancel-workspace").addEventListener("click", () => {
      $("#new-workspace-form").hidden = true;
    });
    $("#new-workspace-form").addEventListener("submit", createWorkspace);
    $("#new-project-form").addEventListener("submit", createProject);
    $("#new-job-form").addEventListener("submit", createJob);
    $("#artifact-form").addEventListener("submit", uploadArtifact);
    $("#model-form").addEventListener("submit", createModel);
    $("#version-form").addEventListener("submit", createModelVersion);
    $("#refresh-jobs").addEventListener("click", loadJobs);
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.addEventListener("click", () => {
        const view = button.dataset.view;
        document.querySelectorAll("[data-view]").forEach((item) => item.classList.toggle("active", item === button));
        $("#page-title").textContent = view === "jobs"
          ? "Job monitor"
          : view === "projects"
            ? "Your projects"
            : view === "models"
              ? "Model registry"
              : "Your workspace.";
        $("#page-subtitle").textContent = view === "jobs"
          ? "Track execution, inspect events, and follow job state changes."
          : view === "projects"
            ? "Organize work into isolated projects within your workspace."
            : view === "models"
              ? "Catalogue model identities and version metadata linked to project assets."
              : "An operational view of your Container projects and jobs.";
        if (view === "jobs") $("#new-job-form").scrollIntoView({behavior: "smooth", block: "center"});
        if (view === "projects") $("#workspace-view").scrollIntoView({behavior: "smooth", block: "start"});
        if (view === "models") $("#model-registry-panel").scrollIntoView({behavior: "smooth", block: "start"});
      });
    });
    setAuthMode("login");
    if (state.token) showStudio();
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();
