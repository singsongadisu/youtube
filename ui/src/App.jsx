import React, { useState, useEffect, useRef } from 'react';
import {
  Plus, Settings, History, HelpCircle,
  Search, Mic, Clock, Youtube,
  Layout, BookOpen, Layers, Zap,
  ChevronRight, ExternalLink, Download,
  Loader2, AlertCircle, CheckCircle, Split, Map, Sparkles, Image as ImageIcon, FileText, Globe, Maximize, X, Volume2, Info,
  Music, Play, Pause, Save, TrendingUp, User, Target, Camera, Video, Film
} from 'lucide-react';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [duration, setDuration] = useState(5);
  const [language, setLanguage] = useState('am');
  const [tone, setTone] = useState('neutral');
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [studioData, setStudioData] = useState(null);
  const [showTeleprompter, setShowTeleprompter] = useState(false);
  const [tpFontSize, setTpFontSize] = useState(24);
  const [tpSpeed, setTpSpeed] = useState(2);
  const [projects, setProjects] = useState([]);
  const [activeTab, setActiveTab] = useState('studio-am');
  const [ttsAudio, setTtsAudio] = useState(null);
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false);

  // Voice Studio Specific State
  const [vsScript, setVsScript] = useState('');
  const [vsLang, setVsLang] = useState('am');
  const [gender, setGender] = useState('female');

  // Creative Forge Specific State
  const [idea, setIdea] = useState('');
  const [forgeDuration, setForgeDuration] = useState(3);
  const [forgeLang, setForgeLang] = useState('en');
  const [forgeScript, setForgeScript] = useState('');
  const [forgeStatus, setForgeStatus] = useState('idle');
  const [forgeAssets, setForgeAssets] = useState(null);
  const [detectedBlueprint, setDetectedBlueprint] = useState(null);
  const [forgeSegments, setForgeSegments] = useState([]);
  const [forgeMusic, setForgeMusic] = useState(null);
  const [forgeProduction, setForgeProduction] = useState(null);
  const [isRefining, setIsRefining] = useState(false);
  const [isRenderingVideo, setIsRenderingVideo] = useState(false);
  const [forgeVideoUrl, setForgeVideoUrl] = useState(null);
  const [narrators, setNarrators] = useState([]);
  const [selectedNarrator, setSelectedNarrator] = useState(null);

  const ws = useRef(null);

  useEffect(() => {
    fetchProjects();
    fetchNarrators();
  }, []);

  const fetchNarrators = async () => {
    try {
      const resp = await fetch('http://localhost:8000/narrators');
      const data = await resp.json();
      setNarrators(data);
      // Set default narrator for English
      const defaultEn = data.find(n => n.id === 'aria');
      if (defaultEn) setSelectedNarrator(defaultEn);
    } catch (err) {
      console.error("Failed to fetch narrators:", err);
    }
  };

  const fetchProjects = async () => {
    try {
      const resp = await fetch('http://localhost:8000/videos');
      const data = await resp.json();
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    }
  };

  const loadProject = async (id) => {
    try {
      setStatus('processing');
      setMessage('Retrieving from Database...');
      const resp = await fetch(`http://localhost:8000/project/${id}`);
      const data = await resp.json();
      if (data.studio_script) {
        setStudioData(data);
        setVsScript(data.studio_script);
        setVsLang(data.target_lang);
        setStatus('completed');
        setMessage('Loaded from MongoDB');
        setActiveTab('studio');
      }
    } catch (err) {
      console.error("Failed to load project:", err);
      setStatus('error');
    }
  };

  const startAnalysis = () => {
    if (!url) return;
    setStatus('processing');
    setMessage('Igniting Studio Engine...');
    setProgress(0);
    setStudioData(null);

    ws.current = new WebSocket('ws://localhost:8000/ws/process');
    ws.current.onopen = () => {
      ws.current.send(JSON.stringify({ url, duration: parseInt(duration), language }));
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === 'processing') {
        setMessage(data.message);
        setProgress(data.progress);
      } else if (data.status === 'completed') {
        setStatus('completed');
        setMessage(data.message);
        setProgress(100);
        setStudioData(data.studio_data);
        setVsScript(data.studio_data.studio_script);
        setVsLang(data.studio_data.target_lang);
        fetchProjects();
      } else if (data.status === 'error') {
        setStatus('error');
        setMessage(data.message);
      }
    };
  };

  const downloadSRT = () => {
    if (!studioData?.srt_content) return;
    const blob = new Blob([studioData.srt_content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `subtitles_${studioData.target_lang}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const downloadSourceVideo = () => {
    if (!studioData?.video_filename) return;
    const downloadUrl = `http://localhost:8000/static/downloads/${encodeURIComponent(studioData.video_filename)}`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = studioData.video_filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const downloadRenderedVideo = () => {
    if (!studioData?.rendered_video_path) return;
    // The path is absolute on the server, we need to extract the filename
    const filename = studioData.rendered_video_path.split(/[\\/]/).pop();
    const downloadUrl = `http://localhost:8000/static/videos/${encodeURIComponent(filename)}`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const generateTTS = async (text, lang) => {
    if (!text || isGeneratingTTS) return;
    setIsGeneratingTTS(true);
    try {
      const resp = await fetch('http://localhost:8000/generate-tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          lang: lang,
          gender: gender,
          tone: tone,
          filename: `tts_${lang}_${gender}_${tone}_${Date.now()}.mp3`
        })
      });
      const data = await resp.json();
      if (data.url) {
        setTtsAudio(data.url);
      }
    } catch (err) {
      console.error("TTS failed:", err);
    } finally {
      setIsGeneratingTTS(false);
    }
  };

  const refineForgeScript = async (style) => {
    if (!forgeScript || isRefining) return;
    setIsRefining(true);
    try {
      const resp = await fetch('http://localhost:8000/refine-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script: forgeScript, style })
      });
      const data = await resp.json();
      if (data.script) {
        setForgeScript(data.script);
      }
    } catch (err) {
      console.error("Refinement failed:", err);
    } finally {
      setIsRefining(false);
    }
  };

  const generateForgeScript = async () => {
    if (!idea) return;
    setForgeStatus('generating-script');
    try {
      const resp = await fetch('http://localhost:8000/generate-creative-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, duration: forgeDuration, lang: forgeLang })
      });
      const data = await resp.json();
      if (data.script) {
        setForgeScript(data.script);
        setDetectedBlueprint(data.blueprint);
        setForgeSegments(data.segments);
        setForgeMusic(data.music);
        setForgeProduction(data.production);
        setForgeStatus('preview');
      }
    } catch (err) {
      console.error("Forge script gen failed:", err);
      setForgeStatus('idle');
    }
  };

  const approveForgeProject = async () => {
    if (!forgeScript) return;
    setForgeStatus('generating-assets');
    try {
      const resp = await fetch('http://localhost:8000/approve-creative-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: forgeScript,
          lang: forgeLang,
          narratorId: selectedNarrator?.id || 'aria',
          segments: forgeSegments,
          idea: idea
        })
      });
      const data = await resp.json();
      if (data.audio_url) {
        setForgeAssets(data);
        setForgeStatus('completed');
      }
    } catch (err) {
      console.error("Forge approval failed:", err);
      setForgeStatus('script-ready');
    }
  };

  const generateForgeVideo = async () => {
    if (!forgeAssets?.audio_path || isRenderingVideo) return;
    setIsRenderingVideo(true);
    setForgeVideoUrl(null);
    try {
      const resp = await fetch('http://localhost:8000/generate-forge-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_path: forgeAssets.audio_path,
          segments: forgeSegments,
          bg_music: forgeMusic?.genre || 'explainer'
        })
      });
      const data = await resp.json();
      if (data.video_url) {
        setForgeVideoUrl(data.video_url);
      } else if (data.error) {
        alert("Rendering error: " + data.error);
      }
    } catch (err) {
      console.error("Video rendering failed:", err);
    } finally {
      setIsRenderingVideo(false);
    }
  };

  return (
    <div className="studio-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-dot" />
          <span>Amharic Studio</span>
        </div>

        <nav className="nav-section">
          <div className={`nav-item ${activeTab === 'studio-am' ? 'active' : ''}`} onClick={() => { setActiveTab('studio-am'); setLanguage('am'); }}>
            <Layout size={18} />
            <span>Amharic Studio</span>
          </div>
          <div className={`nav-item ${activeTab === 'studio-en' ? 'active' : ''}`} onClick={() => { setActiveTab('studio-en'); setLanguage('en'); }}>
            <Globe size={18} />
            <span>English Studio</span>
          </div>
          <div className={`nav-item ${activeTab === 'voice-gen' ? 'active' : ''}`} onClick={() => setActiveTab('voice-gen')}>
            <Music size={18} />
            <span>AI Voice Studio</span>
          </div>
          <div className={`nav-item ${activeTab === 'launch' ? 'active' : ''}`} onClick={() => setActiveTab('launch')}>
            <TrendingUp size={18} />
            <span>Viral Launchpad</span>
          </div>
          <div className={`nav-item ${activeTab === 'voice' ? 'active' : ''}`} onClick={() => setActiveTab('voice')}>
            <Volume2 size={18} />
            <span>Voice Mastery</span>
          </div>
          <div className={`nav-item ${activeTab === 'forge' ? 'active' : ''}`} onClick={() => setActiveTab('forge')}>
            <Sparkles size={18} color="var(--primary)" />
            <span>Creative Forge</span>
          </div>
        </nav>

        <div className="history-section">
          <h4 className="history-title">Recent Activity</h4>
          <div className="history-list">
            {projects.length > 0 ? projects.slice(0, 8).map((p, i) => (
              <div className="history-item" key={i} onClick={() => loadProject(p._id)} title={p.title}>
                <History size={14} style={{ marginRight: '8px' }} />
                <span className="truncate">{p.title}</span>
              </div>
            )) : <span style={{ fontSize: '0.8rem', opacity: 0.3 }}>No projects yet</span>}
          </div>
        </div>
      </aside>

      {/* Main Stage */}
      <main className="main-stage">
        <header className="top-bar">
          <div className="top-tools">
            {studioData && (
              <>
                <button className="tool-btn" onClick={downloadSRT}>
                  <FileText size={16} />
                  <span>Export .SRT</span>
                </button>
                <button className="tool-btn highlight" onClick={downloadSourceVideo}>
                  <Youtube size={16} />
                  <span>Download Source Video</span>
                </button>
                {studioData.rendered_video_path && (
                  <button className="tool-btn highlight pulse-border" onClick={downloadRenderedVideo}>
                    <Zap size={16} />
                    <span>Download Rendered (7m)</span>
                  </button>
                )}
              </>
            )}
          </div>
          <div className="user-profile">
            <HelpCircle size={18} color="var(--text-dark)" />
          </div>
        </header>

        <div className="stage-content">
          {(activeTab === 'studio-am' || activeTab === 'studio-en') && (
            <>
              {/* Hero Input Section */}
              <section className="input-hero fade-up">
                <h2>{activeTab === 'studio-am' ? 'Amharic Transformation Studio' : 'English Transformation Studio'}</h2>
                <div className="glass-box">
                  <div className="pro-input-group">
                    <input
                      type="text"
                      placeholder="Paste YouTube Link (English)"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      disabled={status === 'processing'}
                    />
                    <button className="action-btn" onClick={startAnalysis} disabled={status === 'processing' || !url}>
                      {status === 'processing' ? <Loader2 size={18} className="spinning" /> : <Zap size={18} />}
                      <span>{status === 'processing' ? 'Processing' : 'Analyze'}</span>
                    </button>
                  </div>

                  <div className="settings-row">
                    <div className="setting-item">
                      <Clock size={16} />
                      <span>Target Duration</span>
                      <input
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(e.target.value)}
                        disabled={status === 'processing'}
                      />
                      <span>Mins</span>
                    </div>

                    <div className="setting-item">
                      <Globe size={16} />
                      <span>Mode: {activeTab === 'studio-am' ? 'Amharic Generation' : 'English Synthesis'}</span>
                    </div>
                  </div>

                  {status === 'processing' && (
                    <div className="progress-loader">
                      <div className="loader-track">
                        <div className="loader-bar" style={{ width: `${progress}%` }} />
                      </div>
                      <div className="loader-status">
                        {message} — {progress}%
                      </div>
                    </div>
                  )}
                </div>
              </section>

              {/* Results Area */}
              {studioData && (
                <div className="results-wrapper fade-up">
                  {/* Viral Hooks & Thumbnail */}
                  <div className="growth-row mb-2">
                    <div className="hook-lab glass-box">
                      <div className="panel-title">
                        <Sparkles size={20} className="icon glow" />
                        <h2>Viral Hook Lab</h2>
                      </div>
                      <div className="hook-grid">
                        {studioData.viral_hooks?.map((hook, i) => (
                          <div className="hook-card" key={i}>
                            <span className="hook-tag">Option {i + 1}</span>
                            <p>{hook}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="thumbnail-lab glass-box">
                      <div className="panel-title">
                        <ImageIcon size={20} className="icon glow-blue" />
                        <h2>Thumbnail Strategy</h2>
                      </div>
                      <div className="thumbnail-prompt-card">
                        <span className="hook-tag">AI Design Prompt (English Only)</span>
                        <p>{studioData.thumbnail_prompt}</p>
                      </div>
                    </div>
                  </div>

                  {/* SEO & Meta */}
                  <div className="meta-panel glass-box mb-2">
                    <div className="panel-title">
                      <Search size={20} className="icon glow-green" />
                      <h2>SEO & Meta Success Kit</h2>
                    </div>
                    <div className="meta-grid">
                      <div className="meta-col">
                        <span className="hook-tag">Recommended Titles ({studioData.target_lang?.toUpperCase()})</span>
                        <div className="title-options">
                          {studioData.metadata?.titles.map((t, i) => (
                            <div className="title-opt" key={i}>
                              <CheckCircle size={14} color="var(--success)" />
                              <span>{t}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="meta-col">
                        <span className="hook-tag">YouTube Chapters (Paste into Desc)</span>
                        <div className="chapters-box">
                          {studioData.chapters}
                        </div>
                      </div>
                      <div className="meta-col full-w">
                        <span className="hook-tag">Full Video Description</span>
                        <div className="desc-preview">
                          {studioData.metadata?.description}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="studio-grid">
                    <div className="script-container">
                      <div className="panel-title">
                        <BookOpen size={20} className="icon" />
                        <h2>Creative Scripts</h2>
                        <div className="script-tools">
                          <button className="tele-btn" onClick={() => setShowTeleprompter(true)}>
                            <Maximize size={14} />
                            Teleprompter
                          </button>
                        </div>
                      </div>

                      <div className="split-view">
                        <div className="script-card">
                          <div className="card-header">
                            <span>Source Transcript</span>
                          </div>
                          <div className="script-area" readOnly>
                            {studioData.english_script}
                          </div>
                        </div>
                        <div className={`script-card ${studioData.target_lang === 'am' ? 'amharic' : 'condensed'}`}>
                          <div className="card-header">
                            <span>{studioData.target_lang === 'am' ? 'Amharic Narration Ready' : 'Condensed English'}</span>
                            <Mic size={14} color="var(--primary)" />
                          </div>
                          <div className="script-area">
                            {studioData.studio_script}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="roadmap-panel">
                      <div className="panel-title">
                        <Map size={20} className="icon" />
                        <h2>Editing Roadmap</h2>
                      </div>
                      <div className="roadmap-list">
                        {studioData.editing_guide.map((item, idx) => (
                          <div className="roadmap-item" key={idx}>
                            <div className="timeline">
                              <div className="time-badge">{item.timestamp}</div>
                              <div className="line" />
                            </div>
                            <div className="roadmap-content">
                              <span className="action-chip">{item.edit_action}</span>
                              <p className="am-txt">{item.narration_suggestion || item.amharic_suggestion}</p>
                              {item.visual_prompt && (
                                <div className="visual-prompt-box">
                                  <ImageIcon size={12} />
                                  <span>AI Visual B-Roll:</span>
                                  <p>{item.visual_prompt}</p>
                                </div>
                              )}
                              {item.video_clip_prompt && (
                                <div className="visual-prompt-box video-p">
                                  <Zap size={12} />
                                  <span>AI Video Clip (5s):</span>
                                  <p>{item.video_clip_prompt}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'voice-gen' && (
            <section className="voice-studio fade-up">
              <div className="voice-studio-header mb-2">
                <h1>AI Voice Studio 🎙️</h1>
                <p>Generate high-quality neural narration with custom voices.</p>
              </div>

              <div className="voice-studio-grid">
                <div className="vs-editor glass-box">
                  <div className="panel-title">
                    <FileText size={20} className="icon" />
                    <h2>Script Editor</h2>
                    <div className="vs-lang-select">
                      <button className={vsLang === 'am' ? 'active' : ''} onClick={() => setVsLang('am')}>Amharic</button>
                      <button className={vsLang === 'en' ? 'active' : ''} onClick={() => setVsLang('en')}>English</button>
                    </div>
                    <div className="vs-gender-select ml-1">
                      <button className={gender === 'female' ? 'active' : ''} onClick={() => setGender('female')}>
                        {vsLang === 'am' ? 'Mekdes (Female)' : 'Aria (Female)'}
                      </button>
                      <button className={gender === 'male' ? 'active' : ''} onClick={() => setGender('male')}>
                        {vsLang === 'am' ? 'Ameha (Male)' : 'Guy (Male)'}
                      </button>
                    </div>
                    <div className="vs-tone-selector ml-1">
                      <select
                        value={tone}
                        onChange={(e) => setTone(e.target.value)}
                        className="pro-select"
                      >
                        <option value="neutral">Neutral Vibe</option>
                        <option value="viral">Viral / Hype</option>
                        <option value="preaching">Preaching / Deep</option>
                        <option value="news">Breaking News</option>
                      </select>
                    </div>
                  </div>
                  <textarea
                    className="vs-textarea"
                    placeholder="Paste your script here..."
                    value={vsScript}
                    onChange={(e) => setVsScript(e.target.value)}
                  />
                  <div className="vs-actions">
                    <button className="vs-gen-btn" onClick={() => generateTTS(vsScript, vsLang)} disabled={isGeneratingTTS || !vsScript}>
                      {isGeneratingTTS ? <Loader2 size={18} className="spinning" /> : <Mic size={18} />}
                      <span>{isGeneratingTTS ? 'Generating Audio...' : 'Generate AI Voice'}</span>
                    </button>
                  </div>
                </div>

                <div className="vs-preview glass-box">
                  <div className="panel-title">
                    <Music size={20} className="icon glow" />
                    <h2>Audio Output</h2>
                  </div>

                  {ttsAudio ? (
                    <div className="vs-audio-card fade-up">
                      <div className="audio-visualizer">
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                        <div className="bar" />
                      </div>
                      <h3>Your Narration is Ready!</h3>
                      <audio controls src={ttsAudio} className="vs-custom-audio" />
                      <div className="vs-download-box">
                        <a href={ttsAudio} download className="vs-dl-link">
                          <Download size={18} />
                          Download Audio File (.mp3)
                        </a>
                      </div>
                    </div>
                  ) : (
                    <div className="vs-empty-state">
                      <Sparkles size={48} color="var(--border)" />
                      <p>Your generated audio will appear here.</p>
                    </div>
                  )}

                  <div className="vs-tips mt-2">
                    <h4>💡 Pro-Studio Tip:</h4>
                    <p>For the best results, use the **Voice Mastery** tools to enhance the generated AI audio for that premium "Studio" sound.</p>
                  </div>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'launch' && studioData && (
            <section className="launchpad-studio fade-up">
              <div className="voice-studio-header mb-2">
                <h1>Viral Growth Launchpad 🚀</h1>
                <p>Repurpose your content for maximum reach and engagement.</p>
              </div>

              <div className="launchpad-grid">
                {/* Mockup Preview */}
                <div className="mockup-panel glass-box">
                  <div className="panel-title">
                    <Youtube size={20} className="icon glow-red" />
                    <h2>Feed Clickability Test</h2>
                  </div>
                  <div className="yt-mock-feed">
                    <div className="yt-mock-card">
                      <div className="yt-mock-thumb-container">
                        <img src={studioData.thumbnail_data?.image_url} alt="Thumbnail Mock" className="yt-mock-thumb" />
                        <span className="yt-mock-duration">12:45</span>
                      </div>
                      <div className="yt-mock-info">
                        <div className="yt-mock-avatar" />
                        <div className="yt-mock-text">
                          <h3 className="yt-mock-title">{studioData.metadata?.titles[0]}</h3>
                          <p className="yt-mock-meta">Amharic Studio • 1.2M views • 2 hours ago</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p className="vs-tips mt-1">💡 Does this thumbnail "pop" against the dark background? Professionals check this before uploading.</p>
                </div>

                {/* Community & Threads */}
                <div className="growth-assets glass-box">
                  <div className="panel-title">
                    <Layers size={20} className="icon glow-green" />
                    <h2>Launch Day Assets</h2>
                  </div>

                  <div className="asset-card mb-2">
                    <span className="hook-tag">YouTube Community Post</span>
                    <p className="asset-txt">{studioData.growth_launchpad?.teaser}</p>
                    <div className="poll-preview mt-1">
                      <strong>📊 Poll: {studioData.growth_launchpad?.poll.question}</strong>
                      <div className="poll-opts">
                        {studioData.growth_launchpad?.poll.options.map((opt, i) => (
                          <div className="poll-opt" key={i}>{opt}</div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="asset-card">
                    <span className="hook-tag">Twitter/X Thread (Viral)</span>
                    <div className="social-thread-box">
                      {studioData.social_thread?.map((item, i) => (
                        <div className="thread-tweet" key={i}>{item}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'voice' && (
            <section className="voice-mastery fade-up">
              <div className="glass-box">
                <div className="panel-title">
                  <Volume2 size={24} className="icon glow" />
                  <h2>Voice Mastery & AI Enhancement</h2>
                </div>
                <div className="voice-grid">
                  <div className="voice-card main">
                    <Sparkles size={32} color="var(--primary)" />
                    <h3>The #1 Success Tip: Adobe Podcast Enhance</h3>
                    <p>After you record your voice (or generate an AI voice), use this tool to make it sound like you're in a professional studio.</p>
                    <a href="https://podcast.adobe.com/enhance" target="_blank" className="link-btn">
                      Open Adobe Enhance (Free AI) <ExternalLink size={16} />
                    </a>
                  </div>

                  <div className="voice-steps">
                    <div className="v-step">
                      <div className="v-num">1</div>
                      <div className="v-info">
                        <h4>Record/Generate</h4>
                        <p>Use our AI Voice Studio or the Teleprompter to get your raw audio narration.</p>
                      </div>
                    </div>
                    <div className="v-step">
                      <div className="v-num">2</div>
                      <div className="v-info">
                        <h4>AI Transformation</h4>
                        <p>Upload your recording to Adobe Enhance. It will remove all background noise and "Studio-ify" your voice.</p>
                      </div>
                    </div>
                    <div className="v-step">
                      <div className="v-num">3</div>
                      <div className="v-info">
                        <h4>Final Polish</h4>
                        <p>If you use CapCut, add a small "Compressor" effect to make your voice sit perfectly over the music.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'forge' && (
            <section className="forge-studio fade-up">
              <div className="voice-studio-header mb-2 text-center">
                <h1>Creative Forge ⚒️</h1>
                <p>From a simple idea to a professional script & narration.</p>
              </div>

              <div className="forge-container glass-box p-3">
                <div className="pro-input-group mb-2">
                  <input
                    type="text"
                    placeholder="Enter your video idea (e.g. 'The history of coffee')"
                    value={idea}
                    onChange={(e) => setIdea(e.target.value)}
                    disabled={forgeStatus !== 'idle' && forgeStatus !== 'script-ready'}
                  />
                  <button
                    className="action-btn"
                    onClick={generateForgeScript}
                    disabled={!idea || (forgeStatus !== 'idle' && forgeStatus !== 'script-ready')}
                  >
                    {forgeStatus === 'generating-script' ? <Loader2 size={18} className="spinning" /> : <Zap size={18} />}
                    <span>Generate Script</span>
                  </button>
                </div>

                <div className="settings-row mb-3">
                  <div className="setting-item">
                    <Clock size={16} />
                    <span>Duration (Mins)</span>
                    <input
                      type="number"
                      value={forgeDuration}
                      onChange={(e) => setForgeDuration(e.target.value)}
                    />
                  </div>
                  <div className="setting-item">
                    <Globe size={16} />
                    <span>Output Language</span>
                    <select
                      value={forgeLang}
                      onChange={(e) => setForgeLang(e.target.value)}
                      className="pro-select"
                    >
                      <option value="en">English</option>
                      <option value="am">Amharic</option>
                      <option value="ar">Arabic</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                    </select>
                  </div>
                </div>

                {forgeScript && (
                  <div className="forge-narrator-section mb-3 fade-up">
                    <div className="section-header">
                      <Mic size={20} color="var(--primary)" />
                      <h2 className="studio-title">Choose Your Narrator</h2>
                    </div>
                    <div className="narrator-grid">
                      {narrators.filter(n => n.lang === forgeLang).map((narrator) => (
                        <div
                          key={narrator.id}
                          className={`narrator-card ${selectedNarrator?.id === narrator.id ? 'active' : ''}`}
                          onClick={() => setSelectedNarrator(narrator)}
                        >
                          <div className="narrator-avatar">
                            <User size={24} />
                          </div>
                          <div className="narrator-info">
                            <span className="narrator-name">{narrator.name}</span>
                            <span className="narrator-role">{narrator.role}</span>
                          </div>
                          {selectedNarrator?.id === narrator.id && (
                            <div className="selection-check">
                              <CheckCircle size={14} />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {forgeScript && (
                  <div className="forge-preview fade-up">
                    <div className="section-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileText size={20} color="var(--primary)" />
                        <h2 className="studio-title" style={{ margin: 0 }}>Generated Script</h2>
                        {detectedBlueprint && (
                          <span className="badge" style={{
                            background: 'rgba(255, 184, 0, 0.1)',
                            color: 'var(--primary)',
                            fontSize: '0.75rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            border: '1px solid var(--primary)',
                            marginLeft: '8px'
                          }}>
                            {detectedBlueprint} Style
                          </span>
                        )}
                        {forgeMusic && (
                          <div className="music-badge" style={{
                            background: 'rgba(129, 140, 248, 0.1)',
                            color: 'var(--secondary)',
                            fontSize: '0.75rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            border: '1px solid var(--secondary)',
                            marginLeft: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <Music size={12} />
                            {forgeMusic.genre}
                          </div>
                        )}
                      </div>
                    </div>

                    {forgeProduction && (
                      <div className="production-guide mb-2 fade-up">
                        <div className="guide-header">
                          <Target size={14} /> <span>Production Mastery Guide</span>
                        </div>
                        <div className="guide-grid">
                          <div className="guide-item">
                            <label>Mood</label>
                            <span>{forgeProduction.mood}</span>
                          </div>
                          <div className="guide-item">
                            <label>Palette</label>
                            <div className="palette-preview">
                              {forgeProduction.palette.split(',').map((c, i) => (
                                <span key={i} className="color-dot" title={c.trim()} style={{ background: c.toLowerCase().includes('gold') ? '#fbbf24' : c.toLowerCase().includes('wood') ? '#78350f' : c.toLowerCase().includes('velvet') ? '#7f1d1d' : 'var(--primary)' }}></span>
                              ))}
                              <span>{forgeProduction.palette}</span>
                            </div>
                          </div>
                          <div className="guide-item">
                            <label>Pacing</label>
                            <span>{forgeProduction.pacing}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="refiner-row mb-2">
                      <span className="refiner-label">Magic Refiners:</span>
                      <button className="refiner-btn viral" onClick={() => refineForgeScript('viral')} disabled={isRefining}>
                        <Zap size={14} /> Viral Hook
                      </button>
                      <button className="refiner-btn emotional" onClick={() => refineForgeScript('emotional')} disabled={isRefining}>
                        <Sparkles size={14} /> Emotional Depth
                      </button>
                      <button className="refiner-btn simple" onClick={() => refineForgeScript('simple')} disabled={isRefining}>
                        <BookOpen size={14} /> Simplify
                      </button>
                      {isRefining && <Loader2 size={16} className="spinning ml-1" />}
                    </div>

                    <div className="forge-segments-list mb-2">
                      {forgeSegments.map((seg, idx) => (
                        <div key={idx} className="forge-segment-item">
                          <div className="seg-meta">
                            <div className="seg-left">
                              <span className="seg-time">{seg.timestamp}</span>
                              <span className="seg-title">{seg.title}</span>
                            </div>
                            {seg.visual_suggestion && (
                              <div className="seg-broll">
                                <Video size={12} /> <span>{seg.visual_suggestion}</span>
                              </div>
                            )}
                          </div>
                          <p className="seg-text-preview">{seg.text.substring(0, 80)}...</p>
                        </div>
                      ))}
                    </div>

                    <textarea
                      className="vs-textarea mb-2"
                      value={forgeScript}
                      onChange={(e) => setForgeScript(e.target.value)}
                      rows={10}
                    />
                    <div className="vs-actions">
                      <button
                        className="vs-gen-btn pulse-border"
                        onClick={approveForgeProject}
                        disabled={forgeStatus === 'generating-assets'}
                      >
                        {forgeStatus === 'generating-assets' ? <Loader2 size={18} className="spinning" /> : <CheckCircle size={18} />}
                        <span>Approve & Generate Assets</span>
                      </button>
                    </div>
                  </div>
                )}

                {forgeAssets && (
                  <div className="forge-results mt-3 fade-up">
                    <div className="results-grid">
                      <div className="vs-audio-card glass-box">
                        <div className="panel-title">
                          <Volume2 size={20} className="icon" />
                          <h2>Voice Narration</h2>
                        </div>
                        <audio controls src={forgeAssets.audio_url} className="vs-custom-audio mt-1" />

                        <div className="cinema-actions mt-2">
                          <button
                            className="vs-gen-btn secondary"
                            onClick={generateForgeVideo}
                            disabled={isRenderingVideo}
                          >
                            {isRenderingVideo ? <Loader2 size={16} className="spinning" /> : <Video size={16} />}
                            <span>{isRenderingVideo ? 'Rendering Cinema...' : 'Generate Official Video'}</span>
                          </button>
                        </div>

                        {forgeVideoUrl && (
                          <div className="rendered-cinema mt-2 fade-up">
                            <div className="panel-title mb-1">
                              <Film size={18} color="var(--primary)" />
                              <h3 style={{ fontSize: '0.9rem', margin: 0 }}>Official Render</h3>
                            </div>
                            <video controls src={forgeVideoUrl} className="forge-main-video" />
                            <a href={forgeVideoUrl} download className="vs-dl-link mt-1">
                              <Download size={14} /> Download Final MP4
                            </a>
                          </div>
                        )}

                        <a href={forgeAssets.audio_url} download className="vs-dl-link mt-1">
                          <Download size={16} /> Download Audio
                        </a>
                      </div>

                      <div className="glass-box">
                        <div className="panel-title">
                          <ImageIcon size={20} className="icon" />
                          <h2>Visual Storyboard</h2>
                        </div>
                        <div className="storyboard-gallery">
                          {forgeAssets.storyboard ? forgeAssets.storyboard.map((item, idx) => (
                            <div className="storyboard-item" key={idx}>
                              <div className="story-meta">
                                <div className="meta-left">
                                  <span className="story-time">{item.timestamp}</span>
                                  <span className="story-title">{item.title}</span>
                                </div>
                                <div className="visual-intent">
                                  <Camera size={12} /> <span>{['Wide Shot', 'Close-up', 'Low Angle', 'Tracking', 'Aerial', 'Macro'][idx % 6]}</span>
                                </div>
                              </div>
                              <div className="story-prompt">
                                <p>{item.prompt}</p>
                              </div>
                            </div>
                          )) : (
                            <p className="vs-tips">Storyboarding in progress...</p>
                          )}
                        </div>
                      </div>
                      <div className="roadmap-list mt-1">
                        {forgeAssets.visual_prompts?.map((p, i) => (
                          <div className="roadmap-item" key={i}>
                            <div className="roadmap-content">
                              <span className="action-chip">Scene {i + 1}</span>
                              <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{p}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Teleprompter Overlay */}
      {
        showTeleprompter && studioData && (
          <div className="tele-overlay">
            <div className="tele-header">
              <span>Teleprompter Mode — {studioData.target_lang?.toUpperCase()}</span>
              <button className="close-tele" onClick={() => setShowTeleprompter(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="tele-content">
              <div className="tele-text">
                {studioData.studio_script}
              </div>
              <div className="reading-line" />
            </div>
            <div className="tele-footer">
              <p>Tip: Scroll slowly as you read. Take your time 🎙️</p>
            </div>
          </div>
        )
      }
    </div >
  );
}

export default App;
