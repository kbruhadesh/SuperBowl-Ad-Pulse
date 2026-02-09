/**
 * SuperBowl Ad Pulse — Frontend Dashboard
 * 
 * HONEST UI Requirements (Phase 9):
 * ✓ Event timeline with scores
 * ✓ Event score breakdown
 * ✓ Why ad was triggered (decision_reason)
 * ✓ Latency per step (Gemini/Groq)
 * ✓ Confidence value
 * 
 * NO "live" unless actually live
 * NO magical auto behavior
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SEGMENT_INTERVAL = 5 // seconds per segment

function App() {
    // Video state
    const [objectUrl, setObjectUrl] = useState(null)
    const [currentTime, setCurrentTime] = useState(0)
    const videoRef = useRef(null)

    // Business config
    const [businessName, setBusinessName] = useState('MVP Pizza')
    const [businessType, setBusinessType] = useState('pizza restaurant')

    // Upload state
    const [videoUri, setVideoUri] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [uploadError, setUploadError] = useState('')

    // Events and ads from database
    const [events, setEvents] = useState([])
    const [ads, setAds] = useState([])
    const [metrics, setMetrics] = useState(null)

    // Analysis state
    const analyzedSegmentsRef = useRef(new Set())
    const [analyzingSegment, setAnalyzingSegment] = useState(null)
    const [copiedIdx, setCopiedIdx] = useState(-1)

    // Refs for auto-scroll
    const eventsEndRef = useRef(null)
    const adsEndRef = useRef(null)

    // Format time helper
    const formatSec = (s) => {
        const m = Math.floor(s / 60)
        const sec = Math.floor(s % 60)
        return `${m}:${sec.toString().padStart(2, '0')}`
    }

    const formatWindow = (startSec, endSec) => {
        return `${formatSec(startSec)} – ${formatSec(endSec)}`
    }

    // Handle video time update
    const handleTimeUpdate = useCallback(() => {
        const v = videoRef.current
        if (v && !isNaN(v.currentTime)) setCurrentTime(v.currentTime)
    }, [])

    // Fetch metrics from API
    const fetchMetrics = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/metrics`)
            if (res.ok) {
                const data = await res.json()
                setMetrics(data)
            }
        } catch (err) {
            console.error('Failed to fetch metrics:', err)
        }
    }

    // Upload video
    const handleFileChange = async (e) => {
        const file = e.target.files?.[0]
        if (!file) return

        // Show video locally
        if (objectUrl) URL.revokeObjectURL(objectUrl)
        setObjectUrl(URL.createObjectURL(file))

        // Reset state
        setEvents([])
        setAds([])
        setMetrics(null)
        analyzedSegmentsRef.current = new Set()
        setVideoUri(null)
        setUploadError('')
        setUploading(true)

        try {
            const formData = new FormData()
            formData.append('file', file)

            const res = await fetch(`${API_BASE}/api/upload-video`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
                throw new Error(err.detail || 'Upload failed')
            }

            const data = await res.json()
            setVideoUri(data.video_uri)
        } catch (err) {
            setUploadError(err.message)
        } finally {
            setUploading(false)
        }
    }

    // Analyze segments as video plays
    useEffect(() => {
        if (!videoUri) return

        const segStart = Math.floor(currentTime / SEGMENT_INTERVAL) * SEGMENT_INTERVAL
        const segEnd = segStart + SEGMENT_INTERVAL

        // Collect all unanalyzed segments up to current time
        const segmentsToAnalyze = []
        for (let s = 0; s <= segStart; s += SEGMENT_INTERVAL) {
            const key = `${s}-${s + SEGMENT_INTERVAL}`
            if (!analyzedSegmentsRef.current.has(key)) {
                segmentsToAnalyze.push({ start: s, end: s + SEGMENT_INTERVAL, key })
            }
        }

        if (segmentsToAnalyze.length === 0) return

        // Mark as in-progress
        segmentsToAnalyze.forEach(seg => analyzedSegmentsRef.current.add(seg.key))

            // Process segments sequentially
            ; (async () => {
                for (const seg of segmentsToAnalyze) {
                    const window = formatWindow(seg.start, seg.end)
                    setAnalyzingSegment(window)

                    try {
                        const res = await fetch(`${API_BASE}/api/analyze-segment`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                start_sec: seg.start,
                                end_sec: seg.end,
                                video_uri: videoUri,
                                business_name: businessName,
                                business_type: businessType,
                            }),
                        })

                        const data = await res.json()

                        // Add event to list
                        if (data.event) {
                            const newEvent = {
                                ...data.event,
                                window: formatWindow(data.event.start_sec, data.event.end_sec),
                                decision_reason: data.decision_reason,
                            }
                            setEvents(prev => [...prev, newEvent])
                        }

                        // Add ad if generated
                        if (data.ad) {
                            const newAd = {
                                ...data.ad,
                                source_event: data.event,
                                decision_reason: data.decision_reason,
                            }
                            setAds(prev => [...prev, newAd])
                        }

                        // Refresh metrics
                        fetchMetrics()
                    } catch (err) {
                        console.error(`Segment ${seg.key} failed:`, err)
                    }
                }
                setAnalyzingSegment(null)
            })()
    }, [currentTime, videoUri, businessName, businessType])

    // Auto-scroll
    useEffect(() => {
        eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [events.length])

    useEffect(() => {
        adsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [ads.length])

    // Copy to clipboard
    const copyToClipboard = (text, idx) => {
        navigator.clipboard.writeText(text)
        setCopiedIdx(idx)
        setTimeout(() => setCopiedIdx(-1), 2000)
    }

    const isAnalyzing = analyzingSegment !== null

    return (
        <div className="dashboard">
            {/* ── Top Bar ── */}
            <header className="top-bar">
                <div className="top-bar-brand">
                    <h1>SuperBowl Ad Pulse</h1>
                    <span className="tagline">AI-powered ad generation from game moments</span>
                </div>
                <div className="top-bar-config">
                    <input
                        type="text"
                        placeholder="Business name"
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        className="config-input"
                    />
                    <input
                        type="text"
                        placeholder="Business type"
                        value={businessType}
                        onChange={(e) => setBusinessType(e.target.value)}
                        className="config-input"
                    />
                    <div className="status-indicator">
                        {(isAnalyzing || uploading) && <span className="status-dot warning" />}
                        {!isAnalyzing && !uploading && videoUri && <span className="status-dot" />}
                        <span>
                            {uploading
                                ? 'Uploading to Gemini...'
                                : isAnalyzing
                                    ? `Analyzing ${analyzingSegment}...`
                                    : videoUri
                                        ? 'Ready'
                                        : 'Waiting for video'}
                        </span>
                    </div>
                </div>
            </header>

            <div className="main-grid">
                {/* ── Left Column: Video + Events ── */}
                <div className="left-col">
                    {/* Video Player */}
                    <div className="video-card">
                        <div className="video-container">
                            {objectUrl ? (
                                <video
                                    ref={videoRef}
                                    src={objectUrl}
                                    controls
                                    onTimeUpdate={handleTimeUpdate}
                                    onSeeked={handleTimeUpdate}
                                    onPlay={handleTimeUpdate}
                                />
                            ) : (
                                <div className="video-placeholder">
                                    <label className="upload-label">
                                        {uploading ? 'Uploading...' : '📹 Upload Game Video'}
                                        <input
                                            type="file"
                                            accept="video/*"
                                            onChange={handleFileChange}
                                            hidden
                                            disabled={uploading}
                                        />
                                    </label>
                                </div>
                            )}
                        </div>
                        {objectUrl && (
                            <div className="video-info-bar">
                                <span className="time-display">{formatSec(currentTime)}</span>
                                {uploading && <span className="upload-status">Uploading to Gemini...</span>}
                                {!uploading && videoUri && <span className="upload-status ready">✓ Gemini Ready</span>}
                                {uploadError && <span className="upload-status error">⚠ {uploadError}</span>}
                                <div className="stats-group">
                                    <span>{events.length} events</span>
                                    <span>|</span>
                                    <span>{ads.length} ads</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Metrics Card */}
                    {metrics && (
                        <div className="metrics-card card">
                            <h3>Pipeline Metrics</h3>
                            <div className="metrics-grid">
                                <div className="metric-item">
                                    <div className="metric-value">{Math.round(metrics.avg_gemini_latency_ms)}ms</div>
                                    <div className="metric-label">Avg Gemini</div>
                                </div>
                                <div className="metric-item">
                                    <div className="metric-value">{Math.round(metrics.avg_groq_latency_ms)}ms</div>
                                    <div className="metric-label">Avg Groq</div>
                                </div>
                                <div className="metric-item">
                                    <div className="metric-value">{(metrics.discard_rate * 100).toFixed(0)}%</div>
                                    <div className="metric-label">Discard Rate</div>
                                </div>
                                <div className="metric-item">
                                    <div className="metric-value">{metrics.ads_generated}</div>
                                    <div className="metric-label">Ads Generated</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Events Timeline */}
                    <div className="events-card card">
                        <h3>
                            Event Timeline
                            <span className="count">{events.length}</span>
                        </h3>
                        <div className="events-list">
                            {events.map((ev, i) => (
                                <div
                                    key={`${ev.start_sec}-${ev.end_sec}`}
                                    className={`event-item ${currentTime >= ev.start_sec && currentTime < ev.end_sec ? 'active' : ''
                                        } ${i === events.length - 1 ? 'newest' : ''}`}
                                    onClick={() => {
                                        if (videoRef.current) videoRef.current.currentTime = ev.start_sec
                                    }}
                                >
                                    <span className="event-time">{ev.window}</span>
                                    <div className="event-content">
                                        <span className="event-type">{ev.event_type}</span>
                                        <span className="event-summary">
                                            {ev.summary || '(no events detected)'}
                                        </span>
                                        <div className="event-meta">
                                            <span className="event-score">
                                                Score: <strong>{ev.score?.toFixed(1)}/10</strong>
                                            </span>
                                            <span className="event-confidence">
                                                Confidence: {(ev.confidence * 100).toFixed(0)}%
                                            </span>
                                            {ev.gemini_latency_ms && (
                                                <span className="event-latency">
                                                    Gemini: {ev.gemini_latency_ms}ms
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="event-indicators">
                                        {ev.generate_ad ? (
                                            <span className="ad-generated-badge">AD</span>
                                        ) : (
                                            <span className="ad-skipped-badge">—</span>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isAnalyzing && (
                                <div className="analyzing-indicator">
                                    <span className="spinner" />
                                    <span>Analyzing {analyzingSegment} with Gemini...</span>
                                </div>
                            )}

                            <div ref={eventsEndRef} />

                            {events.length === 0 && !isAnalyzing && (
                                <p className="empty-msg">
                                    {videoUri
                                        ? 'Play the video to start segment analysis.'
                                        : uploading
                                            ? 'Uploading video to Gemini...'
                                            : 'Upload a video to get started.'}
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── Right Column: Key Moments + Ads ── */}
                <div className="right-col">
                    {/* Key Moments Table */}
                    {ads.length > 0 && (
                        <div className="key-moments-card">
                            <h3>Key Moments Summary</h3>
                            <table className="key-moments-table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Type</th>
                                        <th>Score</th>
                                        <th>Urgency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ads.map((ad, i) => (
                                        <tr
                                            key={i}
                                            onClick={() => {
                                                if (videoRef.current && ad.source_event?.start_sec != null) {
                                                    videoRef.current.currentTime = ad.source_event.start_sec
                                                }
                                            }}
                                        >
                                            <td>{formatWindow(ad.source_event?.start_sec || 0, ad.source_event?.end_sec || 0)}</td>
                                            <td>{ad.source_event?.event_type || '—'}</td>
                                            <td className="score-cell">{ad.source_event?.score?.toFixed(1) || '—'}</td>
                                            <td>
                                                <span className={`urgency-badge ${ad.urgency}`}>
                                                    {ad.urgency}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Ad Feed */}
                    <div className="ads-card card">
                        <h3>
                            Generated Ads
                            <span className="count">{ads.length}</span>
                        </h3>
                        <div className="ads-list">
                            {ads.map((ad, i) => (
                                <div key={i} className="ad-item">
                                    <div className="ad-header">
                                        <span className={`urgency-badge ${ad.urgency}`}>
                                            {ad.urgency}
                                        </span>
                                        <span className="event-type-tag">
                                            {ad.source_event?.event_type || 'play'}
                                        </span>
                                        <span className="ad-time">
                                            {formatWindow(ad.source_event?.start_sec || 0, ad.source_event?.end_sec || 0)}
                                        </span>
                                    </div>

                                    <div className="ad-copy">{ad.ad_copy}</div>
                                    <div className="ad-promo">{ad.promo_suggestion}</div>

                                    {ad.social_hashtags && (
                                        <div className="ad-hashtags">
                                            {(typeof ad.social_hashtags === 'string'
                                                ? JSON.parse(ad.social_hashtags)
                                                : ad.social_hashtags
                                            ).map((h, j) => (
                                                <span key={j} className="hashtag">{h}</span>
                                            ))}
                                        </div>
                                    )}

                                    {/* HONEST UI: Show why ad was triggered */}
                                    {ad.decision_reason && (
                                        <div className="ad-decision-reason">
                                            <strong>Why this ad:</strong> {ad.decision_reason}
                                        </div>
                                    )}

                                    <div className="ad-meta">
                                        <span>Score: {ad.source_event?.score?.toFixed(1)}/10</span>
                                        <span>Confidence: {(ad.source_event?.confidence * 100).toFixed(0)}%</span>
                                        {ad.groq_latency_ms && <span>Groq: {ad.groq_latency_ms}ms</span>}
                                    </div>

                                    <div className="ad-actions">
                                        <button
                                            className={`copy-btn ${copiedIdx === i ? 'copied' : ''}`}
                                            onClick={() =>
                                                copyToClipboard(
                                                    `${ad.ad_copy}\n\n${ad.promo_suggestion}\n\n${(typeof ad.social_hashtags === 'string'
                                                        ? JSON.parse(ad.social_hashtags)
                                                        : ad.social_hashtags || []
                                                    ).join(' ')
                                                    }`,
                                                    i
                                                )
                                            }
                                        >
                                            {copiedIdx === i ? '✓ Copied!' : 'Copy Ad'}
                                        </button>
                                    </div>
                                </div>
                            ))}

                            <div ref={adsEndRef} />

                            {ads.length === 0 && (
                                <p className="empty-msg">
                                    {videoUri
                                        ? 'Ads will appear when significant moments are detected.'
                                        : 'Upload a video to generate ads.'}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
