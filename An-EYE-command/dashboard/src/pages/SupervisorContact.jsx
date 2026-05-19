import CommandPageShell from "../components/CommandPageShell";


function SupervisorContact() {
  return (
    <CommandPageShell
      subtitle="Live CCTV relay - South precinct belt - Updated 18s ago"
      title="Supervisor Contact"
    >
      <section className="panel action-form">
        <div className="map-topbar">
          <div>
            <h3 className="panel-title">Contact Supervisor</h3>
            <div className="panel-sub">Use structured escalation when command oversight is needed.</div>
          </div>
        </div>

        <div className="preview-body form-grid">
          <div className="form-row">
            <label>Supervisor Desk</label>
            <select defaultValue="Central Command - Desk Alpha">
              <option>Central Command - Desk Alpha</option>
              <option>Night Review Cell - Desk Delta</option>
            </select>
          </div>

          <div className="form-row">
            <label>Subject</label>
            <input defaultValue="Urgent: Multiple clustered alerts in Ward 6" />
          </div>

          <div className="form-row">
            <label>Message</label>
            <textarea defaultValue="Three alerts have appeared within a seven-minute window around Ashok Rajpath belt. One case already moved to dispatch recommendation." />
          </div>

          <button className="send-btn" type="button">Send Escalation Note</button>
        </div>
      </section>
    </CommandPageShell>
  );
}


export default SupervisorContact;
