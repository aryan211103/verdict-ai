export default function HandoffScreen({ message, name, subtext, buttonLabel, onContinue }) {
  return (
    <div className="handoff-screen">
      <div className="handoff-card">
        <p className="handoff-msg">{message}</p>
        <h2 className="handoff-name">{name}</h2>
        <p className="handoff-sub">{subtext}</p>
        <button className="handoff-btn" onClick={onContinue}>{buttonLabel}</button>
      </div>
    </div>
  );
}
