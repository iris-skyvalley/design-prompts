import React, { useState } from 'react';

// Loading spinner component
const LoadingSpinner = () => (
  <div style={{
    display: 'inline-block',
    width: '20px',
    height: '20px',
    border: '3px solid rgba(255,255,255,.3)',
    borderRadius: '50%',
    borderTopColor: '#fff',
    animation: 'spin 1s ease-in-out infinite',
    marginRight: '8px'
  }}>
    <style>{`
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `}</style>
  </div>
);

function App() {
  const [images, setImages] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [jsonPrompt, setJsonPrompt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingType, setLoadingType] = useState(null); // 'generate' or 'surprise'
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleFiles = (files) => {
    const fileArr = Array.from(files);
    if (fileArr.length < 1 || fileArr.length > 5) {
      setError('Please upload 1-5 images.');
      return;
    }
    setImages(fileArr);
    setError('');
  };

  const removeImage = (indexToRemove) => {
    setImages(images.filter((_, index) => index !== indexToRemove));
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        jsonPrompt.landing_page_prompt || JSON.stringify(jsonPrompt, null, 2)
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const handleChange = (e) => {
    handleFiles(e.target.files);
  };

  const handleSubmit = async () => {
    if (images.length === 0) return;
    setLoading(true);
    setLoadingType('generate');
    setPrompts([]);
    setJsonPrompt(null);
    setError('');
    const formData = new FormData();
    images.forEach((img) => formData.append('files', img));
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/generate-prompt/`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to generate prompt');
      const data = await res.json();
      setPrompts(data.prompt_variations || []);
      setJsonPrompt(data.json_variation || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingType(null);
    }
  };

  const handleSurpriseMe = async () => {
    setLoading(true);
    setLoadingType('surprise');
    setPrompts([]);
    setJsonPrompt(null);
    setError('');
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/surprise-me/`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to generate surprise prompt');
      const data = await res.json();
      setPrompts(data.prompt_variations || []);
      setJsonPrompt(data.json_variation || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingType(null);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'center',
      paddingTop: '100px',
      fontFamily: 'sans-serif',
      background: '#ffffff',
      padding: '100px 20px 40px'
    }}>
      <div style={{ 
        maxWidth: 600, 
        width: '100%',
        background: '#fff',
        borderRadius: 16,
        padding: 40,
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        border: '1px solid #e5e7eb'
      }}>
        <h1 style={{ 
          textAlign: 'center', 
          marginBottom: 32,
          color: '#333',
          fontSize: 28,
          fontWeight: 700
        }}>
          Design Prompt Generator
        </h1>
        
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          style={{
            border: '2px dashed #ddd',
            borderRadius: 12,
            padding: 40,
            textAlign: 'center',
            marginBottom: 24,
            background: '#fafbfc',
            transition: 'all 0.3s ease'
          }}
          onDragEnter={(e) => e.target.style.borderColor = '#667eea'}
          onDragLeave={(e) => e.target.style.borderColor = '#ddd'}
        >
          <p style={{ margin: 0, color: '#666', fontSize: 16 }}>
            Drag & drop 1-5 images here, or{' '}
            <label style={{ color: '#667eea', cursor: 'pointer', fontWeight: 600 }}>
              <input 
                type="file" 
                multiple 
                accept="image/*" 
                style={{ display: 'none' }} 
                onChange={handleChange} 
              />
              browse
            </label>
          </p>
          {images.length > 0 && (
            <div style={{ 
              marginTop: 16, 
              padding: 12, 
              background: '#e8f4fd', 
              borderRadius: 8,
              cursor: 'default'
            }}>
              {images.map((img, i) => (
                <div key={i} style={{ 
                  fontSize: 14, 
                  color: '#333',
                  marginBottom: 8,
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'default'
                }}>
                  <span style={{ cursor: 'default' }}>📁 {img.name}</span>
                  <button
                    onClick={() => removeImage(i)}
                    style={{
                      background: '#ff4757',
                      color: 'white',
                      border: 'none',
                      borderRadius: 4,
                      padding: '4px 8px',
                      fontSize: 12,
                      cursor: 'pointer',
                      fontWeight: 600,
                      marginLeft: 8
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <button 
          onClick={handleSubmit} 
          disabled={loading || images.length === 0} 
          style={{ 
            width: '100%',
            padding: '16px 24px', 
            borderRadius: 12, 
            background: loading ? '#ccc' : '#000000', 
            color: '#fff', 
            border: 'none', 
            fontWeight: 600, 
            fontSize: 16,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 24
          }}
        >
          {loadingType === 'generate' && <LoadingSpinner />}
          {loadingType === 'generate' ? 'Generating Design Prompts...' : 'Generate Prompt'}
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: 24,
          color: '#666',
          fontSize: 14
        }}>
          <div style={{ flex: 1, height: '1px', background: '#ddd' }}></div>
          <span style={{ padding: '0 16px', fontWeight: 600 }}>OR</span>
          <div style={{ flex: 1, height: '1px', background: '#ddd' }}></div>
        </div>

        <button 
          onClick={handleSurpriseMe} 
          disabled={loading} 
          style={{ 
            width: '100%',
            padding: '16px 24px', 
            borderRadius: 12, 
            backgroundImage: loading ? 'none' : 'linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4ecdc4, #45b7d1, #a8e6cf, #ff9ff3)', 
            backgroundColor: loading ? '#ccc' : 'transparent',
            backgroundSize: '300% 300%',
            animation: loading ? 'none' : 'rainbow 3s ease infinite',
            color: '#fff', 
            border: 'none', 
            fontWeight: 600, 
            fontSize: 16,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textShadow: '0 1px 2px rgba(0,0,0,0.3)'
          }}
        >
          {loadingType === 'surprise' && <LoadingSpinner />}
          {loadingType === 'surprise' ? 'Creating Surprise...' : '🎲 Surprise Me!'}
          <style>{`
            @keyframes rainbow {
              0% { background-position: 0% 50%; }
              50% { background-position: 100% 50%; }
              100% { background-position: 0% 50%; }
            }
          `}</style>
        </button>
        
        {error && (
          <div style={{ 
            color: '#dc3545', 
            marginTop: 16, 
            padding: 12,
            background: '#f8d7da',
            borderRadius: 8,
            border: '1px solid #f5c6cb'
          }}>
            {error}
          </div>
        )}
        
        
        {jsonPrompt && (
          <div style={{ marginTop: 32 }}>
            <h3 style={{ color: '#333', fontSize: 20, marginBottom: 16 }}>Landing Page Prompt</h3>
            <div style={{ 
              background: '#1a1a1a', 
              color: '#f8f8f2', 
              padding: 24, 
              borderRadius: 12, 
              fontSize: 14,
              lineHeight: '1.6',
              fontFamily: 'Monaco, Consolas, monospace',
              overflow: 'auto',
              maxHeight: '400px'
            }}>
              {jsonPrompt.landing_page_prompt ? (
                <div style={{ whiteSpace: 'pre-wrap' }}>{jsonPrompt.landing_page_prompt}</div>
              ) : (
                <pre>{JSON.stringify(jsonPrompt, null, 2)}</pre>
              )}
            </div>
            <button 
              style={{
                marginTop: 12,
                padding: '12px 20px',
                background: copied ? '#198754' : '#28a745',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 14,
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 0.2s ease'
              }}
              onClick={handleCopy}
            >
              {copied ? '✓ Copied!' : 'Copy Landing Page Prompt'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
