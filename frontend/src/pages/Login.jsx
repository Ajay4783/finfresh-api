import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // Backend API-la irunthu token vaangurom
      const response = await axios.post('http://127.0.0.1:8000/auth/login', {
        email: email,
        password: password
      });
      
      // Token-a browser localStorage-la save pandrom (appothaan transactions panna mudiyum)
      localStorage.setItem('token', response.data.token);
      
      // Success aana udane dashboard-ku porom
      navigate('/dashboard'); 
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Invalid credentials.");
    }
  };

  return (
    <div style={{ padding: '50px', maxWidth: '400px', margin: 'auto' }}>
      <h2>Login to FinFresh</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <input 
          type="email" placeholder="Email Address" required
          value={email} onChange={(e) => setEmail(e.target.value)} 
          style={{ padding: '10px' }}
        />
        <input 
          type="password" placeholder="Password" required
          value={password} onChange={(e) => setPassword(e.target.value)} 
          style={{ padding: '10px' }}
        />
        <button type="submit" style={{ padding: '10px', background: 'green', color: 'white', border: 'none', cursor: 'pointer' }}>
          Login
        </button>
      </form>
      <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
  );
}