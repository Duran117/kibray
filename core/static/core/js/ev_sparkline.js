/**
 * EV trend sparkline renderer (Phase D follow-up).
 *
 * Zero-dependency vanilla canvas renderer for tiny SPI/CPI trend
 * sparklines on the project overview page. Activated by the presence of
 * any `<canvas data-testid="ev-sparkline-canvas">` element with JSON
 * arrays in `data-spi`, `data-cpi`, `data-ev`, `data-pv`, `data-labels`.
 *
 * Two thin lines are drawn (SPI = indigo, CPI = rose), normalised to the
 * combined min/max of both series so the visual scale is meaningful.
 * A horizontal reference line at y=1.000 (the "on-budget / on-schedule"
 * baseline) is rendered when the data range crosses it.
 *
 * No tooltips, no legend — that's what the EV card next to the canvas
 * is for. This is purely a glanceable trend.
 */
(function () {
  "use strict";

  const SPI_COLOR = "#6366f1"; // indigo-500
  const CPI_COLOR = "#f43f5e"; // rose-500
  const BASELINE_COLOR = "#cbd5e1"; // slate-300
  const PADDING = 2;

  function parseArr(canvas, attr) {
    const raw = canvas.getAttribute("data-" + attr);
    if (!raw) return null;
    try {
      const arr = JSON.parse(raw);
      if (!Array.isArray(arr)) return null;
      return arr.map((v) => parseFloat(v));
    } catch (_e) {
      return null;
    }
  }

  function drawLine(ctx, values, color, w, h, minV, maxV) {
    if (!values || values.length < 2) return;
    const n = values.length;
    const range = maxV - minV || 1;
    ctx.beginPath();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = color;
    ctx.lineJoin = "round";
    for (let i = 0; i < n; i++) {
      const x = PADDING + ((w - 2 * PADDING) * i) / (n - 1);
      const y = h - PADDING - ((h - 2 * PADDING) * (values[i] - minV)) / range;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  function renderOne(canvas) {
    const spi = parseArr(canvas, "spi");
    const cpi = parseArr(canvas, "cpi");
    if (!spi || spi.length < 2 || !cpi || cpi.length < 2) return;

    // Match canvas backing store to its CSS box (HiDPI-safe).
    const dpr = window.devicePixelRatio || 1;
    const cssW = canvas.clientWidth || 200;
    const cssH = canvas.clientHeight || 40;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssW, cssH);

    // Combined range so both series share the y-axis.
    const all = spi.concat(cpi).filter((v) => Number.isFinite(v));
    if (all.length === 0) return;
    let minV = Math.min.apply(null, all);
    let maxV = Math.max.apply(null, all);
    // Always include the 1.0 baseline if data crosses or is near it.
    if (minV > 0.95) minV = 0.95;
    if (maxV < 1.05) maxV = 1.05;

    // Baseline at y=1.0 (on-budget / on-schedule).
    if (minV <= 1.0 && maxV >= 1.0) {
      const yBase =
        cssH - PADDING - ((cssH - 2 * PADDING) * (1.0 - minV)) / (maxV - minV);
      ctx.beginPath();
      ctx.lineWidth = 1;
      ctx.strokeStyle = BASELINE_COLOR;
      ctx.setLineDash([2, 3]);
      ctx.moveTo(PADDING, yBase);
      ctx.lineTo(cssW - PADDING, yBase);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    drawLine(ctx, spi, SPI_COLOR, cssW, cssH, minV, maxV);
    drawLine(ctx, cpi, CPI_COLOR, cssW, cssH, minV, maxV);
    canvas.setAttribute("data-rendered", "1");
  }

  function renderAll() {
    const nodes = document.querySelectorAll(
      'canvas.ev-sparkline, canvas[data-testid="ev-sparkline-canvas"]'
    );
    nodes.forEach(renderOne);
  }

  // Re-render on resize (debounced) so the line tracks the card width.
  let resizeT = null;
  window.addEventListener("resize", function () {
    if (resizeT) clearTimeout(resizeT);
    resizeT = setTimeout(renderAll, 120);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderAll);
  } else {
    renderAll();
  }

  // Expose for tests / manual debugging.
  window.kibrayEvSparkline = { renderAll: renderAll, renderOne: renderOne };
})();
