import React from 'react';

export default function RoiPanel({ session, latestRoi, history }) {
  const hasFace = !!latestRoi;
  const conf = hasFace ? Math.round(latestRoi.confidence * 100) : 0;

  const fmtTime = (ts) => {
    const d = new Date(ts);
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
  };

  return (
    <>
      {/* Detection */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Latest Detection Details</span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 20,
            background: hasFace ? 'rgba(34,212,133,0.12)' : 'var(--surface2)',
            color: hasFace ? 'var(--green)' : 'var(--text3)',
            border: `1px solid ${hasFace ? 'var(--green-border)' : 'var(--border2)'}`,
          }}>
            {hasFace ? '✓ Face' : 'No Face'}
          </span>
        </div>
        <div className="det-body">
          {session && (
            <div className="session-row">
              <span className="session-key">Session ID:</span>
              <span className="session-val">{session.id}</span>
            </div>
          )}
          <div className={`det-box${hasFace ? '' : ' none'}`}>
            <div className="det-grid">
              {['X','Y','W','H'].map((k, i) => {
                const vals = hasFace ? [latestRoi.x, latestRoi.y, latestRoi.width, latestRoi.height] : ['-','-','-','-'];
                return (
                  <div key={k} className="det-cell">
                    <div className="det-cell-label">{k}</div>
                    <div className={`det-cell-val${hasFace ? '' : ' none'}`}>{vals[i]}</div>
                  </div>
                );
              })}
            </div>
            {hasFace ? (
              <div className="conf-row">
                <div className="conf-bar"><div className="conf-fill" style={{ width: `${conf}%` }} /></div>
                <span className="conf-pct">{conf}%</span>
              </div>
            ) : (
              <div style={{ fontSize: 12, color: 'var(--text3)' }}>No face detected in current frame</div>
            )}
          </div>
        </div>
      </div>

      {/* History table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">History &amp; Database View</span>
          <span style={{ fontSize: 10, color: 'var(--text3)' }}>{history.length} records</span>
        </div>
        <div className="history-body">
          {history.length > 0 ? (
            <div className="history-scroll">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Frame</th>
                    <th>Time</th>
                    <th>ROI (x,y,w,h)</th>
                    <th>Conf</th>
                    <th>Stored</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((r, i) => (
                    <tr key={i}>
                      <td className="td-frame">#{r.frame_index}</td>
                      <td>{fmtTime(r.t)}</td>
                      <td>[{r.x},{r.y},{r.width},{r.height}]</td>
                      <td className="td-conf">{Math.round(r.confidence * 100)}%</td>
                      <td className="td-stored">Yes</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="history-empty">No detections yet</div>
          )}
        </div>
      </div>
    </>
  );
}
