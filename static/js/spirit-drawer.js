/**
 * Side drawer for landing «spirit» cards (ayah / hadith / adhkar).
 * Opens via fixed tab, teaser button, or URL hash #adhkar.
 */
(function () {
  var root = document.querySelector("[data-spirit-drawer-root]");
  if (!root) return;

  var panel = root.querySelector("#spirit-drawer-panel");
  var backdrop = root.querySelector(".spirit-drawer-backdrop");
  var tab = root.querySelector("#spirit-drawer-tab");
  var openers = document.querySelectorAll("[data-spirit-open]");
  var closers = root.querySelectorAll("[data-spirit-close]");
  var closeBtn = root.querySelector(".spirit-drawer-close");

  function setOpen(open) {
    root.classList.toggle("is-open", open);
    document.body.classList.toggle("spirit-drawer-lock", open);
    if (panel) {
      panel.setAttribute("aria-hidden", open ? "false" : "true");
    }
    if (backdrop) {
      backdrop.setAttribute("aria-hidden", open ? "false" : "true");
    }
    if (tab) {
      tab.setAttribute("aria-expanded", open ? "true" : "false");
    }
    if (open && closeBtn) {
      try {
        closeBtn.focus();
      } catch (e) {}
    }
  }

  function openDrawer() {
    setOpen(true);
  }

  function closeDrawer() {
    setOpen(false);
    if (window.location.hash === "#adhkar") {
      try {
        history.replaceState(null, "", window.location.pathname + window.location.search);
      } catch (e) {}
    }
  }

  function maybeOpenFromHash() {
    if (window.location.hash === "#adhkar") {
      openDrawer();
      var anchor = document.getElementById("adhkar");
      if (anchor) {
        anchor.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }

  openers.forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      openDrawer();
    });
  });

  closers.forEach(function (el) {
    el.addEventListener("click", function () {
      closeDrawer();
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && root.classList.contains("is-open")) {
      closeDrawer();
    }
  });

  window.addEventListener("hashchange", maybeOpenFromHash);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", maybeOpenFromHash);
  } else {
    maybeOpenFromHash();
  }
})();
