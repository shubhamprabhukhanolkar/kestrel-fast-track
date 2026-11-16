import { useEffect, useState } from "react";
import { api, send } from "../api/client";
import { Badge } from "./shared";

export default function EmailApproval({
  active,
  user,
  draftText,
  onLoadDraft,
  notify,
}) {
  const [draft, setDraft] = useState(null);
  const [recipient, setRecipient] = useState("rm@example.invalid");
  const [subject, setSubject] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setDraft(null);
    setPassword("");
    setError("");
    setRecipient("rm@example.invalid");
    setSubject(`Document request — ${active.business}`);
    api(`/cases/${active.id}/email-drafts/latest`)
      .then((result) => {
        if (!alive) return;
        setDraft(result);
        if (result) {
          setRecipient(result.recipient);
          setSubject(result.subject);
          onLoadDraft((current) => current || result.body);
        }
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [active.id]);
  async function submit() {
    setBusy(true);
    setError("");
    try {
      setDraft(
        await send(`/cases/${active.id}/email-drafts`, {
          recipient,
          subject,
          body: draftText,
        }),
      );
      notify("Draft submitted for credit authorizer review.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function authorize(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await send(
        `/cases/${active.id}/email-drafts/${draft.id}/authorize`,
        { password },
      );
      setDraft({ ...draft, ...result });
      notify("Email approval recorded. Approved for sending.");
    } catch (e) {
      setError(e.message);
    } finally {
      setPassword("");
      setBusy(false);
    }
  }
  return (
    <section className="email-approval" aria-label="Email authorization">
      <div className="row spread">
        <strong>Email authorization</strong>
        <Badge
          type={draft?.status === "approved_for_sending" ? "green" : "amber"}
        >
          {draft?.status === "approved_for_sending"
            ? "Approved for sending"
            : draft
              ? "Authorizer review pending"
              : "Draft not submitted"}
        </Badge>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <label>
        Recipient email
        <input
          type="email"
          value={recipient}
          maxLength={254}
          onChange={(e) => setRecipient(e.target.value)}
        />
      </label>
      <label>
        Email subject
        <input
          value={subject}
          maxLength={200}
          onChange={(e) => setSubject(e.target.value)}
        />
      </label>
      <button
        className="secondary"
        disabled={
          busy ||
          draftText.trim().length < 10 ||
          subject.trim().length < 3 ||
          !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient)
        }
        onClick={submit}
      >
        Submit current draft for authorization
      </button>
      {draft && (
        <div className="submitted-email">
          <small>
            Submitted by {draft.created_by} · Version #{draft.id}
          </small>
          <strong>{draft.subject}</strong>
          <small>To: {draft.recipient}</small>
          <pre>{draft.body}</pre>
        </div>
      )}
      {draft?.status === "pending_authorization" &&
        user.persona === "arjun" && (
          <form onSubmit={authorize} className="email-password-form">
            <label>
              Credit authorizer password
              <input
                type="password"
                autoComplete="current-password"
                maxLength={256}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <p className="helper">
              Confirm your password to approve the submitted version shown
              above.
            </p>
            <button
              type="submit"
              className="primary"
              disabled={busy || !password}
            >
              {busy ? "Confirming…" : "Confirm password & approve email"}
            </button>
          </form>
        )}
      {draft?.status === "pending_authorization" &&
        user.persona !== "arjun" && (
          <p className="helper">
            Arjun Iyer must review this version and confirm his password before
            it is approved for sending.
          </p>
        )}
    </section>
  );
}
