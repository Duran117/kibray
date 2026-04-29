/* Kibray — global responsive table enhancer.
 *
 * For every <table> in the page that is not already inside a scrollable
 * container, wrap it in <div class="kb-table-scroll"> so it can scroll
 * horizontally on small screens.
 *
 * Also copies each <th> text into the matching <td>'s data-label, which
 * powers the card-layout CSS for tables marked `.kb-mobile-cards`.
 *
 * Idempotent: marks processed tables with `data-kb-resp="1"`.
 *
 * Skip rules:
 *  - Tables inside emails or PDF print templates (body has data-kb-no-resp)
 *  - Tables with class `kb-no-resp` (opt-out)
 *  - Tables already inside .table-responsive, .kb-table-scroll, or any
 *    ancestor that already has overflow-x: auto|scroll.
 */
(function () {
    "use strict";
    if (typeof document === "undefined") return;

    var SKIP_CLASSES = ["kb-no-resp"];
    var SCROLL_PARENT_SEL = ".table-responsive, .kb-table-scroll";

    function ancestorScrolls(el) {
        var node = el.parentElement;
        while (node && node !== document.body) {
            if (node.matches && node.matches(SCROLL_PARENT_SEL)) return true;
            var cs = window.getComputedStyle(node);
            var ox = cs.overflowX;
            if ((ox === "auto" || ox === "scroll") && node.clientWidth > 0) {
                return true;
            }
            node = node.parentElement;
        }
        return false;
    }

    function shouldSkip(table) {
        if (!table || table.dataset.kbResp === "1") return true;
        if (document.body && document.body.dataset.kbNoResp === "1") return true;
        for (var i = 0; i < SKIP_CLASSES.length; i++) {
            if (table.classList.contains(SKIP_CLASSES[i])) return true;
        }
        return false;
    }

    function wrap(table) {
        if (ancestorScrolls(table)) return;
        var wrapper = document.createElement("div");
        wrapper.className = "kb-table-scroll";
        var parent = table.parentNode;
        if (!parent) return;
        parent.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    }

    function labelCells(table) {
        var headRow = table.querySelector("thead tr");
        if (!headRow) return;
        var headers = [];
        headRow.querySelectorAll("th").forEach(function (th) {
            // Strip nested icons / inputs to get a clean label
            var label = (th.getAttribute("data-label") ||
                         th.textContent ||
                         "").trim().replace(/\s+/g, " ");
            headers.push(label);
        });
        if (!headers.length) return;
        table.querySelectorAll("tbody > tr").forEach(function (tr) {
            var cells = tr.children;
            for (var i = 0; i < cells.length; i++) {
                var td = cells[i];
                if (td.tagName !== "TD") continue;
                if (td.hasAttribute("colspan") &&
                    parseInt(td.getAttribute("colspan"), 10) > 1) continue;
                if (!td.hasAttribute("data-label") && headers[i]) {
                    td.setAttribute("data-label", headers[i]);
                }
            }
        });
    }

    function process(root) {
        (root || document).querySelectorAll("table").forEach(function (table) {
            if (shouldSkip(table)) return;
            wrap(table);
            labelCells(table);
            table.dataset.kbResp = "1";
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { process(document); });
    } else {
        process(document);
    }

    // Re-process tables added later (HTMX, AJAX list refreshes).
    if (typeof MutationObserver !== "undefined") {
        var obs = new MutationObserver(function (mutations) {
            for (var m = 0; m < mutations.length; m++) {
                var added = mutations[m].addedNodes;
                for (var i = 0; i < added.length; i++) {
                    var node = added[i];
                    if (node.nodeType !== 1) continue;
                    if (node.tagName === "TABLE") {
                        if (!shouldSkip(node)) {
                            wrap(node);
                            labelCells(node);
                            node.dataset.kbResp = "1";
                        }
                    } else if (node.querySelectorAll) {
                        process(node);
                    }
                }
            }
        });
        obs.observe(document.body || document.documentElement, {
            childList: true, subtree: true
        });
    }

    // Public hook for callers that want to force re-scan.
    window.kbResponsiveTables = { rescan: function () { process(document); } };
})();
