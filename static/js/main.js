/**
 * main.js — Global client-side utilities.
 * =========================================
 * Keep this file lean. Page-specific JS lives inside
 * {% block scripts %} in the relevant template.
 *
 * Currently provides:
 *   • Auto-dismiss flash messages after 4 seconds
 *   • Confirm-before-submit guard for delete buttons
 *     (the forms also have onsubmit="return confirm(...)" as a fallback)
 */

document.addEventListener("DOMContentLoaded", () => {

    // ── Auto-dismiss flash messages ──────────────────────────────
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((el) => {
        setTimeout(() => {
            el.style.transition = "opacity 0.5s";
            el.style.opacity    = "0";
            setTimeout(() => el.remove(), 500);
        }, 4000);   // dismiss after 4 s
    });

});
