import { useState } from 'react'
import './App.css'

function App() {
  const [userType, setUserType] = useState('Seller')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Auto-generate user_id based on role
  const getUserId = (role) => {
    const roleMap = {
      'Seller': 'seller_1',
      'Buyer': 'buyer_1',
      'Carrier': 'carrier_1',
      'Agent': 'agent_1'
    }
    return roleMap[role] || 'user_1'
  }

  const handleSearch = async () => {
    setLoading(true)
    setHasSearched(true)
    try {
      const response = await fetch(`http://localhost:8004/search?q=${query}`, {
        method: 'GET',
        headers: {
          'user-type': userType,
          'user-id': getUserId(userType),
          'account-id': 'acc_1'
        }
      })
      const data = await response.json()
      setResults(data.results || [])
    } catch (error) {
      console.error("Search failed", error)
    }
    setLoading(false)
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Unified Search Enterprise</h1>
        <p>One API. Infinite Possibilities. 10M+ Records.</p>
      </div>

      <div className="controls-wrapper">
        <div className="control-group">
          <label>ACCESS ROLE</label>
          <select value={userType} onChange={(e) => setUserType(e.target.value)}>
            <option value="Seller">Seller</option>
            <option value="Buyer">Buyer</option>
            <option value="Carrier">Carrier</option>
            <option value="Agent">Agent</option>
          </select>
        </div>
      </div>

      <div className="search-section">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="Search by VIN, Model, Status, or ID..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button className="search-btn" onClick={handleSearch} disabled={loading}>
          {loading ? <span className="loading-pulse"></span> : 'Search'}
        </button>
      </div>

      <div className="results-grid">
        {results.map((item, index) => (
          <div key={index} className="card" style={{ animationDelay: `${index * 50}ms`, animation: 'fadeIn 0.5s ease-out forwards' }}>
            <div className="card-header">
              <span className={`badge ${item.entity_type}`}>{item.entity_type}</span>
              <span className="date">{new Date(item.created_at || item.purchase_date || item.schedule_date).toLocaleDateString()}</span>
            </div>

            <div className="card-body">
              {item.entity_type === 'offer' && (
                <>
                  <h3>{item.year} {item.make} {item.model}</h3>
                  <div className="info-row">
                    <div className="info-item">
                      <label>Price</label>
                      <span>${item.price?.toLocaleString()}</span>
                    </div>
                    <div className="info-item">
                      <label>Condition</label>
                      <span>{item.condition}</span>
                    </div>
                  </div>
                  <div className="info-row">
                    <div className="info-item">
                      <label>VIN</label>
                      <span style={{ fontFamily: 'monospace' }}>{item.vin}</span>
                    </div>
                    <div className="info-item">
                      <label>Status</label>
                      <span><span className="status-dot"></span>{item.status}</span>
                    </div>
                  </div>
                </>
              )}
              {item.entity_type === 'purchase' && (
                <>
                  <h3>Purchase Order</h3>
                  <div className="info-row">
                    <div className="info-item">
                      <label>Amount</label>
                      <span>${item.amount?.toLocaleString()}</span>
                    </div>
                    <div className="info-item">
                      <label>Buyer</label>
                      <span>{item.buyer_id}</span>
                    </div>
                  </div>
                </>
              )}
              {item.entity_type === 'transport' && (
                <>
                  <h3>Logistics Task</h3>
                  <div className="info-row">
                    <div className="info-item">
                      <label>Pickup</label>
                      <span>{item.pickup_location}</span>
                    </div>
                    <div className="info-item">
                      <label>Delivery</label>
                      <span>{item.delivery_location}</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        ))}

        {results.length === 0 && !loading && hasSearched && (
          <div style={{ gridColumn: '1/-1', textAlign: 'center', color: '#64748b', marginTop: '40px' }}>
            <h2>No results found</h2>
            <p>Try adjusting your search terms or user permissions.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
