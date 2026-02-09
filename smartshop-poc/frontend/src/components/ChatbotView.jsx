import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

const LS_KEY = "smartshop_chatbot_ui_v2";
const DEFAULT_POS = { right: 18, bottom: 18 };
const DEFAULT_SIZE = { w: 420, h: 580 };

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

export default function ChatbotView() {
  const { user } = useAuth(); // ✅ watch login/logout

  // ---------- persisted UI state ----------
  const persisted = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem(LS_KEY) || "{}");
    } catch {
      return {};
    }
  }, []);

  const [minimized, setMinimized] = useState(
    typeof persisted.minimized === "boolean" ? persisted.minimized : true
  );

  const [pos, setPos] = useState({
    right: typeof persisted.right === "number" ? persisted.right : 18,
    bottom: typeof persisted.bottom === "number" ? persisted.bottom : 18,
  });

  const [size, setSize] = useState({
    w: typeof persisted.w === "number" ? persisted.w : 420,
    h: typeof persisted.h === "number" ? persisted.h : 580,
  });

  const [vw, setVw] = useState(window.innerWidth);
  const [vh, setVh] = useState(window.innerHeight);

  useEffect(() => {
    const onResize = () => {
      setVw(window.innerWidth);
      setVh(window.innerHeight);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // ---------- chat state ----------
  const [sending, setSending] = useState(false);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);

  const listRef = useRef(null);
  const canSend = text.trim().length > 0;

  const scrollToBottom = () => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  useEffect(() => {
    if (!minimized) scrollToBottom();
  }, [messages, minimized]);

  // ---------- persist UI state ----------
  useEffect(() => {
    localStorage.setItem(
      LS_KEY,
      JSON.stringify({
        minimized,
        right: pos.right,
        bottom: pos.bottom,
        w: size.w,
        h: size.h,
      })
    );
  }, [minimized, pos, size]);

  // ---------- clamp size to viewport ----------
  const clampedSize = useMemo(() => {
    const maxW = Math.max(300, vw - 24);
    const maxH = Math.max(420, vh - 24);
    return {
      w: clamp(size.w, 320, maxW),
      h: clamp(size.h, 460, maxH),
    };
  }, [size, vw, vh]);

  // ---------- clamp position to viewport ----------
  const clampedPos = useMemo(() => {
    const footprintW = minimized ? 170 : clampedSize.w;
    const footprintH = minimized ? 56 : clampedSize.h;

    const maxRight = Math.max(10, vw - footprintW - 10);
    const maxBottom = Math.max(10, vh - footprintH - 10);

    return {
      right: clamp(pos.right, 10, maxRight),
      bottom: clamp(pos.bottom, 10, maxBottom),
    };
  }, [pos, minimized, vw, vh, clampedSize]);

  useEffect(() => {
    setPos((p) => ({ ...p, ...clampedPos }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vw, vh, minimized, clampedSize.w, clampedSize.h]);

  useEffect(() => {
    setSize((s) => ({ ...s, ...clampedSize }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vw, vh]);

  // ✅ Helper: set welcome message based on auth
  const setWelcome = () => {
    if (user?.username) {
      setMessages([
        {
          role: "assistant",
          content: `Hi ${user.username}! Tell me what you need + budget. I’ll recommend items from SmartShop.`,
        },
      ]);
    } else {
      setMessages([
        {
          role: "assistant",
          content:
            "Hi! You’re browsing as a guest. Tell me what you need + budget (if any).",
        },
      ]);
    }
  };

  const resetUiLayout = () => {
    try {
        localStorage.removeItem(LS_KEY); // ✅ clear saved pos/size/minimized
    } catch {}
    setPos(DEFAULT_POS);
    setSize(DEFAULT_SIZE);
    setMinimized(true); // go back to bubble by default (change if you prefer open)
};


  // ✅ Reset chat when login/logout changes
  const lastAuthKeyRef = useRef(null);
  useEffect(() => {
    const authKey = user?.username ? `user:${user.username}` : "guest";

    // first run init
    if (lastAuthKeyRef.current === null) {
      lastAuthKeyRef.current = authKey;
      setWelcome();
      return;
    }

    // auth changed (login or logout or switched user)
    if (lastAuthKeyRef.current !== authKey) {
    lastAuthKeyRef.current = authKey;

    (async () => {
        try {
        await api.post("/assistant/reset/");
        } catch {}

        setText("");
        setSending(false);
        setWelcome();

        // ✅ also reset size/position/minimized state
        resetUiLayout();
    })();
    }



  }, [user]); // ✅ key line

  // ---------- API ----------
  const send = async () => {
    if (!canSend || sending) return;

    const userMsg = text.trim();
    setText("");
    setSending(true);
    setMessages((m) => [...m, { role: "user", content: userMsg }]);

    try {
      const r = await api.post("/assistant/chat/", { message: userMsg });
      const reply = r.data?.reply || "Sorry, I couldn't reply.";
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
    } catch (e) {
      const msg =
        e?.response?.data
          ? typeof e.response.data === "string"
            ? e.response.data
            : JSON.stringify(e.response.data)
          : e?.message || "Unknown error";
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${msg}` }]);
    } finally {
      setSending(false);
    }
  };

    const reset = async () => {
    try {
        await api.post("/assistant/reset/");
    } catch {}
    setText("");
    setSending(false);
    setWelcome();

    // ✅ reset UI layout too
    resetUiLayout();
    };


  // Enter to send, Shift+Enter for new line
  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // ---------- Drag ----------
  const dragRef = useRef({
    dragging: false,
    startX: 0,
    startY: 0,
    startRight: 18,
    startBottom: 18,
  });

  const startDrag = (x, y) => {
    dragRef.current.dragging = true;
    dragRef.current.startX = x;
    dragRef.current.startY = y;
    dragRef.current.startRight = clampedPos.right;
    dragRef.current.startBottom = clampedPos.bottom;
  };

  const moveDrag = (x, y) => {
    if (!dragRef.current.dragging) return;

    const dx = x - dragRef.current.startX;
    const dy = y - dragRef.current.startY;

    const footprintW = minimized ? 170 : clampedSize.w;
    const footprintH = minimized ? 56 : clampedSize.h;

    const maxRight = Math.max(10, vw - footprintW - 10);
    const maxBottom = Math.max(10, vh - footprintH - 10);

    setPos({
      right: clamp(dragRef.current.startRight - dx, 10, maxRight),
      bottom: clamp(dragRef.current.startBottom - dy, 10, maxBottom),
    });
  };

  const endDrag = () => (dragRef.current.dragging = false);

  // ---------- Resize (corner handle) ----------
  const resizeRef = useRef({
    resizing: false,
    startX: 0,
    startY: 0,
    startW: 420,
    startH: 580,
  });

  const startResize = (x, y) => {
    resizeRef.current.resizing = true;
    resizeRef.current.startX = x;
    resizeRef.current.startY = y;
    resizeRef.current.startW = clampedSize.w;
    resizeRef.current.startH = clampedSize.h;
  };

  const moveResize = (x, y) => {
    if (!resizeRef.current.resizing) return;

    const dx = resizeRef.current.startX - x;
    const dy = resizeRef.current.startY - y;

    const maxW = Math.max(300, vw - 24);
    const maxH = Math.max(420, vh - 24);

    setSize({
      w: clamp(resizeRef.current.startW + dx, 320, maxW),
      h: clamp(resizeRef.current.startH + dy, 460, maxH),
    });
  };

  const endResize = () => (resizeRef.current.resizing = false);

  useEffect(() => {
    const onMouseMove = (e) => {
      moveDrag(e.clientX, e.clientY);
      moveResize(e.clientX, e.clientY);
    };
    const onMouseUp = () => {
      endDrag();
      endResize();
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);

    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vw, vh, minimized, clampedSize.w, clampedSize.h, clampedPos.right, clampedPos.bottom]);

  // ---------- UI actions ----------
  const openPanel = () => {
    setMinimized(false);
    setTimeout(scrollToBottom, 0);
  };
  const minimizeToBubble = () => setMinimized(true);

  const sampleQuestions = [
    "Recommend hiking essentials for a student under $40",
    "I need a gift for my sister who likes running under $30",
    "HDMI cable 2m for laptop under $10",
  ];

  // ---------- consistent typography ----------
  const uiFont = {
    fontFamily: "Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
    color: "#0b1220",
  };
  const textSm = { fontSize: 12, fontWeight: 600 };
  const textBase = { fontSize: 13, fontWeight: 600 };
  const textStrong = { fontSize: 13, fontWeight: 800 };

  // ---------- styles ----------
  const bubbleStyle = {
    ...uiFont,
    position: "fixed",
    right: clampedPos.right,
    bottom: clampedPos.bottom,
    zIndex: 9999,
  };

  const panelStyle = {
    ...uiFont,
    position: "fixed",
    right: clampedPos.right,
    bottom: clampedPos.bottom,
    zIndex: 9999,
    width: clampedSize.w,
    height: clampedSize.h,
    borderRadius: 18,
    overflow: "hidden",
    background: "#fff",
    boxShadow: "0 18px 60px rgba(0,0,0,0.18)",
    border: "1px solid rgba(0,0,0,0.08)",
    display: "flex",
    flexDirection: "column",
  };

  const headerStyle = {
    background: "#f4f6fb",
    borderBottom: "1px solid rgba(0,0,0,0.08)",
    padding: "12px 12px",
    cursor: "grab",
    userSelect: "none",
  };

  const bodyStyle = {
    background: "#f8f9fb",
    padding: 12,
    flex: 1,
    overflowY: "auto",
  };

  const footerStyle = {
    background: "#ffffff",
    borderTop: "1px solid rgba(0,0,0,0.08)",
    padding: 12,
  };

  const chipStyle = {
    ...textSm,
    background: "#ffffff",
    border: "1px solid rgba(0,0,0,0.08)",
    borderRadius: 999,
    padding: "8px 10px",
    cursor: "pointer",
    boxShadow: "0 8px 20px rgba(0,0,0,0.05)",
  };

  const msgBubble = (role) => ({
    maxWidth: "86%",
    borderRadius: 14,
    padding: "10px 12px",
    whiteSpace: "pre-wrap",
    lineHeight: 1.35,
    fontSize: 13,
    fontWeight: 650,
    border: role === "assistant" ? "1px solid rgba(0,0,0,0.08)" : "none",
    background: role === "assistant" ? "#ffffff" : "#1f4fff",
    color: role === "assistant" ? "#0b1220" : "#ffffff",
  });

  const resizeHandleStyle = {
    position: "absolute",
    right: 8,
    bottom: 8,
    width: 18,
    height: 18,
    borderRadius: 6,
    background: "rgba(31,79,255,0.10)",
    border: "1px solid rgba(31,79,255,0.25)",
    cursor: "nwse-resize",
    display: "grid",
    placeItems: "center",
    userSelect: "none",
  };

  // ---------- render ----------
  if (minimized) {
    return (
      <div style={bubbleStyle}>
        <button
          onClick={openPanel}
          style={{
            ...uiFont,
            borderRadius: 999,
            padding: "12px 14px",
            fontWeight: 800,
            fontSize: 13,
            border: "none",
            background: "#1f4fff",
            color: "white",
            boxShadow: "0 14px 36px rgba(31,79,255,0.35)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
          title="Open Virtual Shopping Assistant"
        >
          💬 <span>Assistant</span>
        </button>
      </div>
    );
  }

  return (
    <div style={panelStyle}>
      <div
        style={headerStyle}
        onMouseDown={(e) => startDrag(e.clientX, e.clientY)}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
          <div>
            <div style={{ ...textStrong, fontSize: 14 }}>
              Virtual Shopping Assistant
              {sending ? <span style={{ opacity: 0.7 }}> • typing…</span> : null}
            </div>
            <div style={{ ...textSm, opacity: 0.8, marginTop: 2 }}>
              {user?.username ? `Signed in as ${user.username}` : "Browsing as guest"}
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "start" }}>
            <button
              onClick={reset}
              disabled={sending}
              style={{
                ...textBase,
                padding: "8px 10px",
                borderRadius: 12,
                background: "#fff",
                border: "1px solid rgba(0,0,0,0.12)",
                cursor: sending ? "not-allowed" : "pointer",
              }}
              title="Reset"
            >
              Reset
            </button>

            <button
              onClick={minimizeToBubble}
              style={{
                ...textBase,
                padding: "8px 10px",
                borderRadius: 12,
                background: "#fff",
                border: "1px solid rgba(0,0,0,0.12)",
                cursor: "pointer",
              }}
              title="Minimize"
            >
              —
            </button>
          </div>
        </div>

        <div style={{ marginTop: 10 }}>
          <div style={{ ...textSm, opacity: 0.8, marginBottom: 8 }}>Try one:</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {sampleQuestions.map((q) => (
              <button key={q} onClick={() => setText(q)} style={chipStyle}>
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div ref={listRef} style={bodyStyle}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              justifyContent: m.role === "user" ? "flex-end" : "flex-start",
              marginBottom: 10,
            }}
          >
            <div style={msgBubble(m.role)}>{m.content}</div>
          </div>
        ))}
      </div>

      <div style={footerStyle}>
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={4}
            placeholder="Type your question… (Shift+Enter for a new line)"
            style={{
              ...uiFont,
              flex: 1,
              borderRadius: 14,
              border: "1px solid rgba(0,0,0,0.14)",
              padding: 12,
              fontSize: 13,
              fontWeight: 600,
              outline: "none",
              minHeight: 96,
              resize: "none",
              background: "#fbfcff",
            }}
          />

          <button
            onClick={send}
            disabled={!canSend || sending}
            style={{
              ...uiFont,
              borderRadius: 14,
              border: "none",
              background: !canSend || sending ? "rgba(31,79,255,0.45)" : "#1f4fff",
              color: "white",
              fontWeight: 800,
              fontSize: 13,
              padding: "12px 14px",
              minWidth: 92,
              height: 46,
              cursor: !canSend || sending ? "not-allowed" : "pointer",
            }}
          >
            {sending ? "..." : "Send"}
          </button>
        </div>

        <div style={{ ...textSm, opacity: 0.75, marginTop: 8 }}>
          Tip: include <b>budget</b> and <b>use-case</b> for better recommendations.
        </div>
      </div>

      <div
        style={resizeHandleStyle}
        title="Resize"
        onMouseDown={(e) => startResize(e.clientX, e.clientY)}
      >
        ↘
      </div>
    </div>
  );
}
