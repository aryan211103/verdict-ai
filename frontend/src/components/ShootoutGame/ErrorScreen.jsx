// Full-screen error state — used for expired/evicted sessions and hard failures.
// Never shown for transient errors that the user can retry from context.
export default function ErrorScreen({ title, message, actionLabel, onAction }) {
  return (
    <div className="error-screen">
      <div className="error-screen-icon">⚠️</div>
      <h2 className="error-screen-title">{title}</h2>
      <p  className="error-screen-msg">{message}</p>
      <button className="start-btn" onClick={onAction}>{actionLabel}</button>
    </div>
  );
}
