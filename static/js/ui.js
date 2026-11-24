// Shared page behaviour, loaded on every page by base.html:
//  - the mobile navigation menu
//  - show/hide buttons on password fields

// ---------- Mobile menu ----------
const toggle = document.querySelector(".nav__toggle");
const menu = document.getElementById("nav-menu");

if (toggle && menu) {
    const setOpen = (open) => {
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
        menu.classList.toggle("is-open", open);
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Close with the Escape key and return focus to the button.
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu.classList.contains("is-open")) {
            setOpen(false);
            toggle.focus();
        }
    });
}

// ---------- Password show/hide ----------
document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const input = document.getElementById(button.dataset.passwordToggle);
    button.addEventListener("click", () => {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        button.setAttribute("aria-pressed", String(show));
        button.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
});
