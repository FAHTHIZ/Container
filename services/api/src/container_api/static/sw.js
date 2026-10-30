/* SPDX-License-Identifier: Apache-2.0 */
const CACHE = "container-shell-v1";
const SHELL = [
  "/studio",
  "/manifest.webmanifest",
  "/studio-assets/app.css",
  "/studio-assets/app.js",
  "/studio-assets/chat.js",
  "/studio-assets/pwa.js",
  "/studio-assets/icon.svg"
];
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  if (!SHELL.includes(url.pathname)) return;
  event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});
