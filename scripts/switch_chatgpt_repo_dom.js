(() => {
  const sourceSlugs = [
    "ds4psb/veo3-prompting",
    "ds4psb-ai/veo3-prompting",
    "veo3-prompting",
  ];
  const targetSlugs = [
    "ds4psb/komission",
    "ds4psb-ai/komission",
    "komission",
  ];

  const sleep = (ms) => {
    const end = Date.now() + ms;
    while (Date.now() < end) {}
  };

  const isLoginScreen = () => {
    const bodyText = ((document.body && document.body.innerText) || "").toLowerCase();
    if (
      bodyText.includes("log in") ||
      bodyText.includes("sign up") ||
      bodyText.includes("continue with")
    ) {
      return true;
    }
    if (document.querySelector("input[type=email], input[name*=email], input[name*=username]")) {
      return true;
    }
    return false;
  };

  const findClickableForText = (needle) => {
    const lower = needle.toLowerCase();
    const all = Array.from(document.querySelectorAll("*"));
    for (const el of all) {
      const text = (el.innerText || "").toLowerCase();
      if (!text || !text.includes(lower)) continue;
      let cur = el;
      while (cur && cur !== document.body) {
        const role = cur.getAttribute && cur.getAttribute("role");
        if (
          cur.tagName === "BUTTON" ||
          cur.tagName === "A" ||
          role === "button" ||
          role === "combobox"
        ) {
          return cur;
        }
        cur = cur.parentElement;
      }
    }
    return null;
  };

  const click = (el) => {
    if (!el) return false;
    el.scrollIntoView({ block: "center" });
    el.click();
    return true;
  };

  const setInputValue = (input, value) => {
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  };

  const findSearchInput = () => {
    return document.querySelector(
      "input[type=text], input[role=combobox], input[placeholder*='Search'], input[aria-label*='Search']"
    );
  };

  const findOption = (needle) => {
    const lower = needle.toLowerCase();
    const candidates = Array.from(
      document.querySelectorAll("[role=option], button, li, div")
    ).filter((el) => (el.innerText || "").toLowerCase().includes(lower));
    for (const el of candidates) {
      const role = el.getAttribute && el.getAttribute("role");
      if (role === "option" || el.tagName === "BUTTON" || el.tagName === "LI") return el;
      const parent = el.closest("button,[role=option],li");
      if (parent) return parent;
    }
    return null;
  };

  if (isLoginScreen()) return "login_required";

  let opened = false;
  for (const slug of sourceSlugs) {
    const el = findClickableForText(slug);
    if (el) {
      opened = click(el);
      break;
    }
  }

  if (!opened) {
    const el =
      findClickableForText("sync") ||
      findClickableForText("repository") ||
      findClickableForText("repo");
    if (el) opened = click(el);
  }

  sleep(300);

  const input = findSearchInput();
  if (input) {
    setInputValue(input, "komission");
    sleep(300);
  }

  let selected = false;
  for (const slug of targetSlugs) {
    const opt = findOption(slug);
    if (opt) {
      selected = click(opt);
      break;
    }
  }

  if (selected) return "switched_to_komission";
  if (opened) return "menu_opened_but_no_match";
  return "no_target_found";
})();
