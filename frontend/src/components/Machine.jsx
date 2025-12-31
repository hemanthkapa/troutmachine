import { useState, useRef } from "react";
import "./Machine.css";

const API_Base = import.meta.env.VITE_API_URL || "http://127.0.0.1:32001/api";

export default function Machine() {
  const [status, setStatus] = useState("idle"); // idle, curating, results
  const [query, setQuery] = useState("");
  const [artworks, setArtworks] = useState([]);
  const [title, setTitle] = useState("mysterious trout machine");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    startCurating(query, `search?q=${query}`);
  };

  // Whimsical prompts for "I'm Feeling Lucky"
  const WHIMSICAL_PROMPTS = [
    "clouds and castles",
    "morning coffee ritual",
    "frog and friends",
    "golden hour",
    "mysterious faces",
    "ancient silence",
    "garden party",
    "winter whisper",
    "ocean dream",
    "forest path",
    "stars and night",
    "quiet reading",
    "cats and dogs",
    "flower power",
  ];

  const handleLucky = () => {
    const prompt =
      WHIMSICAL_PROMPTS[Math.floor(Math.random() * WHIMSICAL_PROMPTS.length)];
    setQuery(prompt); // Update the input value to show what was "searched"
    // Use search endpoint to find items matching the whimsical prompt
    startCurating(prompt, `search?q=${encodeURIComponent(prompt)}`);
  };

  const [selectedArtwork, setSelectedArtwork] = useState(null);
  const [zoomProps, setZoomProps] = useState({ x: 0, y: 0, show: false });

  // Magnifier Logic
  const handleImageMouseMove = (e) => {
    const { left, top, width, height } =
      e.currentTarget.getBoundingClientRect();
    const x = e.clientX - left;
    const y = e.clientY - top;

    // Check boundaries
    if (x < 0 || y < 0 || x > width || y > height) {
      setZoomProps({ ...zoomProps, show: false });
      return;
    }

    setZoomProps({ x, y, show: true, width, height });
  };

  const handleImageMouseLeave = () => {
    setZoomProps({ ...zoomProps, show: false });
  };

  const startCurating = async (displayTitle, endpoint) => {
    setStatus("curating");
    setSelectedArtwork(null);
    // Artificial delay for the "machine" feel
    await new Promise((r) => setTimeout(r, 2000));

    try {
      const res = await fetch(`${API_Base}/${endpoint}`);
      const data = await res.json();
      setArtworks(data);
      setTitle(displayTitle);
      setStatus("results");
    } catch (err) {
      console.error(err);
      setStatus("idle");
    }
  };

  const handleSelectArtwork = (art) => {
    setSelectedArtwork(art);
  };

  const closeDetail = () => {
    setSelectedArtwork(null);
    setZoomProps({ ...zoomProps, show: false });
  };

  const reset = () => {
    setStatus("idle");
    setQuery("");
    setTitle("mysterious trout machine");
    setArtworks([]);
    setSelectedArtwork(null);
  };

  return (
    <div className={`machine-container ${status}`}>
      {/* HEADER */}
      {/* HEADER - Only show when NOT idle (i.e. results/curating) */}
      {status !== "idle" && (
        <header className="machine-header">
          <img
            src="/trout-logo-large.png"
            alt="The Trout Gallery"
            className="header-logo"
          />
          <h1 className="results-title">{title}</h1>
          <button className="search-again-link" onClick={reset}>
            search again
          </button>
        </header>
      )}

      {/* IDLE STATE */}
      {status === "idle" && (
        <div className="state-idle fade-in">
          <div className="idle-content">
            <img
              src="/trout-logo-large.png"
              alt="The Trout Gallery"
              className="hero-logo"
            />
            <h1 className="hero-title">mysterious trout machine</h1>
            <p className="hero-subtitle">
              enter a phrase to reveal hidden connections.
            </p>

            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="castle and clouds"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
            </form>

            <div className="actions">
              <button className="lucky-btn" onClick={handleLucky}>
                i'm feeling lucky
              </button>
            </div>

            <div className="bottom-action">
              <button
                className="search-link"
                onClick={handleSearch}
                disabled={!query}
              >
                search the collection →
              </button>
            </div>
          </div>

          <footer className="machine-footer">
            made with 💌 by hemanth and John
          </footer>
        </div>
      )}

      {/* CURATING STATE */}
      {status === "curating" && (
        <div className="state-curating fade-in">
          <p>curating...</p>
        </div>
      )}

      {/* RESULTS STATE */}
      {status === "results" && !selectedArtwork && (
        <div className="state-results fade-in">
          {artworks.filter((art) => art.image_url && art.title && art.artist)
            .length > 0 ? (
            <div className="gallery-track">
              {artworks
                .filter(
                  (art) => art.image_url && art.title
                ) /* artist filter removed */
                .map((art) => (
                  <div key={art.id} className="artwork-card">
                    <div
                      className="image-wrapper"
                      onClick={() => handleSelectArtwork(art)}
                    >
                      <img src={art.image_url} alt={art.title} />
                      <div className="artwork-info">
                        <h2>{art.title}</h2>
                        <p>{art.artist || "Artist Unknown"}</p>
                      </div>
                    </div>
                  </div>
                ))}

              {/* End Card */}
              <div className="artwork-card end-card">
                <button onClick={reset}>search again -{">"}</button>
              </div>
            </div>
          ) : (
            <div className="no-results">
              <p>the machine is confused. "{query}" remains a mystery.</p>
              <button onClick={reset}>try another phrase</button>
            </div>
          )}
        </div>
      )}

      {/* DETAIL VIEW */}
      {selectedArtwork && (
        <div className="detail-view fade-in">
          <button className="close-btn" onClick={closeDetail}>
            ×
          </button>
          <div className="detail-content">
            <div
              className="detail-image"
              onMouseMove={handleImageMouseMove}
              onMouseLeave={handleImageMouseLeave}
              onMouseEnter={handleImageMouseMove}
              style={{ position: "relative", overflow: "hidden" }}
            >
              {" "}
              {/* Added relative positioning */}
              <img
                src={selectedArtwork.image_url}
                alt={selectedArtwork.title}
                style={{ cursor: "crosshair" }}
              />
              {zoomProps.show && (
                <div
                  className="magnifier-lens"
                  style={{
                    position: "absolute",
                    left: `${zoomProps.x - 75}px`, // Center the lens (150px / 2)
                    top: `${zoomProps.y - 75}px`,
                    backgroundImage: `url(${selectedArtwork.image_url})`,
                    backgroundPosition: `${
                      (zoomProps.x / zoomProps.width) * 100
                    }% ${(zoomProps.y / zoomProps.height) * 100}%`,
                    backgroundSize: `${zoomProps.width * 2}px ${
                      zoomProps.height * 2
                    }px`, // 2x Zoom relative to formatted image size
                  }}
                />
              )}
            </div>
            <div className="detail-metadata">
              <h2>{selectedArtwork.title}</h2>
              <p className="artist">{selectedArtwork.artist}</p>

              <div className="meta-grid">
                <div className="meta-item">
                  <label>Date</label>
                  <span>{selectedArtwork.date}</span>
                </div>
                <div className="meta-item">
                  <label>Medium</label>
                  <span>{selectedArtwork.medium}</span>
                </div>
                <div className="meta-item">
                  <label>Dimensions</label>
                  <span>
                    {selectedArtwork.dimensions || "Dimensions unavailable"}
                  </span>
                </div>
                <div className="meta-item">
                  <label>Department</label>
                  <span>{selectedArtwork.department || "Trout Gallery"}</span>
                </div>
                <div className="meta-item">
                  <label>Credit</label>
                  <span>{selectedArtwork.credit || "Gift of the Artist"}</span>
                </div>
                <div className="meta-item">
                  <label>Object ID</label>
                  <span>{selectedArtwork.id}</span>
                </div>
              </div>

              <a
                href={selectedArtwork.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="met-link"
              >
                View on Trout Gallery Website →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
