import { useEffect, useRef, useState } from "react";
import { BookOpen, Download, Search, X, ArrowRight } from "lucide-react";

import topics from "../helpTopics";

export default function HelpCenter({ onClose, user, navigate }) {
  const dialog = useRef(null);
  const searchInput = useRef(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState("start");
  useEffect(() => {
    const element = dialog.current;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    element.showModal();
    searchInput.current.focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
      element.close();
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, []);
  const search = query.trim().toLowerCase();
  const matches = topics.filter((topic) =>
    [topic.title, topic.subtitle, ...topic.steps, ...topic.notes]
      .join(" ")
      .toLowerCase()
      .includes(search),
  );
  const current = matches.find((topic) => topic.id === selected) || matches[0];
  function download() {
    const text =
      "# Kestrel Workbench — Operating Guide\n\n" +
      topics
        .map(
          (topic) =>
            `## ${topic.title}\n\n${topic.subtitle}\n\n${topic.steps.map((step, index) => `${index + 1}. ${step}`).join("\n\n")}\n\n${topic.notes.map((note) => `Note: ${note}`).join("\n\n")}`,
        )
        .join("\n\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/markdown;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "Kestrel-Operating-Guide.md";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <dialog
      ref={dialog}
      className="help-dialog"
      aria-labelledby="help-title"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          onClose();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialog.current) onClose();
      }}
    >
      <div className="help-shell">
        <header className="help-header">
          <div>
            <span className="section-label">KESTREL WORKBENCH GUIDE</span>
            <h2 id="help-title">
              <BookOpen size={23} /> Help & Tutorial
            </h2>
            <p>
              Instructions for completing your work and resolving common issues.
            </p>
          </div>
          <button
            className="secondary"
            onClick={onClose}
            aria-label="Close help"
          >
            <X size={18} />
          </button>
        </header>
        <div className="help-tools">
          <label className="help-search">
            <Search size={17} />
            <input
              ref={searchInput}
              type="search"
              aria-label="Search operating guide"
              placeholder="Search documents, chaser, sign-off, costs…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <button className="secondary" onClick={download}>
            <Download size={15} /> Download operating guide
          </button>
        </div>
        <div className="help-layout">
          <nav className="help-topics" aria-label="Help topics">
            {matches.map((topic) => (
              <button
                key={topic.id}
                aria-current={current?.id === topic.id ? "page" : undefined}
                className={current?.id === topic.id ? "selected" : ""}
                onClick={() => setSelected(topic.id)}
              >
                {topic.title}
              </button>
            ))}
          </nav>
          <article className="help-content" key={current?.id}>
            {current ? (
              <>
                <span className="section-label">
                  {user
                    ? `SIGNED IN AS ${user.name.toUpperCase()}`
                    : "AVAILABLE BEFORE SIGN-IN"}
                </span>
                <h3>{current.title}</h3>
                <p className="help-subtitle">{current.subtitle}</p>
                <ol>
                  {current.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
                {current.notes.map((note) => (
                  <p className="help-note" key={note}>
                    {note}
                  </p>
                ))}
                {user && current.target && (
                  <button
                    className="primary"
                    onClick={() => {
                      navigate(current.target);
                      onClose();
                    }}
                  >
                    Open{" "}
                    {current.target === "intake"
                      ? "Intake & Extraction"
                      : current.target === "verification"
                        ? "Verification & Sign-Off"
                        : current.target === "studio"
                          ? "Prompt & Toner Studio"
                          : "FinOps & API Health"}
                    <ArrowRight size={15} />
                  </button>
                )}
              </>
            ) : (
              <div role="status">
                <h3>No matching topics</h3>
                <p>Try “PDF”, “chaser”, “cost” or “signature”.</p>
                <button className="secondary" onClick={() => setQuery("")}>
                  Clear search
                </button>
              </div>
            )}
          </article>
        </div>
      </div>
    </dialog>
  );
}
