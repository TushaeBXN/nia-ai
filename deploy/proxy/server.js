/**
 * Nia API proxy — Render.com / Fly.io deployment
 *
 * Sits between the public frontend and RunPod Serverless.
 * Handles: rate limiting, CORS, API key hiding.
 *
 * Fix #3 — /api/nia has NO cache (each situation is unique and private).
 */
"use strict";

const express     = require("express");
const helmet      = require("helmet");
const rateLimit   = require("express-rate-limit");
const cors        = require("cors");

const app = express();

// Security headers
app.use(helmet());

// Parse JSON bodies
app.use(express.json({ limit: "16kb" }));

// CORS — lock to your frontend domain in production
const allowedOrigin = process.env.ALLOWED_ORIGIN || "*";
app.use(cors({ origin: allowedOrigin }));

// Rate limit: 10 requests per minute per IP
const limiter = rateLimit({
    windowMs: 60 * 1_000,
    max: 10,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: "Too many requests — please wait a minute." },
});

// ── Env ───────────────────────────────────────────────────────────────────────

const RUNPOD_ENDPOINT = process.env.RUNPOD_ENDPOINT_URL; // e.g. https://api.runpod.io/v2/abc123
const RUNPOD_API_KEY  = process.env.RUNPOD_API_KEY;

if (!RUNPOD_ENDPOINT || !RUNPOD_API_KEY) {
    console.error("RUNPOD_ENDPOINT_URL and RUNPOD_API_KEY must be set.");
    process.exit(1);
}

// ── Routes ────────────────────────────────────────────────────────────────────

// Fix #3: NO cache — every crisis situation is personal and must not be served
// to a different user. Cache headers are explicitly set to prevent proxies and
// CDNs from storing the response.
app.post("/api/nia", limiter, async (req, res) => {
    res.set("Cache-Control", "no-store");
    res.set("Pragma", "no-cache");

    const message = (req.body?.message || "").trim();
    if (!message) {
        return res.status(400).json({ error: "message is required" });
    }

    try {
        // RunPod /runsync blocks until the job completes (up to 90s)
        const rpRes = await fetch(`${RUNPOD_ENDPOINT}/runsync`, {
            method:  "POST",
            headers: {
                "Content-Type":  "application/json",
                "Authorization": `Bearer ${RUNPOD_API_KEY}`,
            },
            body: JSON.stringify({ input: { message } }),
            signal: AbortSignal.timeout(90_000),
        });

        if (!rpRes.ok) {
            const text = await rpRes.text().catch(() => "");
            console.error(`[proxy] RunPod ${rpRes.status}:`, text.slice(0, 200));
            return res.status(502).json({ error: "Inference service error." });
        }

        const result = await rpRes.json();

        if (result.status === "TIMED_OUT" || result.status === "FAILED") {
            return res.status(504).json({ error: "Inference timed out. Please try again." });
        }

        return res.json(result.output ?? result);
    } catch (err) {
        if (err.name === "TimeoutError" || err.name === "AbortError") {
            return res.status(504).json({ error: "Request timed out." });
        }
        console.error("[proxy] Unexpected error:", err.message);
        return res.status(502).json({ error: "Inference service unavailable." });
    }
});

app.get("/health", (_req, res) => res.json({ status: "ok" }));

// ── Start ─────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.PORT || "3001", 10);
app.listen(PORT, () => console.log(`Nia proxy listening on :${PORT}`));
