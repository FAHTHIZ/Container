/* SPDX-License-Identifier: Apache-2.0 */
(() => {
  if ("serviceWorker" in navigator && window.location.protocol === "https:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }
})();
