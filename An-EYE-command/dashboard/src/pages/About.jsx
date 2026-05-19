import CommandPageShell from "../components/CommandPageShell";


function About() {
  return (
    <CommandPageShell
      subtitle="Human-in-the-loop policing interface for AI-assisted violence detection."
      title="System Overview"
    >
      <section className="panel summary-box">
        <div className="map-topbar">
          <div>
            <h3 className="panel-title">System Overview</h3>
            <div className="panel-sub">Human-in-the-loop policing interface for AI-assisted violence detection.</div>
          </div>
        </div>

        <div className="preview-body">
          <div className="timeline">
            <div className="timeline-item"><strong>Monitor</strong> - Live city camera streams surface possible violence events.</div>
            <div className="timeline-item"><strong>Review</strong> - Officer validates the clip with confidence and location metadata.</div>
            <div className="timeline-item"><strong>Decide</strong> - Confirm, reject, escalate, or defer without disturbing background alerts.</div>
            <div className="timeline-item"><strong>Dispatch</strong> - Nearest station assignment forms a case record and moves it to history.</div>
          </div>
        </div>
      </section>
    </CommandPageShell>
  );
}


export default About;
