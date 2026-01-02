import { useState, useRef, useEffect } from "react";
import "./Machine.css";

const API_Base = import.meta.env.VITE_API_URL || "/api";

export default function Machine() {
  const [status, setStatus] = useState("idle"); // idle, curating, results
  const [query, setQuery] = useState("");
  const [artworks, setArtworks] = useState([]);
  const [title, setTitle] = useState("Mysterious Trout Machine");
  const galleryTrackRef = useRef(null);
  
  // Mobile detection state
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

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
  const imageRef = useRef(null);
  const containerRef = useRef(null);

  // Magnifier Logic - improved to check actual image boundaries
  // Disabled on mobile devices for better UX
  const handleImageMouseMove = (e) => {
    // Disable magnifier on mobile/tablet
    if (isMobile) return;
    
    if (!imageRef.current || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const imgRect = imageRef.current.getBoundingClientRect();

    // Mouse position relative to image
    const xRelativeToImage = e.clientX - imgRect.left;
    const yRelativeToImage = e.clientY - imgRect.top;

    // Check if mouse is actually over the image
    if (
      xRelativeToImage < 0 ||
      yRelativeToImage < 0 ||
      xRelativeToImage > imgRect.width ||
      yRelativeToImage > imgRect.height
    ) {
      setZoomProps({ ...zoomProps, show: false });
      return;
    }

    // Position relative to container for absolute positioning
    const xRelativeToContainer = e.clientX - containerRect.left;
    const yRelativeToContainer = e.clientY - containerRect.top;

    setZoomProps({
      x: xRelativeToContainer,
      y: yRelativeToContainer,
      imgX: xRelativeToImage,
      imgY: yRelativeToImage,
      show: true,
      imgWidth: imgRect.width,
      imgHeight: imgRect.height,
    });
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
    setTitle("Mysterious Trout Machine");
    setArtworks([]);
    setSelectedArtwork(null);
  };

  // Resize listener for mobile detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mouse wheel scroll handler for horizontal gallery scrolling with smooth behavior
  useEffect(() => {
    const galleryElement = galleryTrackRef.current;
    if (!galleryElement || selectedArtwork) return; // Don't attach if detail view is open

    const handleWheel = (e) => {
      // On mobile/touch devices, use native touch scrolling
      if ('ontouchstart' in window || isMobile) return;
      
      // If there's horizontal scrolling (trackpad gesture), let it work naturally
      if (Math.abs(e.deltaX) > 0) {
        return; // Don't prevent default, allow native trackpad scrolling
      }

      // Only convert vertical scroll (mouse wheel) to horizontal
      if (Math.abs(e.deltaY) > 0) {
        e.preventDefault();
        // Direct scrollLeft update for instant, smooth response like trackpad
        galleryElement.scrollLeft += e.deltaY * 1.5;
      }
    };

    // Add event listener with passive: false to allow preventDefault
    galleryElement.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      galleryElement.removeEventListener("wheel", handleWheel);
    };
  }, [status, artworks, selectedArtwork]); // Re-attach when selectedArtwork changes

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
            Search again
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
            <h1 className="hero-title">Mysterious Trout Machine</h1>
            <p className="hero-subtitle">
              Enter a phrase to reveal hidden connections.
            </p>

            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="Castle and clouds"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
            </form>

            <div className="actions">
              <button className="lucky-btn" onClick={handleLucky}>
                I'm feeling lucky
              </button>
            </div>

            <div className="bottom-action">
              <button
                className="search-link"
                onClick={handleSearch}
                disabled={!query}
              >
                Search the collection →
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
          <p>Curating...</p>
        </div>
      )}

      {/* RESULTS STATE */}
      {status === "results" && !selectedArtwork && (
        <div className="state-results fade-in">
          {artworks.filter((art) => art.image_url && art.title).length > 0 ? (
            <div className="gallery-track" ref={galleryTrackRef}>
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
                        <h2>{art.title || "Untitled"}</h2>
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
              <p>The machine is confused. "{query}" remains a mystery.</p>
              <button onClick={reset}>Try another phrase</button>
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
              ref={containerRef}
              onMouseMove={handleImageMouseMove}
              onMouseLeave={handleImageMouseLeave}
              style={{ position: "relative", overflow: "hidden" }}
            >
              <img
                ref={imageRef}
                src={selectedArtwork.image_url}
                alt={selectedArtwork.title}
                style={{ 
                  cursor: isMobile ? "default" : "crosshair", 
                  display: "block" 
                }}
              />
              {zoomProps.show && (
                <div
                  className="magnifier-lens"
                  style={{
                    position: "absolute",
                    left: `${zoomProps.x - 75}px`,
                    top: `${zoomProps.y - 75}px`,
                    backgroundImage: `url(${selectedArtwork.image_url})`,
                    backgroundPosition: `${-(zoomProps.imgX * 2 - 75)}px ${-(
                      zoomProps.imgY * 2 -
                      75
                    )}px`,
                    backgroundSize: `${zoomProps.imgWidth * 2}px ${
                      zoomProps.imgHeight * 2
                    }px`,
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
