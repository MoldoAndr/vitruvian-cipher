import express from "express";
import cors from "cors";
import pinoHttp from "pino-http";

import { loadAgents } from "./agents.mjs";

const REQUEST_TIMEOUT_MS = Number(process.env.REQUEST_TIMEOUT_MS ?? 3500);
const agents = loadAgents();

if (!agents.length) {
    console.warn("Gateway started without downstream agents configured.");
}

const app = express();

app.use(cors());
app.use(express.json({ limit: "256kb" }));
app.use(pinoHttp({
    level: process.env.LOG_LEVEL ?? "info",
    autoLogging: true
}));

app.get("/healthz", (_req, res) => {
    res.json({
        status: "ok",
        service: "cryptosystem-gateway",
        agents: agents.map((agent) => agent.name)
    });
});

app.post("/detect", async (req, res) => {
    const payload = req.body;
    const { input, operation, options } = parsePayload(payload);

    if (!input || typeof input !== "string") {
        return res.status(400).json({
            error: "invalid_input",
            message: "Body must provide text under 'input' (or 'text' / 'ciphertext') as a string."
        });
    }

    if (operation && operation !== "detect") {
        return res.status(400).json({
            error: "unsupported_operation",
            message: `Requested operation '${operation}' is not supported. Use 'detect'.`
        });
    }

    if (!agents.length) {
        return res.status(503).json({
            error: "no_agents_available",
            message: "Gateway has no downstream agents configured."
        });
    }

    const body = JSON.stringify(payload ?? { input, operation, options });
    const results = await Promise.all(agents.map((agent) => callAgent(agent, body)));

    const successes = results.filter((result) => result.ok).length;

    res.json({
        input,
        operation: operation ?? "detect",
        options,
        agents: results,
        meta: {
            totalAgents: agents.length,
            successfulAgents: successes
        }
    });
});

app.use((err, req, res, _next) => {
    req.log?.error({ err }, "Unhandled error");
    res.status(500).json({
        error: "internal_error",
        message: "Failed to process request.",
        detail: process.env.NODE_ENV === "production" ? undefined : err.message
    });
});

function parsePayload(body) {
    if (Array.isArray(body)) {
        return {
            input: body[0],
            operation: body[1],
            options: body[2]
        };
    }

    if (body && typeof body === "object") {
        return {
            input: body.input ?? body.text ?? body.ciphertext ?? null,
            operation: body.operation ?? body.action ?? body.mode ?? "detect",
            options: body.options ?? {}
        };
    }

    return { input: typeof body === "string" ? body : null, operation: "detect", options: {} };
}

async function callAgent(agent, body) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch(agent.url, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body,
            signal: controller.signal
        });

        const contentType = response.headers.get("content-type") ?? "";
        let data = null;

        if (contentType.includes("application/json")) {
            data = await response.json().catch(() => null);
        } else {
            data = await response.text().catch(() => null);
        }

        if (!response.ok) {
            return {
                name: agent.name,
                ok: false,
                status: response.status,
                error: extractErrorMessage(data),
                data: data && response.status < 500 ? data : undefined
            };
        }

        return {
            name: agent.name,
            ok: true,
            status: response.status,
            data
        };
    } catch (error) {
        return {
            name: agent.name,
            ok: false,
            status: null,
            error: error.name === "AbortError" ? "timeout" : error.message
        };
    } finally {
        clearTimeout(timeout);
    }
}

function extractErrorMessage(payload) {
    if (!payload) return "agent_error";
    if (typeof payload === "string") return payload.slice(0, 256);
    if (typeof payload === "object") {
        return payload.message ?? payload.error ?? JSON.stringify(payload).slice(0, 256);
    }
    return "agent_error";
}

export default app;

if (process.env.NODE_ENV !== "test") {
    const port = Number(process.env.PORT ?? 8090);
    app.listen(port, () => {
        console.log(`Cryptosystem gateway listening on port ${port}`);
    });
}
