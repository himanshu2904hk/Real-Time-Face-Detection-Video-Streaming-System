import React from 'react';

export default function VideoFeed({ imgRef, isLive, latestRoi, className }) {
  return (
    <div className={`card${isLive ? ' live' : ''}${className ? ` ${className}` : ''}`}>
      <div className="card-header">
        <span className="card-title">
          {isLive && <span className="live-dot" />}
          Live Processed Feed
        </span>
        {isLive && (
          <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 700, letterSpacing: '0.5px' }}>● LIVE</span>
        )}
      </div>
      <div className="video-card-body">
        <div className="video-wrap">
          <img ref={imgRef} className="video-img" alt="" />
          {!isLive && (
            <div className="video-idle">
              <div className="idle-icon-wrap">
                <div className="idle-icon">📷</div>
              </div>
              <div className="idle-text">Camera not active</div>
              <div className="idle-hint">Click "Start Live Stream" to begin</div>
            </div>
          )}
        </div>
        <div className="video-caption">
          <span className="caption-dot" style={{ background: latestRoi ? 'var(--green)' : 'var(--text3)' }} />
          {latestRoi
            ? `ROI: Axis-Aligned Minimal Bounding Box · (${latestRoi.x}, ${latestRoi.y}) ${latestRoi.width}×${latestRoi.height}`
            : 'ROI: Axis-Aligned Minimal Bounding Box (Non-OpenCV Overlay)'}
        </div>
      </div>
    </div>
  );
}
