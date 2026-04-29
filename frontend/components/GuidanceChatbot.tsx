"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

type SuggestedAction = { label: string; href: string };
type ChatResponse = { reply: string; intent: string; suggested_actions?: SuggestedAction[] };

type ChatMessage =
  | { role: "assistant"; text: string; actions?: SuggestedAction[] }
  | { role: "user"; text: string };

function getApiBase() {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export default function GuidanceChatbot() {
  const pathname = usePathname();

  // Hard rule: do not render on admin pages, and hide on /login (admin-ish entry).
  const shouldRender = useMemo(() => {
    if (!pathname) return true;
    if (pathname === "/login") return false;
    return !pathname.startsWith("/admin");
  }, [pathname]);

  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "Hi! I can help you use the Forecast, History, downloads, and price alerts on this site. What do you want to do?",
      actions: [
        { label: "Forecast", href: "/forecast" },
        { label: "History", href: "/history" },
      ],
    },
  ]);

  const endRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [open, messages.length]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;

    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);

    try {
      const res = await fetch(`${getApiBase()}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, page: pathname || "/" }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = (await res.json()) as ChatResponse;
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: data.reply || "Sorry — I couldn’t generate a response.",
          actions: data.suggested_actions || [],
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "I couldn’t reach the help service right now. Please try again in a moment.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  if (!shouldRender) return null;

  return (
    <div style={{ position: "fixed", right: 18, bottom: 18, zIndex: 50 }}>
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          aria-label="Open help chat"
          style={{
            width: 52,
            height: 52,
            borderRadius: 999,
            border: "1px solid rgba(0, 212, 255, 0.25)",
            background: "linear-gradient(135deg, rgba(0,212,255,0.18), rgba(16,217,160,0.12))",
            color: "#EDF4FF",
            boxShadow: "0 10px 28px rgba(0,0,0,0.45)",
            cursor: "pointer",
            backdropFilter: "blur(14px)",
            fontWeight: 800,
            letterSpacing: "0.02em",
          }}
        >
          ?
        </button>
      ) : (
        <div
          role="dialog"
          aria-label="Guidance chatbot"
          style={{
            width: "min(360px, calc(100vw - 36px))",
            height: 460,
            borderRadius: 16,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(13, 21, 38, 0.92)",
            boxShadow: "0 14px 46px rgba(0,0,0,0.55)",
            overflow: "hidden",
            backdropFilter: "blur(18px)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 12px 10px",
              borderBottom: "1px solid rgba(255,255,255,0.10)",
              gap: 12,
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <div style={{ fontWeight: 800, fontSize: 13, letterSpacing: "0.02em" }}>Site Guide</div>
              <div style={{ fontSize: 11, color: "rgba(237,244,255,0.65)" }}>Public site help</div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => {
                  setMessages([
                    {
                      role: "assistant",
                      text: "Hi! I can help you use the Forecast, History, downloads, and price alerts on this site. What do you want to do?",
                      actions: [
                        { label: "Forecast", href: "/forecast" },
                        { label: "History", href: "/history" },
                      ],
                    },
                  ]);
                }}
                style={{
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "rgba(255,255,255,0.06)",
                  color: "#EDF4FF",
                  padding: "8px 10px",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Reset
              </button>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close chat"
                style={{
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "rgba(255,255,255,0.06)",
                  color: "#EDF4FF",
                  padding: "8px 10px",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Close
              </button>
            </div>
          </div>

          <div
            style={{
              flex: 1,
              padding: 12,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {messages.map((m, idx) => {
              const isUser = m.role === "user";
              return (
                <div key={idx} style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
                  <div
                    style={{
                      maxWidth: "88%",
                      borderRadius: 14,
                      padding: "10px 12px",
                      background: isUser ? "rgba(0, 212, 255, 0.16)" : "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.10)",
                      color: "#EDF4FF",
                      lineHeight: 1.45,
                      fontSize: 13,
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {m.text}
                    {"actions" in m && m.actions && m.actions.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                        {m.actions.map((a) => (
                          <Link
                            key={`${a.href}-${a.label}`}
                            href={a.href}
                            onClick={() => setOpen(false)}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              padding: "6px 10px",
                              borderRadius: 999,
                              fontSize: 12,
                              fontWeight: 700,
                              textDecoration: "none",
                              color: "#00D4FF",
                              background: "rgba(0, 212, 255, 0.08)",
                              border: "1px solid rgba(0, 212, 255, 0.18)",
                            }}
                          >
                            {a.label}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={endRef} />
          </div>

          <div style={{ padding: 12, borderTop: "1px solid rgba(255,255,255,0.10)" }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
                placeholder={busy ? "Thinking…" : "Ask about forecast, history, alerts…"}
                disabled={busy}
                style={{
                  flex: 1,
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "rgba(255,255,255,0.06)",
                  color: "#EDF4FF",
                  padding: "10px 12px",
                  outline: "none",
                  fontSize: 13,
                }}
              />
              <button
                onClick={send}
                disabled={busy || !input.trim()}
                style={{
                  borderRadius: 12,
                  border: "1px solid rgba(0, 212, 255, 0.22)",
                  background: busy ? "rgba(0, 212, 255, 0.10)" : "rgba(0, 212, 255, 0.16)",
                  color: "#EDF4FF",
                  padding: "10px 12px",
                  cursor: busy || !input.trim() ? "not-allowed" : "pointer",
                  fontSize: 13,
                  fontWeight: 800,
                  minWidth: 74,
                }}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

